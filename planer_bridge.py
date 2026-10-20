"""Freiwillige Anbindung an den Routenplaner der BYD-Community (https://byd.serveone.at/ev/).

Was passiert (nur mit Haekchen im Assistenten und dem persoenlichen Planer-Link):
  - Ladestand melden: der Planer fuellt damit den Start-Ladestand vor. Gespeichert wird dort
    nur der letzte Wert, kein Verlauf, kein Ort.
  - Fahrten melden (eigenes Haekchen): nach einer Fahrt ohne Laden gehen Kilometer, Dauer,
    Ladestand vorher/nachher und Aussentemperatur an den Planer - KEINE Koordinaten, keine
    Uhrzeit. Daraus lernt der Planer den echten Verbrauch deines Autos.
Der Schluessel aus dem Link bleibt auf diesem Rechner und geht nur als Kopfzeile an den Planer.
"""
import json
import re
import time
import urllib.request

BASIS = "https://byd.serveone.at/ev/"
UA = "ev-cockpit"
_TOKEN = re.compile(r"(?:[#&?]z=)?\b([0-9a-f]{32})\b")


def token_aus_link(text):
    """Persoenlicher Link (…/ev/#z=<32 hex>) oder nackter Schluessel -> Schluessel bzw. ''."""
    m = _TOKEN.search((text or "").strip().lower())
    return m.group(1) if m else ""


def oeffnen_url(token):
    return BASIS + ("#z=" + token if token else "")


