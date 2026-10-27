"""Wallbox-Adapter Home Assistant und Tuya (WALLBOX_VERTRAG v1.1 §0, §3, §4, §4b) im Cockpit.

Jeder Adapter liefert Ladepunkte im Format §3 und kann steuern (mit Zuruecklesen). Freigabe, Bestaetigung und
Protokoll liegen NICHT hier, sondern im Server darueber (wallbox_steuern) - ein Adapter kann sie nicht umgehen.
Modelldaten sind Daten: Tuya-DP-Bedeutung kommt aus static/wallbox-tuya-modelle.json (dieselbe Datei wie in Panoptes)
oder aus der eigenen Zuordnung; HA-Entitaeten ordnet der Nutzer zu (mit generischem Vorschlag, kein Code je Modell).
"""
import json
import math
import re
import time
import urllib.error
import urllib.parse
from pathlib import Path

from network_safety import open_lan_url, private_ziel

MODI = ("aus", "sofort", "minpv", "pv")
NAMEN = {"aus": "Aus", "sofort": "Sofort", "minpv": "Min+PV", "pv": "PV"}
SCHLUESSEL = re.compile(r"[a-z0-9_]{1,32}\Z")
ENTITAET = re.compile(r"[a-z_]{1,32}\.[a-z0-9_]{1,128}\Z")
UHRZEIT = re.compile(r"([01][0-9]|2[0-3]):[0-5][0-9]\Z")
DOMAENEN = {"laedt": ("binary_sensor", "sensor", "switch", "input_boolean"), "leistung": ("sensor",),
            "modus": ("select", "input_select", "switch"), "ziel": ("number", "input_number"),
            "strom": ("number", "input_number", "select"), "startzeit": ("time", "input_datetime"),
            "start": ("button",), "stop": ("button",),
            "freigabe": ("switch", "input_boolean"), "echo": ("sensor",)}   # nur LESEN: Sperre der Bruecke, Echo des Soll-Ladestroms
# Nie als Wallbox-Steuerung nehmen (Sicherheits-/Geraete-Einstellungen) und nie Fahrzeug-Entitaeten als Wallbox anzeigen.
NIE_STEUERN = re.compile(r"unearth|earth|erdung|lock|sperre|child|kinder|led|_led|light|licht|display|sound|beep|phase|rcd|"
                         r"reset|restart|neu_starten|reboot|update|firmware|erlaubt|freigabe|maximum_current|max_current|max_strom|calibrat")
FAHRZEUG = re.compile(r"(^|[._ ])(byd|overdrive|surfmate|panoptes|vehicle|fahrzeug)")
STEUER_ROLLEN = ("modus", "ziel", "strom", "start", "stop")
TABELLE = Path(__file__).with_name("static") / "wallbox-tuya-modelle.json"


class WallboxFehler(Exception):
    def __init__(self, code, status=400):
        super().__init__(code)
        self.code, self.status = code, status


def _zahl(x):
    if isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return int(v) if v == int(v) else v


def ganzzahl(wert, mi, ma):
    if isinstance(wert, bool):
        raise WallboxFehler("wert_ungueltig")
    try:
        v = float(wert)
    except (TypeError, ValueError):
        raise WallboxFehler("wert_ungueltig")
    if v != int(v) or not mi <= v <= ma:
        raise WallboxFehler("wert_ungueltig")
    return int(v)


def basis_url(url):
    """HA-Adresse -> http://<private IP>:<port> (§2: nur privat, Namen aufgeloest, keine Benutzer:Passwort@)."""
    import ha_finden
    u = urllib.parse.urlsplit(ha_finden.normal(str(url or "")))      # ohne Port: HA-Standard 8123
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
        raise WallboxFehler("adresse_gesperrt")
    try:
        schema, ziel = private_ziel(u.hostname, "Home Assistant")
        port = u.port or (443 if u.scheme == "https" else 80)
    except ValueError:
        raise WallboxFehler("adresse_gesperrt")
    if schema == "https":                    # nur im Praxistest (testziel)
        return "https://%s:%d" % (ziel, port)
    if u.scheme == "https":
        raise WallboxFehler("adresse_gesperrt")   # https auf IP ohne Zertifikatsnamen: v1 nur http im Heimnetz
    return "http://%s:%d" % (ziel, port)


