"""Freiwillige Anbindung an den Routenplaner der BYD-Community (https://byd.serveone.at/ev/).

Was passiert (nur mit Haekchen im Assistenten und dem persoenlichen Planer-Link):
  - Ladestand melden: der Planer fuellt damit den Start-Ladestand vor. Gespeichert wird dort
    nur der letzte Wert, kein Verlauf, kein Ort.
  - Fahrten auswerten (eigenes Haekchen): Fahrten bleiben auf DIESEM Rechner. Fuer jede Fahrt
    fragt das Cockpit beim Planer nur den Modellwert ab (dort wird nichts gespeichert), rechnet
    daraus selbst den Korrekturfaktor und schickt nur diesen Faktor (Vorgabe: kein Fahrtenbuch
    auf dem Server).
Ist Panoptes im Auto gekoppelt, meldet NUR Panoptes Ladestand und Faktor (je Auto eine Quelle,
sonst flackert der Ladestand bzw. Fahrten zaehlen doppelt). Das Cockpit liest dann nur.
Jede Meldung traegt die kurze Zufalls-Kennung `auto` (nie die VIN).
Der Schluessel aus dem Link bleibt auf diesem Rechner und geht nur als Kopfzeile an den Planer.
"""
import json
import re
import secrets
import time
import urllib.error
import urllib.request

BASIS = "https://byd.serveone.at/ev/"
UA = "ev-cockpit"
_TOKEN = re.compile(r"(?:[#&?]z=)?\b([0-9a-f]{32})\b")


def token_aus_link(text):
    """Persoenlicher Link (…/ev/#z=<32 hex>) oder nackter Schluessel -> Schluessel bzw. ''."""
    m = _TOKEN.search((text or "").strip().lower())
    return m.group(1) if m else ""


def neue_auto_kennung():
    """Kurze Zufalls-Kennung je Fahrzeug fuer das Planer-Feld `auto` (nie VIN oder VIN-Hash)."""
    return "evc-" + secrets.token_hex(4)


def panoptes_meldet(cfg):
    """True, wenn Panoptes im Auto gekoppelt ist - dann meldet Panoptes selbst an den Planer."""
    return bool(cfg.get("panoptes") and cfg.get("panoptes_url") and cfg.get("panoptes_code"))


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


SCHRUMPF_K = 4.0
FAKTOR_MIN, FAKTOR_MAX = 0.70, 1.40


def faktor_aus(verhaeltnisse):
    """Median der Verhaeltnisse gemessen/Modell, bei wenigen Fahrten zu 1.0 hin gezogen (wie im Planer)."""
    if not verhaeltnisse:
        return 1.0
    v = sorted(verhaeltnisse)
    n = len(v)
    med = v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0
    return max(FAKTOR_MIN, min(FAKTOR_MAX, 1.0 + (med - 1.0) * (n / (n + SCHRUMPF_K))))


class Bruecke:
    """Haelt den Zustand fuer Cockpit-Thread und Anzeige. `speicher` = (laden, speichern) fuer die
    lokalen Verhaeltnisse je Profil (bleiben auf diesem Rechner)."""
    SOC_TAKT_S = 900
    MAX_JE_PROFIL = 200

    def __init__(self, anfrage=_anfrage, uhr=time.time, speicher=None):
        self.anfrage, self.uhr = anfrage, uhr
        self.laden, self.speichern = speicher or ((lambda: {}), (lambda d: None))
        self.schreiber = Fahrtenschreiber()
        self.soc_gesendet = None
        self.soc_t = 0.0
        self.status = {"soc": None, "soc_t": None, "fahrten": 0, "fahrt_letzte": None, "fehler": ""}

    def nach_abfrage(self, cfg, st):
        token = cfg.get("planer_token") or ""
        if not (cfg.get("planer") and token):
            return
        if panoptes_meldet(cfg):
            self.status["panoptes"] = True      # Panoptes meldet selbst - hier nur lesen
            return
        self.status["panoptes"] = False
        auto = cfg.get("planer_auto") or ""
        jetzt = self.uhr()
        soc = st.get("soc")
        if st.get("online") == "ON" and soc is not None and (
                self.soc_gesendet is None or abs(float(soc) - self.soc_gesendet) >= 1
                or jetzt - self.soc_t >= self.SOC_TAKT_S):
            daten = {"soc": float(soc), "quelle": "ev-cockpit"}
            if auto:
                daten["auto"] = auto
            code, d = self.anfrage("mein-soc", token, daten)
            if code == 200:
                self.soc_gesendet, self.soc_t = float(soc), jetzt
                self.status.update({"soc": float(soc), "soc_t": jetzt, "fehler": ""})
            else:
                self.status["fehler"] = d.get("fehler") or ("Planer antwortet %s" % code)
        fahrt = self.schreiber.neu(jetzt, st.get("odometer"), soc, st.get("charging") == "ON",
                                   st.get("temp_out"))
        if fahrt and cfg.get("planer_fahrten") and cfg.get("planer_fahrzeug"):
            self._fahrt_auswerten(token, cfg["planer_fahrzeug"], fahrt, jetzt, auto)

    def _fahrt_auswerten(self, token, profil, fahrt, jetzt, auto=""):
        # 1. Modellwert holen (der Planer speichert nichts). Nur was das Modell braucht -
        #    der Ladestand vorher/nachher bleibt hier.
        frage = {k: fahrt[k] for k in ("km", "dauer_min", "temp_c") if k in fahrt}
        code, m = self.anfrage("modell-verbrauch", token, dict(frage, fahrzeug=profil))
        if code != 200 or not m.get("ok"):
            self.status["fehler"] = "Fahrt nicht ausgewertet: %s" % (m.get("fehler") or code)
            return
        kwh = (m.get("akku_kwh") or 0) * (fahrt["soc_start"] - fahrt["soc_ende"]) / 100.0
        verh = kwh / m["modell_kwh"] if m.get("modell_kwh") else 0
        if not (0.4 <= verh <= 2.5):
            self.status["fehler"] = "Fahrt unplausibel (Faktor %.2f) - nicht gezaehlt" % verh
            return
        # 2. lokal merken (nur Verhaeltnisse, keine Fahrtdaten) und Faktor rechnen
        alle = self.laden() or {}
        liste = (alle.get(profil) or [])[-(self.MAX_JE_PROFIL - 1):] + [round(verh, 4)]
        alle[profil] = liste
        self.speichern(alle)
        f = faktor_aus(liste)
        # 3. nur den fertigen Faktor senden
        daten = {"fahrzeug": profil, "faktor": round(f, 3), "fahrten": len(liste), "quelle": "ev-cockpit"}
        if auto:
            daten["auto"] = auto
        code, d = self.anfrage("mein-faktor", token, daten)
        if code == 200 and d.get("ok"):
            self.status["fahrten"] = len(liste)
            self.status["fahrt_letzte"] = {"km": fahrt["km"], "kwh_100km": round(kwh / fahrt["km"] * 100, 1),
                                           "faktor": round(f, 3), "t": jetzt}
            self.status["fehler"] = ""
        else:
            self.status["fehler"] = "Faktor nicht uebernommen: %s" % (d.get("fehler") or code)
