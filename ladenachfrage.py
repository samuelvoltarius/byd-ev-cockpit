"""Ladenachfrage „Wo hast du geladen?“ (Panoptes >= 0.1.10, LADENACHFRAGE_VERTRAG Abschnitt GEBAUT).

Das Auto ist die Quelle: Das Cockpit liest die offenen Ladungen ueber die Kopplung und beantwortet sie dort.
Hier wird nichts gespeichert und nichts selbst gerechnet. Ueber die Kopplung kommen keine Koordinaten.
"""
import math
import time
import urllib.error
import urllib.parse

ARTEN = ("karte", "adhoc", "zuhause", "zuhause_gratis", "ortskreis")
PREIS_MAX = 5.0          # EUR je kWh: alles darueber ist ein Tippfehler (Panoptes prueft zusaetzlich PreisPlausibel)


def lesen(pv):
    """GET /api/laden/nachfrage. Aelteres Panoptes (404/403) oder Fehler -> None."""
    try:
        d = pv._get("/api/laden/nachfrage")
    except urllib.error.HTTPError:
        return None
    if not isinstance(d, dict) or d.get("_status") or d.get("ok") is False:
        return None
    return d


def _txt(x, n=80):
    return str(x or "").replace("<", "").replace(">", "")[:n]


def _preis(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def anzeige(d):
    """Was der Browser bekommt: offene Ladungen mit Auswahl, ohne Koordinaten, Texte gekuerzt."""
    if not isinstance(d, dict):
        return None
    offen = []
    for e in (d.get("offen") or [])[:20]:
        if not isinstance(e, dict) or not isinstance(e.get("id"), int):
            continue
        ort = e.get("ort") if isinstance(e.get("ort"), dict) else {}
        vor = []
        for v in (e.get("vorschlaege") or [])[:8]:
            if isinstance(v, dict) and v.get("art") in ("ortskreis", "planer_stopp"):
                vor.append({"art": v["art"], "name": _txt(v.get("name")), "tarifId": _txt(v.get("tarifId"), 40),
                            "preisKwh": _preis(v.get("preisKwh")), "gratis": bool(v.get("gratis"))})
        aus = []
        for a in (e.get("auswahl") or [])[:30]:
            if isinstance(a, dict) and a.get("art") in ARTEN:
                aus.append({"art": a["art"], "id": a.get("id") if isinstance(a.get("id"), int) else None,
                            "anzeige": _txt(a.get("anzeige")), "preisKwh": _preis(a.get("preisKwh")),
                            "vorgeschlagen": bool(a.get("vorgeschlagen"))})
        offen.append({"id": e["id"], "start": e.get("start") if isinstance(e.get("start"), int) else None,
                      "kwh": _preis(e.get("kwh")), "dc": e.get("dc") if isinstance(e.get("dc"), bool) else None,
                      "spaeter": bool(e.get("spaeter")), "ort": _txt(ort.get("name")) if ort.get("bekannt") else "",
                      "vorschlaege": vor, "auswahl": aus})
    return {"an": d.get("an") is not False, "anzahl": len(offen) if d.get("anzahl") is None else int(d.get("anzahl") or 0),
            "offen": offen}


def antwort_body(w):
    """Browser-Eingabe -> Body fuer POST /api/laden/nachfrage. Ungueltig -> ValueError mit Text fuer den Nutzer."""
    try:
        i = int(w.get("id"))
    except (TypeError, ValueError):
        i = 0
    if i <= 0:
        raise ValueError("Unbekannte Ladung")
    art = w.get("art")
    if art not in ARTEN:
        raise ValueError("Bitte wählen, wie bezahlt wurde")
    b = {"id": i, "art": art}
    if art != "zuhause_gratis":
        p = _preis(w.get("preisKwh"))
        if p is None or p > PREIS_MAX:
            raise ValueError("Bitte den Preis je kWh eintragen (0 = gratis)")
        b["preisKwh"] = round(p, 4)
    if art == "karte":
        try:
            b["karteId"] = int(w.get("karteId"))
        except (TypeError, ValueError):
            raise ValueError("Bitte die Ladekarte wählen")
    if art == "ortskreis":
        b["name"] = _txt(w.get("name"))
        if w.get("tarifId"):
            b["tarifId"] = _txt(w.get("tarifId"), 40)
    name = _txt(w.get("ort_merken"), 60).strip() if w.get("ort_merken") is not None else ""
    if name:
        b["ortMerken"] = {"name": name, "radiusM": 100}
    return b


def id_body(w):
    try:
        i = int(w.get("id"))
    except (TypeError, ValueError):
        i = 0
    if i <= 0:
        raise ValueError("Unbekannte Ladung")
    return {"id": i}


_GRUND = {400: "Panoptes hat die Angabe abgelehnt", 403: "Panoptes erlaubt das der Kopplung nicht (Panoptes zu alt?)",
          404: "Diese Ladung gibt es nicht mehr (schon beantwortet?)", 409: "Die Ladung läuft noch",
          503: "Die Ladedaten im Auto sind gerade nicht bereit"}
_HINWEIS = {"zu_niedrig": "Preis ungewöhnlich niedrig – bitte prüfen", "zu_hoch": "Preis ungewöhnlich hoch – bitte prüfen"}
_ORT = {"keine_position": "Ort nicht gemerkt: das Auto kennt die Position dieser Ladung nicht",
        "fehlgeschlagen": "Ort merken hat nicht geklappt"}


def ergebnis(d):
    """Antwort von Panoptes -> {ok, hinweis} bzw. {ok:False, error}."""
    if not isinstance(d, dict):
        return {"ok": False, "error": "Keine Antwort von Panoptes"}
    st = d.get("_status")
    if st or d.get("ok") is False:
        f = d.get("fehler")
        zusatz = (" (" + ", ".join(_txt(k, 30) for k in f) + ")") if isinstance(f, dict) and f else ""
        return {"ok": False, "error": _GRUND.get(st, "Panoptes hat die Angabe abgelehnt") + zusatz}
    h = []
    for e in (d.get("ergebnisse") or [])[:1]:
        if isinstance(e, dict) and e.get("hinweis") in _HINWEIS:
            h.append(_HINWEIS[e["hinweis"]])
    if d.get("ortMerken") in _ORT:
        h.append(_ORT[d["ortMerken"]])
    elif d.get("ortMerken"):
        h.append("Ort gemerkt")
    return {"ok": True, "hinweis": " · ".join(h)}


# ---------------------------------------------------------------- Kosten und Ladungen (Panoptes >= 0.1.10.1)
ZEITRAEUME = ("monat", "30t", "jahr", "gesamt")
QUELLEN = ("tarif", "nutzer", "standard", "ersatz", "fehlt", "overdrive")
_CACHE = {}              # (pfad) -> (zeit, antwort); nichts auf Platte
CACHE_S = 300
FEHLT_S = 3600           # aelteres Panoptes (404/403): hoechstens stuendlich neu fragen


def cache_leeren():
    """Nach einer Antwort auf die Nachfrage aendern sich Kosten und Ladungen."""
    for k in [k for k, v in _CACHE.items() if not v[1].get("fehlt")]:
        _CACHE.pop(k, None)


def _zahl(x):
    if isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _betrag(x):
    """rate/kosten: -1 = Preis fehlt -> None."""
    v = _zahl(x)
    return v if v is not None and v >= 0 else None


def _ganz(x):
    return int(x) if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) else None