def _ha_http(methode, url, token, daten=None, timeout=4.0):
    kopf = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    try:
        with open_lan_url(url, timeout=timeout, method=methode, headers=kopf,
                          data=json.dumps(daten).encode() if daten is not None else None) as r:
            roh = r.read(524289)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise WallboxFehler("anmeldung", 502)
        if e.code == 404:
            return None
        raise WallboxFehler("nicht_erreichbar", 502)
    except ValueError:
        raise WallboxFehler("adresse_gesperrt")
    except OSError:
        raise WallboxFehler("nicht_erreichbar", 502)
    if len(roh) > 524288:
        raise WallboxFehler("antwort_ungueltig", 502)
    try:
        return json.loads(roh.decode("utf-8") or "null")
    except ValueError:
        raise WallboxFehler("antwort_ungueltig", 502)


# ================================================================ Home Assistant
def pruefe_ha_zuordnung(z):
    if not isinstance(z, dict) or not SCHLUESSEL.match(str(z.get("schluessel") or "")):
        raise WallboxFehler("einstellung_ungueltig")
    o = {"schluessel": z["schluessel"], "titel": str(z.get("titel") or "").strip()[:40]}
    for rolle, doms in DOMAENEN.items():
        e = str(z.get(rolle) or "").strip()
        if not e:
            o[rolle] = None
            continue
        if not ENTITAET.match(e) or e.split(".")[0] not in doms:
            raise WallboxFehler("einstellung_ungueltig")
        o[rolle] = e
    opt = z.get("modusOptionen") if isinstance(z.get("modusOptionen"), dict) else {}
    o["modusOptionen"] = {m: (str(opt.get(m) or "").strip()[:64] or None) for m in MODI}
    return o


def ha_bereinigen(z):
    """Gespeicherte Zuordnung entschaerfen (1.17.1): Fahrzeug-Entitaeten raus, nie steuerbare Schalter raus.
    Fall Alfred 23.10.: 1.15 hatte switch.ev_charger_unearthed als 'Modus' und das Ladelimit des Autos als 'Ziel' vorgeschlagen."""
    o, weg = dict(z), []
    for rolle in DOMAENEN:
        e = o.get(rolle)
        if not e:
            continue
        if FAHRZEUG.search(e) or (rolle in STEUER_ROLLEN and NIE_STEUERN.search(e)):
            o[rolle] = None
            weg.append(e)
    o["entfernt"] = weg
    return o


def _gueltig(s):
    return isinstance(s, dict) and str(s.get("state") or "") not in ("", "unavailable", "unknown")


def _laedt(s):
    if not _gueltig(s):
        return None
    return str(s["state"]).strip().lower() in ("on", "true", "charging", "laedt", "lädt", "laden", "charger_charging")


def _knopf_da(s):
    """HA-Knoepfe melden 'unknown', bis sie einmal gedrueckt wurden; nur 'unavailable' heisst: nicht nutzbar."""
    return isinstance(s, dict) and str(s.get("state") or "") not in ("", "unavailable")


def _erreichbar(e):
    """False nur, wenn ALLE zugeordneten Entitaeten 'unavailable' melden (HA erreicht das Geraet nicht)."""
    werte = [x for x in e.values() if isinstance(x, dict)]
    return None if not werte else not all(str(x.get("state")) == "unavailable" for x in werte)


def _leistung_w(s):
    if not _gueltig(s):
        return None
    w = _zahl(s.get("state"))
    if w is None:
        return None
    e = str((s.get("attributes") or {}).get("unit_of_measurement") or "W").strip()
    f = {"w": 1, "kw": 1000, "mw": 1000000}.get(e.lower())
    return None if f is None else int(round(w * f))


