"""Fahrzeugdaten direkt von der Panoptes-App im Auto (vormals SurfMate), statt ueber die BYD-Cloud.

Die App im Auto hat einen eigenen Webserver (Port 8180), erreichbar im Heimnetz oder ueber
Tailscale. Anmeldung: der Kopplungs-Code aus der App ("<geraet>-<geheimnis>") wird einmal gegen
ein Zugangs-Token (JWT, 30 Tage) getauscht; das Token liegt nur in der Cockpit-Konfiguration.

Ist das Auto aus oder nicht erreichbar, liefert lies() None - das Cockpit fragt dann wie bisher
die BYD-Cloud (pybyd). Steuern (Klima, Schloss) laeuft weiter ueber die BYD-Cloud.
"""
import json
import re
import secrets
import socket
import time
import urllib.error
import urllib.request

TIMEOUT = 6
ODO_TAKT_S = 600          # Kilometerstand separat nur alle 10 min (der Endpunkt kann Cloud-Abfragen ausloesen)


class NichtAngemeldet(Exception):
    pass


class KopplungAbgelaufen(NichtAngemeldet):
    """Zugang abgelaufen und der (einmal verwendbare) Kopplungs-Code ist verbraucht -> in Panoptes neu koppeln."""


def _http(url, daten=None, jwt="", timeout=TIMEOUT, methode=None):
    kopf = {"Accept": "application/json", "User-Agent": "ev-cockpit"}
    if daten is not None:
        kopf["Content-Type"] = "application/json"
    if jwt:
        kopf["Authorization"] = "Bearer " + jwt
    req = urllib.request.Request(url, data=json.dumps(daten).encode() if daten is not None else None,
                                 method=methode or ("POST" if daten is not None else "GET"), headers=kopf)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise NichtAngemeldet()
        if e.code in (403, 409):          # Einstellungen: veraltet / nicht erlaubt -> Antwort mit Grund zurueckgeben
            try:
                d = json.loads(e.read().decode("utf-8") or "{}")
            except Exception:
                d = {}
            d["_status"] = e.code
            return d
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
        self.jwt_gespeichert = jwt_gespeichert or (lambda j, code_verbraucht=False: None)
        self.odo_t = 0.0
        self.code_verbraucht = False
        self.letzter_fehler = ""

    def _anmelden(self):
        """Kopplung (Vertrag EINSTELLUNGEN_SCHEMA v1.1): POST /auth/kopplung {"code"} -> JWT mit scope "kopplung".
        Der Code ist einmal verwendbar und 10 min gueltig - danach zaehlt nur noch der JWT. Aeltere Panoptes ohne
        /auth/kopplung (404): wie bisher /auth/token."""
        if not self.code:
            raise KopplungAbgelaufen()
        try:
            d = self.http(self.url + "/auth/kopplung", {"code": self.code, "name": geraetename()})
            einmal = True
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
            d = self.http(self.url + "/auth/token", {"token": self.code})
            einmal = False
        if not d.get("success") or not d.get("jwt"):
            raise NichtAngemeldet()
        self.jwt = d["jwt"]
        if einmal:
            self.code, self.code_verbraucht = "", True       # verbraucht - nie wieder senden
        self.jwt_gespeichert(self.jwt, code_verbraucht=einmal)

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
            self.letzter_fehler = ""
            st["online"] = "ON"
            st["_quelle"] = "Panoptes"
            return st
        except KopplungAbgelaufen:
            self.letzter_fehler = "kopplung_abgelaufen"
            return None
        except Exception:
            return None


def kennung_aus(d):
    """GET /api/planer/identitaet -> sichere auto-Kennung oder "" (Format wie beim Planer: 1-32 Zeichen [A-Za-z0-9_-])."""
    import re
    d = d or {}
    a = str(d.get("autoId") or d.get("auto") or "")       # Kern liefert {success, autoId:"a-<16 hex>"}
    return a if re.fullmatch(r"[A-Za-z0-9_-]{1,32}", a) else ""


def identitaet(p):
    """Die Planer-Kennung von Panoptes (planner.autoId), damit Cockpit und Auto dieselbe Route/Rueckmeldung sehen.
    "" solange Panoptes den Endpunkt noch nicht hat (404) oder das Auto nicht erreichbar ist."""
    try:
        return kennung_aus(p._get("/api/planer/identitaet"))
    except Exception:
        return ""