def _holen(pv, pfad, uhr=time.time):
    t, d = _CACHE.get(pfad, (0.0, None))
    if d is not None and uhr() - t < (FEHLT_S if d.get("fehlt") else CACHE_S):
        return d
    try:
        d = pv._get(pfad)
    except urllib.error.HTTPError as e:
        d = {"_status": e.code}
    if not isinstance(d, dict):
        d = {"_status": 0}
    if d.get("_status") in (403, 404):
        d = {"ok": False, "fehlt": True}            # Panoptes vor 0.1.10.1: ausblenden
    elif d.get("_status") or d.get("ok") is False:
        return {"ok": False, "error": "Panoptes hat die Abfrage abgelehnt"}
    _CACHE[pfad] = (uhr(), d)
    return d


def kosten(pv, zeitraum, uhr=time.time):
    """GET /api/laden/kosten?zeitraum=... -> Zahlen fuer die Kachel. Gerechnet wird im Auto, hier nichts."""
    z = zeitraum if zeitraum in ZEITRAEUME else "monat"
    d = _holen(pv, "/api/laden/kosten?zeitraum=" + z, uhr)
    if not d.get("ok"):
        return {k: d[k] for k in ("ok", "fehlt", "error") if k in d}
    return {"ok": True, "zeitraum": z, "von": _ganz(d.get("von")), "bis": _ganz(d.get("bis")), "km": _zahl(d.get("km")),
            "kwh_geladen": _zahl(d.get("kwh_geladen")), "kosten_summe": _betrag(d.get("kosten_summe")),
            "kosten_je_100km": _betrag(d.get("kosten_je_100km")), "kwh_je_100km": _zahl(d.get("kwh_je_100km")),
            "ladungen": _ganz(d.get("ladungen")) or 0, "ladungen_ohne_preis": _ganz(d.get("ladungen_ohne_preis")) or 0,
            "gratis_ladungen": _ganz(d.get("gratis_ladungen")) or 0, "vollstaendig": d.get("vollstaendig") is not False,
            "waehrung": _txt(d.get("waehrung") or "EUR", 3)}