def ha_ladepunkt(z, e):
    """Rein: Ladepunkt §3 aus Zuordnung z und gelesenen Zustaenden e[rolle] (fehlend = None)."""
    o = {"id": "ha:" + z["schluessel"], "titel": z.get("titel") or z["schluessel"], "art": "wallbox", "verbunden": None,
         "laedt": _laedt(e.get("laedt")), "leistungW": _leistung_w(e.get("leistung")), "fahrzeug": None, "fahrzeugSoc": None}
    modi, modus, roh = [], None, None
    m = e.get("modus")
    if _gueltig(m):
        roh = m["state"]
        if (z.get("modus") or "").startswith("switch."):
            modi = ["aus", "sofort"]
            modus = "sofort" if roh == "on" else "aus" if roh == "off" else None
        else:
            vorhanden = (m.get("attributes") or {}).get("options") or []
            for k in MODI:
                opt = (z.get("modusOptionen") or {}).get(k)
                if opt and opt in vorhanden:
                    modi.append(k)
                    if opt == roh:
                        modus = k
    if not modi and z.get("start") and z.get("stop") and _knopf_da(e.get("start")) and _knopf_da(e.get("stop")):
        modi = ["aus", "sofort"]                   # Knoepfe Laden starten/stoppen (z. B. tuya_local): Zustand = laedt
        modus = {True: "sofort", False: "aus"}.get(o["laedt"])
    o.update(modus=modus, modusRoh=roh)
    zi = e.get("ziel")
    zmin, zmax = 20, 100
    if _gueltig(zi):
        a = zi.get("attributes") or {}
        zmin, zmax = max(0, int(round(_zahl(a.get("min")) or 20))), min(100, int(round(_zahl(a.get("max")) or 100)))
    o.update(zielSoc=_zahl(zi["state"]) if _gueltig(zi) else None, zielMin=zmin, zielMax=zmax)
    st = e.get("strom")
    strom_f = None
    if _gueltig(st) and str(st.get("entity_id") or (z.get("strom") or "")).startswith("select."):
        stufen = _stufen((st.get("attributes") or {}).get("options"))
        strom_f = {"min": stufen[0], "max": stufen[-1], "stufen": stufen} if stufen else None
    elif _gueltig(st):
        a = st.get("attributes") or {}
        smin, smax = max(1, int(round(_zahl(a.get("min")) or 6))), min(80, int(round(_zahl(a.get("max")) or 16)))
        if smin <= smax:
            strom_f = {"min": smin, "max": smax}
    o["stromA"] = _zahl(st["state"]) if _gueltig(st) else None
    sz = e.get("startzeit")
    a = (sz or {}).get("attributes") or {}
    nur_uhr = _gueltig(sz) and ((z.get("startzeit") or "").startswith("time.") or (a.get("has_time") and not a.get("has_date")))
    zeit = str(sz["state"])[:5] if nur_uhr else ""
    o["plan"] = {"art": "start_um", "zeit": zeit} if nur_uhr and UHRZEIT.match(zeit) else None
    fg, ec = e.get("freigabe"), e.get("echo")
    o["stromEchoA"] = _zahl(ec["state"]) if _gueltig(ec) else None
    o["faehigkeiten"] = {"modus": modi, "ziel": _gueltig(zi), "strom": strom_f, "plan": "start_um" if nur_uhr else None}
    if _gueltig(fg) and str(fg["state"]).lower() == "off":
        o["faehigkeiten"]["gesperrt"] = True
    o["erreichbar"] = _erreichbar(e)
    o["entfernt"] = list(z.get("entfernt") or [])
    return o


WALLBOX_WOERTER = ("charg", "lade", "wallbox", "evse", "ev_", "_ev", "charger", "pile", "ladestation", "wb_")


def ha_vorschlag(alle):
    """Rein: je Rolle Kandidaten + beste Zuordnung aus GET /api/states - generisch ueber Domaene, Einheit,
    device_class und Wallbox-Woerter, kein Code je Modell (wie Kern 6s HaQuelle.vorschlagAus)."""
    kand = {r: [] for r in ("modus", "strom", "ziel", "leistung", "laedt", "startzeit")}
    beste, punkte = {}, {}
    for s in (alle or [])[:5000]:
        if not isinstance(s, dict):
            continue
        eid = str(s.get("entity_id") or "")
        if not ENTITAET.match(eid):
            continue
        a = s.get("attributes") if isinstance(s.get("attributes"), dict) else {}
        name = (eid + " " + str(a.get("friendly_name") or "")).lower()
        wort = 2 if any(w in name for w in WALLBOX_WOERTER) else 0
        einheit, klasse, st, dom = str(a.get("unit_of_measurement") or ""), str(a.get("device_class") or ""), str(s.get("state") or ""), eid.split(".")[0]
        rolle, p = None, wort
        if dom == "switch" and wort:
            rolle = "modus"
        elif dom in ("number", "input_number") and (einheit == "A" or klasse == "current"):
            rolle, p = "strom", p + 2
        elif dom in ("number", "input_number") and einheit == "%" and wort:
            rolle = "ziel"
        elif dom == "sensor" and (klasse == "power" or einheit in ("W", "kW")) and wort:
            rolle, p = "leistung", p + (1 if klasse == "power" else 0)
        elif dom == "sensor" and st.startswith("charger_"):
            rolle, p = "laedt", p + 3
        elif dom == "binary_sensor" and (klasse == "battery_charging" or (wort and klasse not in MELDER_KLASSEN)):
            rolle = "laedt"
        elif dom == "sensor" and wort and any(w in name for w in ("status", "state", "zustand")):
            rolle = "laedt"
        elif dom == "time" and wort:
            rolle = "startzeit"
        if not rolle:
            continue
        if len(kand[rolle]) < 20:
            kand[rolle].append({"entity_id": eid, "name": str(a.get("friendly_name") or eid)[:80], "zustand": st[:40], "einheit": einheit[:10],
                                "optionen": [str(x)[:64] for x in (a.get("options") or [])][:12] if dom in ("select", "input_select") else []})
        if p > punkte.get(rolle, -1):
            punkte[rolle], beste[rolle] = p, eid
    z = dict({"schluessel": "wallbox", "titel": "Wallbox", "modusOptionen": {}}, **{r: beste.get(r) for r in kand})
    return {"ok": True, "kandidaten": kand, "vorschlag": z}


