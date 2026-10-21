"""Ladenachfrage „Wo hast du geladen?“ (Panoptes >= 0.1.10, LADENACHFRAGE_VERTRAG Abschnitt GEBAUT).

Das Auto ist die Quelle: Das Cockpit liest die offenen Ladungen ueber die Kopplung und beantwortet sie dort.
Hier wird nichts gespeichert und nichts selbst gerechnet. Ueber die Kopplung kommen keine Koordinaten.
"""
import math
import urllib.error

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
