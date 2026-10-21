"""Fahrzeugdaten direkt von der Panoptes-App im Auto (vormals SurfMate), statt ueber die BYD-Cloud.

Die App im Auto hat einen eigenen Webserver (Port 8180), erreichbar im Heimnetz oder ueber
Tailscale. Anmeldung: der Kopplungs-Code aus der App ("<geraet>-<geheimnis>") wird einmal gegen
ein Zugangs-Token (JWT, 30 Tage) getauscht; das Token liegt nur in der Cockpit-Konfiguration.

Ist das Auto aus oder nicht erreichbar, liefert lies() None - das Cockpit fragt dann wie bisher
die BYD-Cloud (pybyd). Steuern (Klima, Schloss) laeuft weiter ueber die BYD-Cloud.
"""
import json
import time
import urllib.error
import urllib.request

TIMEOUT = 6
ODO_TAKT_S = 600          # Kilometerstand separat nur alle 10 min (der Endpunkt kann Cloud-Abfragen ausloesen)


class NichtAngemeldet(Exception):
    pass


def _http(url, daten=None, jwt="", timeout=TIMEOUT):
    kopf = {"Accept": "application/json", "User-Agent": "ev-cockpit"}
    if daten is not None:
        kopf["Content-Type"] = "application/json"
    if jwt:
        kopf["Authorization"] = "Bearer " + jwt
    req = urllib.request.Request(url, data=json.dumps(daten).encode() if daten is not None else None,
                                 method="POST" if daten is not None else "GET", headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise NichtAngemeldet()
        raise


def _zahl(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def _an(x):
    if x is None:
        return None
    if isinstance(x, str):
        x = x.strip().lower() in ("1", "true", "on", "yes")
    return "ON" if x else "OFF"


def aus_telemetrie(t):
    """MQTT-Telemetrie-Schnappschuss -> Cockpit-Felder (nur, was da ist)."""
    st = {}
    if _zahl(t.get("soc")) is not None:
        st["soc"] = _zahl(t["soc"])
    if _zahl(t.get("odometer")):
        st["odometer"] = _zahl(t["odometer"])
    if _zahl(t.get("ev_range_km")) is not None:
        st["range_km"] = _zahl(t["ev_range_km"])
    if _zahl(t.get("ext_temp")) is not None:
        st["temp_out"] = _zahl(t["ext_temp"])
    if _zahl(t.get("lat")) and _zahl(t.get("lon")):
        st["latitude"], st["longitude"] = _zahl(t["lat"]), _zahl(t["lon"])
    if t.get("gear"):
        st["gear"] = str(t["gear"]).upper()[:1]
    if _zahl(t.get("power_level")) is not None:       # Zuendung: 0 aus, 2 an (Sperre fuer Cloud-Befehle)
        st["power_level"] = int(_zahl(t["power_level"]))
    if _zahl(t.get("speed")) is not None:
        st["speed"] = _zahl(t["speed"])
    if t.get("is_charging") is not None:
        st["charging"] = _an(t["is_charging"])
    dl = t.get("door_lock")
    if isinstance(dl, list) and dl:
        st["locked"] = "ON" if all(v == 1 for v in dl) else "OFF"
    return st


def aus_uebersicht(s, gps=None, fahrzeug=None):
    """/api/launcher/v1/summary (+ /api/gps, /api/vehicle/state) -> Cockpit-Felder."""
    st = {}
    rng, zust, lad, umw = (s.get("range") or {}), (s.get("state") or {}), (s.get("charging") or {}), (s.get("env") or {})
    soc = _zahl(rng.get("socPct"))
    if soc is None:
        soc = _zahl((s.get("battery") or {}).get("socPct"))
    if soc is not None:
        st["soc"] = soc
    km = _zahl(rng.get("elecKm")) or _zahl(rng.get("totalKm"))
    if km is not None:
        st["range_km"] = km
    if _zahl(umw.get("tempC")) is not None:
        st["temp_out"] = _zahl(umw["tempC"])
    if zust.get("gear"):
        st["gear"] = str(zust["gear"]).upper()[:1]
    if zust.get("locked") is not None:
        st["locked"] = _an(zust["locked"])
    if lad.get("active") is not None:
        st["charging"] = _an(lad["active"])
    if _zahl(lad.get("kw")) is not None:
        st["charge_power"] = _zahl(lad["kw"])
    loc = (gps or {}).get("location") or {}
    if (gps or {}).get("hasLocation", True) and _zahl(loc.get("lat")) and _zahl(loc.get("lng")):
        st["latitude"], st["longitude"] = _zahl(loc["lat"]), _zahl(loc["lng"])
    odo = ((fahrzeug or {}).get("odometer") or {}).get("totalKm")
    if _zahl(odo):
        st["odometer"] = _zahl(odo)
    return st


class Panoptes:
    def __init__(self, url, kopplungscode, jwt="", http=_http, uhr=time.time, jwt_gespeichert=None):
        self.url = (url or "").rstrip("/")
        self.code = (kopplungscode or "").strip()
        self.jwt = jwt or ""
        self.http, self.uhr = http, uhr
        self.jwt_gespeichert = jwt_gespeichert or (lambda j: None)
        self.odo_t = 0.0

    def _anmelden(self):
        if not self.code:
            raise NichtAngemeldet()
        d = self.http(self.url + "/auth/token", {"token": self.code})
        if not d.get("success") or not d.get("jwt"):
            raise NichtAngemeldet()
        self.jwt = d["jwt"]
        self.jwt_gespeichert(self.jwt)

    def _get(self, pfad):
        if not self.jwt:
            self._anmelden()
        try:
            return self.http(self.url + pfad, jwt=self.jwt)
        except NichtAngemeldet:
            self._anmelden()                       # Token abgelaufen/ungueltig: einmal neu
            return self.http(self.url + pfad, jwt=self.jwt)

    def lies(self):
        """Aktueller Zustand als Cockpit-Felder, oder None (Auto aus / nicht erreichbar / falscher Code)."""
        if not self.url:
            return None
        try:
            st = {}
            try:
                t = self._get("/api/mqtt/telemetry")
                if t.get("success") and isinstance(t.get("telemetry"), dict):
                    st = aus_telemetrie(t["telemetry"])
            except NichtAngemeldet:
                raise
            except Exception:
                st = {}
            if "soc" not in st or "latitude" not in st:
                s = self._get("/api/launcher/v1/summary")
                try:
                    g = self._get("/api/gps")
                except Exception:
                    g = None
                fz = None
                if "odometer" not in st and self.uhr() - self.odo_t >= ODO_TAKT_S:
                    try:
                        fz = self._get("/api/vehicle/state")
                        self.odo_t = self.uhr()
                    except Exception:
                        fz = None
                st = dict(aus_uebersicht(s, g, fz), **st)
            if "soc" not in st:
                return None
            st["online"] = "ON"
            st["_quelle"] = "Panoptes"
            return st
        except Exception:
            return None


def kennung_aus(d):
    """GET /api/planer/identitaet -> sichere auto-Kennung oder "" (Format wie beim Planer: 1-32 Zeichen [A-Za-z0-9_-])."""
    import re
    a = str((d or {}).get("auto") or "")
    return a if re.fullmatch(r"[A-Za-z0-9_-]{1,32}", a) else ""


def identitaet(p):
    """Die Planer-Kennung von Panoptes (planner.autoId), damit Cockpit und Auto dieselbe Route/Rueckmeldung sehen.
    "" solange Panoptes den Endpunkt noch nicht hat (404) oder das Auto nicht erreichbar ist."""
    try:
        return kennung_aus(p._get("/api/planer/identitaet"))
    except Exception:
        return ""