MELDER_KLASSEN = ("problem", "plug", "connectivity", "safety", "lock", "door", "running", "tamper", "update")


def _stufen(optionen):
    """Ganzzahlige Stufen eines select (nur wenn ALLE Optionen Zahlen sind) -> sortierte Liste oder []."""
    try:
        v = sorted({int(str(o).strip()) for o in (optionen or [])})
    except ValueError:
        return []
    return v if 1 <= len(v) <= 20 and v[0] >= 1 and v[-1] <= 80 else []


def _rolle(s, a, eid, name):
    """Welche Rolle passt zu einer Entitaet (generisch, kein Code je Modell) -> (rolle, punkte) oder (None, 0)."""
    if FAHRZEUG.search(eid) or FAHRZEUG.search(name):
        return None, 0
    wort = 2 if any(w in name for w in WALLBOX_WOERTER) else 0
    einheit, klasse, st, dom = str(a.get("unit_of_measurement") or ""), str(a.get("device_class") or ""), str(s.get("state") or ""), eid.split(".")[0]
    if dom in ("switch", "input_boolean") and re.search(r"steuern_erlaubt|steuerung_erlaubt|steuern erlaubt|steuerung erlaubt", eid + " " + name):
        return "freigabe", wort + 5                # Sperre der Wallbox-Bruecke: nur lesen, nie schalten
    if dom == "sensor" and wort and (einheit == "A" or klasse == "current") and re.search(r"soll|eingestellt|target|setpoint", name):
        return "echo", wort + 3                    # Echo des eingestellten Ladestroms
    if dom in ("switch", "select", "input_select", "number", "input_number", "button") and NIE_STEUERN.search(eid + " " + name):
        return None, 0
    if dom == "button" and wort:
        if re.search(r"stop|halt|beend", name):
            return "stop", wort + 1
        if re.search(r"charge|start|laden", name):
            return "start", wort + 1
        return None, 0
    if dom == "select" and wort and re.search(r"strom|current|ampere", name) and _stufen(a.get("options")):
        return "strom", wort + 2                   # Stufen-Ladestrom (z. B. 6/8/10/13/16 A)
    if dom == "sensor" and wort and "charging" in [str(x).lower() for x in (a.get("options") or [])]:
        return "laedt", wort + 3
    if dom == "switch" and wort:
        return "modus", wort
    if dom in ("select", "input_select") and wort and any(m in name for m in ("mode", "modus", "lademodus")):
        return "modus", wort + 1
    if dom in ("number", "input_number") and (einheit == "A" or klasse == "current"):
        return "strom", wort + 2
    if dom in ("number", "input_number") and einheit == "%" and wort:
        return "ziel", wort
    if dom == "sensor" and (klasse == "power" or einheit in ("W", "kW")) and wort:
        return "leistung", wort + (1 if klasse == "power" else 0)
    if dom == "sensor" and st.startswith("charger_"):
        return "laedt", wort + 3
    if dom == "binary_sensor" and (klasse == "battery_charging" or (wort and klasse not in MELDER_KLASSEN and not NIE_STEUERN.search(eid))):
        return "laedt", wort
    if dom == "sensor" and wort and any(w in name for w in ("status", "state", "zustand")):
        return "laedt", wort
    if dom == "time" and wort:
        return "startzeit", wort
    return None, 0


MODUS_WOERTER = {"aus": ("off", "aus", "stop", "disabled"), "sofort": ("now", "fast", "sofort", "schnell", "immediate", "max"),
                 "minpv": ("minpv", "min+pv", "min_pv", "min pv"), "pv": ("pv", "solar", "sonne")}


def _modus_optionen(optionen):
    """Optionen eines select-Lademodus vorsichtig zuordnen (nur eindeutige Treffer, sonst leer lassen)."""
    o = {}
    for m, woerter in MODUS_WOERTER.items():
        treffer = [x for x in optionen if str(x).strip().lower() in woerter]
        if len(treffer) == 1:
            o[m] = treffer[0]
    return o