def _anfrage(pfad, token, daten=None, timeout=12):
    req = urllib.request.Request(
        BASIS + "api/" + pfad, method="POST" if daten is not None else "GET",
        data=json.dumps(daten).encode("utf-8") if daten is not None else None,
        headers={"X-Member-Token": token, "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            return e.code, {}


def pruefe_token(token, anfrage=_anfrage):
    """True, wenn der Planer den Schluessel als Mitglied anerkennt (die Fahrzeugliste allein
    ist oeffentlich und sagt darueber nichts)."""
    code, _ = anfrage("mein-soc", token)
    return code == 200


def fahrzeuge(token, anfrage=_anfrage):
    """Profilnamen aus dem Planer (allgemeine + eigene)."""
    code, d = anfrage("fahrzeuge", token)
    if code != 200:
        raise RuntimeError("Planer antwortet %s" % code)
    liste = d if isinstance(d, list) else (d.get("fahrzeuge") or [])
    return [{"name": f.get("name"), "akku_kwh": f.get("akku_kwh"), "eigen": bool(f.get("eigen"))}
            for f in liste if f.get("name")]


def passendes_profil(profile, modell, akku_kwh):
    """Profil, das zum Cockpit-Modell passt (Modellname + Akkugroesse), sonst ''."""
    w = [x for x in re.split(r"[^a-z0-9]+", (modell or "").lower()) if x and x != "byd"]
    best, punkte = "", 0.0
    for p in profile:
        n = (p["name"] or "").lower()
        t = sum(1 for x in w if x in n)
        if not t:
            continue
        a = p.get("akku_kwh") or 0
        s = t - (abs(a - akku_kwh) / 10.0 if akku_kwh and a else 0.5)
        if s > punkte:
            best, punkte = p["name"], s
    return best


class Fahrtenschreiber:
    """Erkennt Fahrten aus aufeinanderfolgenden Abfragen (Kilometerstand, Ladestand, Laden).

    Start: der Kilometerstand steigt. Ende: zwei Abfragen ohne neuen Kilometer, oder 10 min
    Stillstand. Zeitpunkte jeweils in der Mitte zwischen zwei Abfragen (die Abfrage kommt nur
    alle paar Minuten). Faellt waehrenddessen Laden an, wird die Fahrt verworfen.
    """
    MIN_KM = 15.0
    MIN_MIN = 10.0
    STILL_S = 600

    def __init__(self):
        self.letzte = None      # (t, km, soc)
        self.fahrt = None
        self.still = 0

    def neu(self, t, km, soc, laedt, temp=None):
        """Eine Abfrage einspeisen; liefert eine fertige Fahrt (dict) oder None."""
        if km is None or soc is None:
            return None
        km, soc = float(km), float(soc)
        alt, self.letzte = self.letzte, (t, km, soc)
        if alt is None:
            return None
        t0, km0, soc0 = alt
        if self.fahrt is None:
            if km > km0 + 0.5 and not laedt:
                self.fahrt = {"start_t": (t0 + t) / 2.0, "start_km": km0, "start_soc": soc0,
                              "bewegt_t": t, "ende_t": t, "temps": [], "geladen": False}
                if temp is not None:
                    self.fahrt["temps"].append(float(temp))
            return None
        f = self.fahrt
        if laedt or soc > f["start_soc"] + 0.5:
            f["geladen"] = True
        if temp is not None:
            f["temps"].append(float(temp))
        if km > km0 + 0.05:
            f["bewegt_t"], self.still = t, 0
            return None
        self.still += 1
        if self.still == 1:
            f["ende_t"] = (f["bewegt_t"] + t) / 2.0
        if self.still >= 2 or t - f["bewegt_t"] >= self.STILL_S:
            return self._abschluss(km, soc)
        return None

    def _abschluss(self, km, soc):
        f, self.fahrt, self.still = self.fahrt, None, 0
        strecke = km - f["start_km"]
        dauer = (f["ende_t"] - f["start_t"]) / 60.0
        if f["geladen"] or strecke < self.MIN_KM or dauer < self.MIN_MIN or soc >= f["start_soc"]:
            return None
        temps = sorted(f["temps"])
        aus = {"km": round(strecke, 1), "dauer_min": round(dauer), "soc_start": f["start_soc"],
               "soc_ende": soc}
        if temps:
            aus["temp_c"] = temps[len(temps) // 2]
        return aus


class Bruecke:
    """Haelt den Zustand fuer Cockpit-Thread und Anzeige."""
    SOC_TAKT_S = 900

    def __init__(self, anfrage=_anfrage, uhr=time.time):
        self.anfrage, self.uhr = anfrage, uhr
        self.schreiber = Fahrtenschreiber()
        self.soc_gesendet = None
        self.soc_t = 0.0
        self.status = {"soc": None, "soc_t": None, "fahrten": 0, "fahrt_letzte": None, "fehler": ""}

    def nach_abfrage(self, cfg, st):
        token = cfg.get("planer_token") or ""
        if not (cfg.get("planer") and token):
            return
        jetzt = self.uhr()
        soc = st.get("soc")
        if st.get("online") == "ON" and soc is not None and (
                self.soc_gesendet is None or abs(float(soc) - self.soc_gesendet) >= 1
                or jetzt - self.soc_t >= self.SOC_TAKT_S):
            code, d = self.anfrage("mein-soc", token, {"soc": float(soc), "quelle": "ev-cockpit"})
            if code == 200:
                self.soc_gesendet, self.soc_t = float(soc), jetzt
                self.status.update({"soc": float(soc), "soc_t": jetzt, "fehler": ""})
            else:
                self.status["fehler"] = d.get("fehler") or ("Planer antwortet %s" % code)
        fahrt = self.schreiber.neu(jetzt, st.get("odometer"), soc, st.get("charging") == "ON",
                                   st.get("temp_out"))
        if fahrt and cfg.get("planer_fahrten") and cfg.get("planer_fahrzeug"):
            fahrt["fahrzeug"] = cfg["planer_fahrzeug"]
            code, d = self.anfrage("fahrt", token, fahrt)
            if code == 200 and d.get("ok"):
                self.status["fahrten"] += 1
                self.status["fahrt_letzte"] = {"km": fahrt["km"], "kwh_100km": d.get("verbrauch_kwh_100km"),
                                               "t": jetzt}
            else:
                # Der Planer prueft streng (Tempo, Verbrauch); eine abgelehnte Fahrt ist kein Fehler
                self.status["fehler"] = "Fahrt nicht uebernommen: %s" % (d.get("fehler") or code)
