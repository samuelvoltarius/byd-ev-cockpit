"""Panoptes-Einstellungen im gekoppelten EV-Cockpit (Vertrag EINSTELLUNGEN_SCHEMA.md v1, Kern-Sitzung).

Das Cockpit zeichnet die Seite generisch aus GET /api/einstellungen/schema - ohne eigene Feldliste.
Dieses Modul ist die reine Logik (ohne Netz): was ist sichtbar, was darf gesendet werden, was braucht eine
Bestaetigung. Regel B: Felder mit nurLesendExtern (Fernzugang, Login, Ports, adb) sendet das Cockpit NIE,
auch wenn die Oberflaeche manipuliert wird; der Kern lehnt sie zusaetzlich je Feld ab.
Regel A: Diese Einstellungen loesen am Auto nichts aus - Befehle laufen ueber einen anderen Weg.
"""
import re

BEARBEITBAR = ("bool", "int", "zahl", "text", "auswahl", "zeit", "farbe", "geheim")   # liste/zeitfenster/geozone: nur anzeigen


def felder(schema):
    for g in (schema or {}).get("gruppen") or []:
        for f in g.get("felder") or []:
            if isinstance(f, dict) and f.get("key"):
                yield f


def wert(werte, key):
    return ((werte or {}).get("werte") or {}).get(key, {}).get("wert")


def sichtbar(feld, werte, faehigkeiten=None):
    """v1.1: Der Server liefert "sichtbar" je Feld fertig. Nur Abhaengigkeiten von einem anderen Feld (nurWenn key)
    rechnet das Cockpit selbst nach, damit sich die Anzeige beim Umschalten sofort aendert."""
    nw = feld.get("nurWenn")
    if "sichtbar" in feld and not (nw and "key" in nw):
        return bool(feld["sichtbar"])
    if not nw:
        return True
    if "faehigkeit" in nw:
        return bool((faehigkeiten or {}).get(nw["faehigkeit"]))
    if "key" in nw:
        return wert(werte, nw["key"]) == nw.get("gleich")
    return True


def bearbeitbar(feld):
    return feld.get("typ") in BEARBEITBAR and not feld.get("nurLesendExtern")


def _pruefe(feld, v):
    """None = ok, sonst Grund (gleiche Gruende wie der Kern)."""
    typ = feld.get("typ")
    if typ == "geheim":
        return None if v is None or isinstance(v, str) else "typ"
    if typ == "bool":
        return None if isinstance(v, bool) else "typ"
    if typ in ("int", "zahl"):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or (typ == "int" and int(v) != v):
            return "typ"
        if feld.get("min") is not None and v < feld["min"]:
            return "min %s" % feld["min"]
        if feld.get("max") is not None and v > feld["max"]:
            return "max %s" % feld["max"]
        return None
    if typ == "auswahl":
        erlaubt = [o.get("wert") for o in feld.get("optionen") or [] if not o.get("gesperrt")]
        return None if v in erlaubt else "option"
    if typ == "zeit":
        return None if isinstance(v, str) and re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v) else "typ"
    if typ == "farbe":
        return None if isinstance(v, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", v) else "typ"
    if typ == "text":
        return None if isinstance(v, str) and len(v) <= 500 else "typ"
    return "typ"


def vorbereiten(schema, werte, neu, bestaetigt=()):
    """Aenderungen aus der Oberflaeche -> (body fuer PUT, fehler je key). Nur geaenderte, erlaubte Felder.
    Felder mit `bestaetigung` werden nur gesendet, wenn sie in `bestaetigt` stehen."""
    nach_key = {f["key"]: f for f in felder(schema)}
    senden, fehler, best = {}, {}, []
    for key, v in (neu or {}).items():
        f = nach_key.get(key)
        if f is None:
            fehler[key] = "unbekannt"
            continue
        if f.get("nurLesendExtern"):
            fehler[key] = "nurLesendExtern"
            continue
        if not bearbeitbar(f):
            fehler[key] = "typ"
            continue
        if f.get("typ") != "geheim" and v == wert(werte, key):
            continue                                  # unveraendert -> nicht senden
        grund = _pruefe(f, v)
        if grund:
            fehler[key] = grund
            continue
        if f.get("bestaetigung"):
            if key not in (bestaetigt or ()):
                fehler[key] = "bestaetigungFehlt"
                continue
            best.append(key)
        senden[key] = v
    body = {"etag": (werte or {}).get("etag"), "werte": senden}
    if best:
        body["bestaetigt"] = best
    return body, fehler