def ha_geraete(alle, geraet=None):
    """Rein: plausible Wallboxen in HA, je HA-Geraet gruppiert (geraet: entity_id -> (device_id, Name); ohne: nach dem
    ersten Wort der Objekt-ID). Plausibel = (Schalter/Modus oder Ladestrom) und (Leistung oder Lade-Status)."""
    states, gruppen = {}, {}
    for s in (alle or [])[:5000]:
        if not isinstance(s, dict) or not ENTITAET.match(str(s.get("entity_id") or "")):
            continue
        eid = s["entity_id"]
        states[eid] = s
        a = s.get("attributes") if isinstance(s.get("attributes"), dict) else {}
        rolle, p = _rolle(s, a, eid, (eid + " " + str(a.get("friendly_name") or "")).lower())
        if not rolle:
            continue
        did, dname = (geraet or {}).get(eid) or ("", "")
        teile = eid.split(".")[1].split("_")
        key = did or "obj:" + "_".join(teile[:1] if teile[0] in ("wallbox", "evse", "wb") else teile[:2])
        g = gruppen.setdefault(key, {"name": dname, "rollen": {}})
        if rolle not in g["rollen"] or p > g["rollen"][rolle][1]:
            g["rollen"][rolle] = (eid, p)
    aus = []
    for key, g in gruppen.items():
        r = g["rollen"]
        if not (("modus" in r or "strom" in r or ("start" in r and "stop" in r)) and ("leistung" in r or "laedt" in r)):
            continue
        name = g["name"] or (key.split(":")[-1].replace("_", " ").title() if key.startswith("obj:wallbox") else "") or str((states[(r.get("leistung") or r.get("modus") or next(iter(r.values())))[0]].get("attributes") or {}).get("friendly_name") or key.split(":")[-1])
        z = {"schluessel": "wallbox", "titel": name.strip()[:40] or "Wallbox", "modusOptionen": {}}
        for rolle in DOMAENEN:
            z[rolle] = r[rolle][0] if rolle in r else None
        if z["modus"] and not z["modus"].startswith("switch."):
            z["modusOptionen"] = _modus_optionen((states[z["modus"]].get("attributes") or {}).get("options") or [])
        try:
            z = pruefe_ha_zuordnung(z)
        except WallboxFehler:
            continue
        lp = ha_ladepunkt(z, {rolle: dict(states[eid], entity_id=eid) for rolle, (eid, _) in r.items()})
        aus.append({"name": z["titel"], "zuordnung": z, "leistungW": lp["leistungW"], "laedt": lp["laedt"], "modus": lp["modus"],
                    "stromA": lp["stromA"], "rollen": sorted(r), "punkte": sum(p for _, p in r.values()) + 2 * len(r)})
    return sorted(aus, key=lambda x: -x["punkte"])


def _vorlage(eids):
    """Jinja fuer POST /api/template: je Entitaet [entity_id, device_id, Geraetename]. Nur gepruefte IDs (ENTITAET)."""
    liste = json.dumps([e for e in eids if ENTITAET.match(e)][:200])
    return ("{%- set ns = namespace(d=[]) -%}{%- for e in " + liste + " -%}{%- set i = device_id(e) -%}"
            "{%- set ns.d = ns.d + [[e, i or '', ((device_attr(i, 'name_by_user') or device_attr(i, 'name') or '') if i else '')]] -%}"
            "{%- endfor -%}{{ ns.d | tojson }}")


WARTE_ECHO_S = 25
TUYA_DOMAENEN = ("localtuya", "tuya_local", "tuya")


