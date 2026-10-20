"""Home Assistant als Datenquelle fuers Auto (nur lesend, REST-API mit Langzeit-Token).

Fuer alle, die ihr Auto schon in Home Assistant haben: BYD-Integration, Panoptes (MQTT-Discovery,
Geraet "SurfMate (...)"/"Panoptes (...)") oder etwas anderes. Der Assistent schlaegt passende
Sensoren vor, der Nutzer bestaetigt nur. Ist HA die Quelle, fragt das Cockpit die BYD-Cloud NICHT
ab (sonst zwei Abfrager auf einem Konto -> Fehler 6024); die Cloud dient dann nur fuer Fernbefehle.
"""
import json
import re
import urllib.request

FELDER = ("soc", "range_km", "odometer", "charging", "location")

# Wortgrenzen ohne "_" (HA-Namen heissen sensor.auto_ladestand) -> eigene Grenzen statt \b
def _w(x):
    return r"(?<![a-z0-9])(?:%s)(?![a-z0-9])" % x


_AUTO = re.compile(r"byd|surfmate|panoptes|dolphin|seal|sealion|atto|seagull|vehicle|fahrzeug|" +
                   _w("han|tang|auto|car|ev"), re.I)
_KEIN_AUTO = re.compile(r"phone|handy|iphone|pixel|galaxy|watch|tablet|ipad|laptop|" + _w("sm|uhr") + "|"
                        r"notebook|mouse|maus|keyboard|tastatur|remote|fernbedienung|headphone|airpods|"
                        r"sensor_battery|thermostat|rauchmelder|smoke|door_sensor|fenster|window", re.I)
_NAMEN = {
    "soc": re.compile(_w("soc") + r"|state.of.charge|ladestand|akkustand|battery.level|batterie|akku|elec.?percent", re.I),
    "range_km": re.compile(r"range|reichweite|endurance", re.I),
    "odometer": re.compile(r"odometer|kilometerstand|mileage|km.?stand|total.?km|gesamt", re.I),
    "charging": re.compile(r"charging|l[aä]dt|ladevorgang|is.?charging|ladezustand", re.I),
}


def _text(e):
    a = e.get("attributes") or {}
    return "%s %s" % (e.get("entity_id", ""), a.get("friendly_name", ""))


def _zahl(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _punkte(feld, e):
    """Wie gut passt eine Entitaet zu einem Feld? 0 = gar nicht."""
    eid, a = e.get("entity_id", ""), (e.get("attributes") or {})
    dom, t = eid.split(".", 1)[0], _text(e)
    einheit, dc = (a.get("unit_of_measurement") or "").lower(), a.get("device_class") or ""
    if _KEIN_AUTO.search(t):
        return 0
    auto = 2 if _AUTO.search(t) else 0
    if feld == "location":
        if dom != "device_tracker" or a.get("latitude") is None:
            return 0
        return 1 + auto
    name = 3 if _NAMEN[feld].search(t) else 0
    if feld == "soc":
        if dom != "sensor" or einheit != "%" or _zahl(e.get("state")) is None:
            return 0
        return (2 if dc == "battery" else 0) + name + auto if (dc == "battery" or name) else 0
    if feld in ("range_km", "odometer"):
        if dom != "sensor" or einheit not in ("km", "mi") or not name:
            return 0
        return name + auto + (1 if feld == "odometer" and dc == "distance" else 0)
    if feld == "charging":
        if dom == "binary_sensor" and (dc == "battery_charging" or name):
            return 2 + name + auto
        if dom == "sensor" and name and einheit == "":
            return name + auto
    return 0


def vorschlag(states):
    """-> {feld: {"wahl": entity_id|"", "kandidaten": [{"id","name","wert"}...]}}; bestes zuerst.
    Ohne Auto-Bezug im Namen wird nichts vorausgewaehlt (der Nutzer waehlt dann selbst)."""
    aus = {}
    for feld in FELDER:
        k = sorted(((p, e) for e in states for p in [_punkte(feld, e)] if p > 0),
                   key=lambda x: -x[0])
        kand = [{"id": e["entity_id"], "name": (e.get("attributes") or {}).get("friendly_name") or e["entity_id"],
                 "wert": e.get("state")} for _, e in k[:15]]
        wahl = k[0][1]["entity_id"] if k and _AUTO.search(_text(k[0][1])) else ""
        aus[feld] = {"wahl": wahl, "kandidaten": kand}
    return aus


def aus_states(states, zuordnung):
    """HA-Zustaende + bestaetigte Zuordnung -> Cockpit-Felder (nur, was sicher lesbar ist)."""
    nach_id = {e.get("entity_id"): e for e in states}
    st = {}

    def wert(feld):
        e = nach_id.get((zuordnung or {}).get(feld) or "")
        if not e or e.get("state") in (None, "", "unknown", "unavailable"):
            return None, e
        return e.get("state"), e
    for feld in ("soc", "range_km", "odometer"):
        w, e = wert(feld)
        z = _zahl(w)
        if z is not None:
            if feld != "soc" and ((e.get("attributes") or {}).get("unit_of_measurement") or "").lower() == "mi":
                z = round(z * 1.609344, 1)
            st[feld] = z
    w, _ = wert("charging")
    if w is not None:
        st["charging"] = "ON" if str(w).lower() in ("on", "true", "1", "charging", "laedt", "lädt") else "OFF"
    _, e = wert("location")
    if e is not None:
        a = e.get("attributes") or {}
        la, lo = _zahl(a.get("latitude")), _zahl(a.get("longitude"))
        if la and lo:
            st["latitude"], st["longitude"] = la, lo
    return st


def hole_states(url, token, timeout=15):
    req = urllib.request.Request(url.rstrip("/") + "/api/states",
                                 headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))