# ---- Kopplung per Anfrage + 1 Tipp (Vertrag KOPPLUNG_ANFRAGE.md v1.1, ab Panoptes 0.1.7). Kein Code abtippen:
# Das Cockpit zeigt eine Pruefzahl, der Mensch erlaubt in Telegram, im Panoptes-Web oder am Display.
# Die Abhol-id ist ein Geheimnis: sie bleibt im Cockpit-Prozess (nie in Datei, Log oder Browser).
def geraetename():
    """Name, unter dem das Cockpit in Panoptes erscheint (hoechstens 40 Zeichen, ohne Steuerzeichen und <>)."""
    try:
        h = socket.gethostname()
    except Exception:
        h = ""
    return re.sub(r"[\x00-\x1f<>]", "", ("EV-Cockpit " + h).strip())[:40]


def neue_pruefzahl():
    return "%04d" % secrets.randbelow(10000)


def _roh(url, daten=None, timeout=TIMEOUT):
    """(Status, JSON) ohne Ausnahme bei HTTP-Fehlern; Netzfehler werfen weiter."""
    req = urllib.request.Request(url, data=json.dumps(daten).encode() if daten is not None else None,
                                 method="POST" if daten is not None else "GET",
                                 headers={"Accept": "application/json", "User-Agent": "ev-cockpit",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}


def kopplung_anfrage(url, geraet, pruefzahl, roh=_roh):
    """POST /auth/kopplung/anfrage -> {ok, id, gueltigBis} oder {ok:False, grund}."""
    code, d = roh(url.rstrip("/") + "/auth/kopplung/anfrage", {"geraet": geraet, "pruefzahl": pruefzahl})
    if code == 200 and d.get("ok") and re.fullmatch(r"[0-9a-f]{32}", str(d.get("id") or "")):
        return {"ok": True, "id": d["id"], "gueltigBis": d.get("gueltigBis")}
    if code == 404:
        return {"ok": False, "grund": "zu_alt"}           # Panoptes vor 0.1.7: nur der Code-Weg
    return {"ok": False, "grund": str(d.get("grund") or "http_%s" % code)}


def kopplung_status(url, aid, roh=_roh):
    """GET /auth/kopplung/anfrage/{id} -> {status: wartet|erlaubt|abgeholt|abgelehnt|abgelaufen|unbekannt|fehler}."""
    if not re.fullmatch(r"[0-9a-f]{32}", aid or ""):
        return {"status": "unbekannt"}
    code, d = roh(url.rstrip("/") + "/auth/kopplung/anfrage/" + aid)
    if code == 404:
        return {"status": "unbekannt"}
    st = d.get("status")
    if st == "erlaubt" and d.get("jwt"):
        return {"status": "erlaubt", "jwt": d["jwt"], "kopplungId": str(d.get("kopplungId") or ""),
                "expiresIn": d.get("expiresIn")}
    return {"status": st if st in ("wartet", "abgeholt", "abgelehnt", "abgelaufen") else "fehler"}


def aus_kopplungslink(text):
    """Link aus Panoptes "Neues Geraet koppeln" (<adresse>/system.html#koppeln=<code>) -> (adresse, code) oder None."""
    m = re.fullmatch(r"\s*(https?://[^/#?\s]+)(?:/[^#\s]*)?#koppeln=([A-Za-z0-9_-]{4,64})\s*", text or "")
    return (m.group(1), m.group(2)) if m else None


def sitzung_erneuern(p):
    """POST /api/sitzung/erneuern -> frischer JWT (30 Tage, gleiche Kopplung). Neuer JWT oder ""."""
    d = p.http(p.url + "/api/sitzung/erneuern", daten={}, jwt=p.jwt)
    j = str(d.get("jwt") or d.get("token") or "")
    if j:
        p.jwt = j
        p.jwt_gespeichert(j)
    return j


# ---- Einstellungen (Vertrag EINSTELLUNGEN_SCHEMA.md v1). Nur gespeicherte Werte - KEINE Befehle ans Auto (Regel A).
def einstellungen_lesen(p, sprache="de"):
    sprache = sprache if sprache in ("de", "en", "fr", "it", "nl") else "de"
    return {"schema": p._get("/api/einstellungen/schema?sprache=" + sprache), "werte": p._get("/api/einstellungen")}


def einstellungen_schreiben(p, body):
    """PUT /api/einstellungen mit {etag, werte, bestaetigt?}. Liefert die Antwort des Kerns (409 -> _status 409)."""
    if not p.jwt:
        p._anmelden()
    try:
        return p.http(p.url + "/api/einstellungen", daten=body, jwt=p.jwt, methode="PUT")
    except NichtAngemeldet:
        p._anmelden()
        return p.http(p.url + "/api/einstellungen", daten=body, jwt=p.jwt, methode="PUT")