class HaQuelle:
    def __init__(self, url, token, zuordnungen, http=_ha_http, schlaf=time.sleep):
        self.basis, self.token, self.http, self.schlaf = basis_url(url), token, http, schlaf
        self.zu = [ha_bereinigen(z) for z in (zuordnungen or [])]
        if not token:
            raise WallboxFehler("anmeldung", 502)

    def _states(self, z):
        e = {}
        for rolle in DOMAENEN:
            if z.get(rolle):
                e[rolle] = self.http("GET", self.basis + "/api/states/" + z[rolle], self.token)
        return e

    def ladepunkte(self):
        return [ha_ladepunkt(z, self._states(z)) for z in self.zu]

    def vorschlag(self):
        alle = self.http("GET", self.basis + "/api/states", self.token)
        if not isinstance(alle, list):
            raise WallboxFehler("antwort_ungueltig", 502)
        return ha_vorschlag(alle)

    def auto(self):
        """Nur lesend, auf Knopfdruck bzw. einmal beim Start: plausible Wallboxen + ob Tuya schon in HA eingebunden ist."""
        alle = self.http("GET", self.basis + "/api/states", self.token)
        if not isinstance(alle, list):
            raise WallboxFehler("antwort_ungueltig", 502)
        roh = ha_geraete(alle)
        eids = sorted({e for g in roh for e in g["zuordnung"].values() if isinstance(e, str) and "." in e})
        geraet = {}
        if eids:
            try:
                d = self.http("POST", self.basis + "/api/template", self.token, {"template": _vorlage(eids)})
                geraet = {x[0]: (x[1], x[2]) for x in d if isinstance(x, list) and len(x) == 3} if isinstance(d, list) else {}
            except WallboxFehler:
                geraet = {}
        geraete = ha_geraete(alle, geraet) if geraet else roh
        tuya = None
        try:
            e = self.http("GET", self.basis + "/api/config/config_entries/entry", self.token)
            if isinstance(e, list):
                tuya = sorted({str(x.get("domain")) for x in e if isinstance(x, dict) and x.get("domain") in TUYA_DOMAENEN})
        except WallboxFehler:
            tuya = None
        return {"geraete": geraete[:10], "tuya_in_ha": tuya}

    def _zuordnung(self, lid):
        for z in self.zu:
            if "ha:" + z["schluessel"] == lid:
                return z
        raise WallboxFehler("ladepunkt_unbekannt", 404)

    def _dienst(self, dom, dienst, daten):
        self.http("POST", self.basis + "/api/services/%s/%s" % (dom, dienst), self.token, daten)

    def steuern(self, lid, aktion, wert):
        z = self._zuordnung(lid)
        vorher = ha_ladepunkt(z, self._states(z))
        f = vorher["faehigkeiten"]
        if f.get("gesperrt"):
            raise WallboxFehler("bruecke_gesperrt", 409)       # nichts senden: die Bruecke wuerde ohnehin ablehnen
        if aktion == "modus":
            if wert not in f["modus"]:
                raise WallboxFehler("nicht_unterstuetzt")
            eid = z.get("modus") or ""
            if not eid and z.get("start") and z.get("stop"):
                self._dienst("button", "press", {"entity_id": z["stop"] if wert == "aus" else z["start"]})
                for i in range(WARTE_ECHO_S):
                    self.schlaf(0.4 if i == 0 else 1.0)
                    nach = ha_ladepunkt(z, self._states(z))
                    if nach["laedt"] is (wert == "sofort"):
                        return {"uebernommen": True, "ladepunkt": nach}
                # Knopf gedrueckt, Zustand nicht (sicher) zurueckzulesen -> ehrlich "unbekannt" (§0 Regel 6)
                return {"uebernommen": None if nach["laedt"] is None else False, "ladepunkt": nach}
            if eid.startswith("switch."):
                self._dienst("switch", "turn_off" if wert == "aus" else "turn_on", {"entity_id": eid})
            else:
                self._dienst(eid.split(".")[0], "select_option", {"entity_id": eid, "option": z["modusOptionen"][wert]})
            feld, soll = "modus", wert
        elif aktion == "ziel":
            if not f["ziel"]:
                raise WallboxFehler("nicht_unterstuetzt")
            soll = ganzzahl(wert, vorher["zielMin"], vorher["zielMax"])
            self._dienst(z["ziel"].split(".")[0], "set_value", {"entity_id": z["ziel"], "value": soll})
            feld = "zielSoc"
        elif aktion == "strom":
            if not f["strom"]:
                raise WallboxFehler("nicht_unterstuetzt")
            soll = ganzzahl(wert, f["strom"]["min"], f["strom"]["max"])
            if z["strom"].startswith("select."):
                if soll not in f["strom"].get("stufen", []):
                    raise WallboxFehler("wert_ungueltig")
                self._dienst("select", "select_option", {"entity_id": z["strom"], "option": str(soll)})
            else:
                self._dienst(z["strom"].split(".")[0], "set_value", {"entity_id": z["strom"], "value": soll})
            feld = "stromEchoA" if z.get("echo") else "stromA"
        else:
            raise WallboxFehler("nicht_unterstuetzt")
        nach = vorher
        for i in range(WARTE_ECHO_S):              # schlafende Wallbox: Bruecke wiederholt einmal -> bis ~25 s
            self.schlaf(0.4 if i == 0 else 1.0)
            nach = ha_ladepunkt(z, self._states(z))
            if str(nach.get(feld)) == str(soll):
                return {"uebernommen": True, "ladepunkt": nach}
        return {"uebernommen": False, "ladepunkt": nach}


# ================================================================ Tuya
DP = re.compile(r"[1-9][0-9]{0,2}\Z")
CODE = re.compile(r"[a-z][a-z0-9_]{0,47}\Z")
ROLLEN = ("schalter", "strom", "status", "leistung")


def tabelle_laden(pfad=TABELLE):
    try:
        return json.loads(Path(pfad).read_text("utf-8"))
    except Exception:
        return {"modelle": []}