def ladungen(pv, seite=0, jetzt_ms=None, uhr=time.time):
    """GET /api/laden/ladungen (letzte 12 Monate, 50 je Seite) -> Liste ohne Koordinaten plus Monatssummen."""
    bis = int(jetzt_ms if jetzt_ms is not None else uhr() * 1000)
    bis -= bis % 3600000                           # stuendlich gleiche URL -> Cache greift
    von = bis - 366 * 86400000
    seite = max(0, min(int(seite or 0), 200))
    d = _holen(pv, "/api/laden/ladungen?" + urllib.parse.urlencode({"von": von, "bis": bis + 3600000, "seite": seite, "anzahl": 50}), uhr)
    if not d.get("ok"):
        return {k: d[k] for k in ("ok", "fehlt", "error") if k in d}
    li = []
    for e in (d.get("ladungen") or [])[:50]:
        if not isinstance(e, dict):
            continue
        q = e.get("quelle") if e.get("quelle") in QUELLEN else ""
        li.append({"id": _ganz(e.get("id")), "start": _ganz(e.get("start")), "ende": _ganz(e.get("ende")),
                   "dc": e.get("dc") if isinstance(e.get("dc"), bool) else None, "kwh": _zahl(e.get("kwh")),
                   "rate": _betrag(e.get("rate")), "kosten": _betrag(e.get("kosten")), "waehrung": _txt(e.get("waehrung") or "EUR", 3),
                   "quelle": q, "tarif": _txt(e.get("tarifName")), "ort": _txt(e.get("ort")) if isinstance(e.get("ort"), str) else ""})
    mo = []
    for m in (d.get("monate") or [])[:24]:
        if isinstance(m, dict) and isinstance(m.get("monat"), str):
            mo.append({"monat": _txt(m["monat"], 7), "ladungen": _ganz(m.get("ladungen")) or 0, "kwh": _zahl(m.get("kwh")),
                       "kosten": _betrag(m.get("kosten")), "ohne_preis": _ganz(m.get("ohne_preis")) or 0,
                       "vollstaendig": m.get("vollstaendig") is not False})
    return {"ok": True, "seite": seite, "mehr": bool(d.get("mehr")), "ladungen": li, "monate": mo}