def pruefe_tuya_zuordnung(z):
    """Tabelle oder Nutzer; None bleibt None. Mindestens eine Rolle."""
    if z is None:
        return None
    if not isinstance(z, dict):
        raise WallboxFehler("einstellung_ungueltig")
    o = {}
    for rolle in ROLLEN:
        r = z.get(rolle)
        if not isinstance(r, dict):
            continue
        dp, code = str(r.get("dp") or ""), str(r.get("code") or "")
        if (not dp and not code) or (dp and not DP.match(dp)) or (code and not CODE.match(code)):
            raise WallboxFehler("einstellung_ungueltig")
        s = {"dp": dp or None, "code": code or None}
        if rolle == "strom":
            mi, ma, fa = r.get("min"), r.get("max"), r.get("faktor", 1)
            if not all(isinstance(x, int) and not isinstance(x, bool) for x in (mi, ma, fa)) or mi < 1 or ma > 80 or mi > ma or not 1 <= fa <= 1000:
                raise WallboxFehler("einstellung_ungueltig")
            s.update(min=mi, max=ma, faktor=fa)
        elif rolle == "status":
            s["laedt"] = [str(v)[:40] for v in (r.get("laedt") or [])[:10] if str(v)]
        elif rolle == "leistung":
            f = _zahl(r.get("faktorW", 1))
            if f is None or not 0 < f <= 1000000:
                raise WallboxFehler("einstellung_ungueltig")
            s["faktorW"] = f
        o[rolle] = s
    if not o:
        raise WallboxFehler("einstellung_ungueltig")
    return o


def _passt(v, regel):
    if v is None:
        return False
    if regel == "bool":
        return isinstance(v, bool)
    if regel == "int":
        return isinstance(v, (int, float)) and not isinstance(v, bool) and float(v).is_integer()
    if regel == "text":
        return isinstance(v, str)
    if not isinstance(v, str) or not regel or len(regel) > 100:
        return False
    try:
        return re.search(regel, v) is not None
    except re.error:
        return False


def erkenne(tabelle, werte):
    """Regeln erkennung.lan der Tabelle (alle muessen passen) -> (modell, zuordnung) oder None."""
    for m in (tabelle or {}).get("modelle") or []:
        er = ((m or {}).get("erkennung") or {}).get("lan") or {}
        if er and all(_passt(werte.get(k), r) for k, r in er.items()):
            try:
                return m.get("id"), pruefe_tuya_zuordnung(m.get("dp"))
            except WallboxFehler:
                continue
    return None


def modell_zuordnung(tabelle, modell):
    for m in (tabelle or {}).get("modelle") or []:
        if modell and m.get("id") == modell:
            try:
                return pruefe_tuya_zuordnung(m.get("dp"))
            except WallboxFehler:
                return None
    return None


def tuya_ladepunkt(g, werte, z, stand, modell):
    """Rein: Ladepunkt §3 aus Geraet g, DP-Werten, wirksamer Zuordnung z (None = unbekannt)."""
    o = {"id": "tuya:" + g["schluessel"], "titel": g.get("titel") or g["schluessel"], "art": "wallbox", "verbunden": None,
         "laedt": None, "leistungW": None, "modus": None, "modusRoh": None, "zielSoc": None, "zielMin": 20, "zielMax": 100,
         "stromA": None, "fahrzeug": None, "fahrzeugSoc": None, "plan": None, "zuordnung": stand, "modell": modell}
    modi, strom_f = [], None
    if z:
        if z.get("schalter", {}).get("dp"):
            modi = ["aus", "sofort"]
            v = werte.get(z["schalter"]["dp"])
            if isinstance(v, bool):
                o["modus"] = "sofort" if v else "aus"
        st = z.get("status")
        if st and st.get("dp") and st["dp"] in werte:
            o["laedt"] = str(werte[st["dp"]]) in st.get("laedt", [])
        le = z.get("leistung")
        if le and le.get("dp") and _zahl(werte.get(le["dp"])) is not None:
            o["leistungW"] = int(round(_zahl(werte[le["dp"]]) * le.get("faktorW", 1)))
        sr = z.get("strom")
        if sr and sr.get("dp"):
            strom_f = {"min": sr["min"], "max": sr["max"]}
            if _zahl(werte.get(sr["dp"])) is not None:
                o["stromA"] = _zahl(_zahl(werte[sr["dp"]]) / sr.get("faktor", 1))
    o["faehigkeiten"] = {"modus": modi, "ziel": False, "strom": strom_f, "plan": None}
    roh = None
    if not z:   # unbekannt: rohe DPs zum Zuordnen (Werte, keine Schluessel/Adressen)
        roh = {}
        for k in list(werte)[:60]:
            v = werte[k]
            roh[str(k)[:8]] = (v[:64] + "…") if isinstance(v, str) and len(v) > 64 else v
    o["rohDps"] = roh
    return o


class TuyaQuelle:
    """geraete: [(konfig, zugriff)] mit zugriff.dps()/setze(); Konfig {schluessel, titel, modell, zuordnung}."""

    def __init__(self, geraete, tabelle=None, schlaf=time.sleep):
        self.geraete, self.tabelle, self.schlaf = list(geraete), tabelle if tabelle is not None else tabelle_laden(), schlaf

    def _wirksam(self, g, werte):
        if g.get("zuordnung"):
            return g["zuordnung"], "bekannt", None
        if g.get("modell"):
            z = modell_zuordnung(self.tabelle, g["modell"])
            if z:
                return z, "bekannt", g["modell"]
        er = erkenne(self.tabelle, werte)
        if er:
            return er[1], "erkannt", er[0]
        return None, "unbekannt", None

    def _lies(self, zugriff):
        import tuya_lan
        try:
            return zugriff.dps()
        except tuya_lan.TuyaFehler as e:
            raise WallboxFehler(e.code, 502)

    def ladepunkte(self):
        aus = []
        for g, zugriff in self.geraete:
            werte = self._lies(zugriff)
            z, stand, modell = self._wirksam(g, werte)
            aus.append(tuya_ladepunkt(g, werte, z, stand, modell))
        return aus

    def steuern(self, lid, aktion, wert):
        import tuya_lan
        for g, zugriff in self.geraete:
            if "tuya:" + g["schluessel"] == lid:
                break
        else:
            raise WallboxFehler("ladepunkt_unbekannt", 404)
        werte = self._lies(zugriff)
        z, stand, modell = self._wirksam(g, werte)
        if not z:
            raise WallboxFehler("tuya_zuordnung_fehlt")
        if aktion == "modus":
            if not z.get("schalter", {}).get("dp") or wert not in ("aus", "sofort"):
                raise WallboxFehler("nicht_unterstuetzt")
            k, roh = z["schalter"]["dp"], wert == "sofort"
        elif aktion == "strom":
            sr = z.get("strom")
            if not sr or not sr.get("dp"):
                raise WallboxFehler("nicht_unterstuetzt")
            k, roh = sr["dp"], ganzzahl(wert, sr["min"], sr["max"]) * sr.get("faktor", 1)
        else:
            raise WallboxFehler("nicht_unterstuetzt")
        try:
            zugriff.setze({k: roh})
        except tuya_lan.TuyaFehler as e:
            raise WallboxFehler(e.code, 502)
        nach = None
        for i in range(3):
            self.schlaf(0.5 if i == 0 else 1.0)
            werte = self._lies(zugriff)
            nach = tuya_ladepunkt(g, werte, z, stand, modell)
            v = werte.get(k)
            if (isinstance(roh, bool) and v is roh) or (not isinstance(roh, bool) and _zahl(v) == roh):
                return {"uebernommen": True, "ladepunkt": nach}
        return {"uebernommen": False, "ladepunkt": nach}


def pruefe_wert(lp, aktion, wert):
    """Werte VOR der Rueckfrage pruefen (§5.2.4) - gegen die Faehigkeiten des Ladepunkts. -> bereinigter Wert."""
    f = lp.get("faehigkeiten") or {}
    if lp.get("erreichbar") is False:
        raise WallboxFehler("ha_nicht_erreichbar", 502)
    if lp.get("art") != "wallbox":
        raise WallboxFehler("keine_wallbox")
    if lp.get("zuordnung") == "unbekannt":
        raise WallboxFehler("tuya_zuordnung_fehlt")
    if f.get("gesperrt"):
        raise WallboxFehler("bruecke_gesperrt", 409)
    if aktion == "modus":
        if wert not in (f.get("modus") or []):
            raise WallboxFehler("nicht_unterstuetzt")
        return wert
    if aktion == "strom":
        s = f.get("strom")
        if not s:
            raise WallboxFehler("nicht_unterstuetzt")
        v = ganzzahl(wert, s["min"], s["max"])
        if s.get("stufen") and v not in s["stufen"]:
            raise WallboxFehler("wert_ungueltig")
        return v
    if aktion == "ziel":
        if not f.get("ziel"):
            raise WallboxFehler("nicht_unterstuetzt")
        return ganzzahl(wert, lp.get("zielMin", 20), lp.get("zielMax", 100))
    raise WallboxFehler("aktion_ungueltig")
