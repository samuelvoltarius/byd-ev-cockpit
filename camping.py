"""Camping-Modus im Cockpit (Panoptes >= 0.1.16.1, GET/POST /api/camping, Einstellungen camping.*).

Die App im Auto ist die Quelle und plant/regelt selbst. Das Cockpit zeigt an und stellt ein - es gibt hier KEINE eigene
Heizlogik und KEINEN BYD-Cloud-Befehl. Geschrieben wird nur ueber die gekoppelte Panoptes-API.
Ehrlich angezeigt: Heizweg 'probelauf' (Standard) heizt nichts; eine Innentemperatur gibt es am Surf nicht (kein Fuehler),
sie wird nie angezeigt. Aeltere Panoptes (403/404) -> alles ausgeblendet.
"""
import math
import urllib.error

import einstellungen as ew

# Nur diese Einstellungen stellt die Cockpit-Seite ein (alles Weitere bleibt in den Panoptes-Einstellungen).
# camping.heizweg gehoert BEWUSST nicht dazu: ob das Auto wirklich heizt (statt Probelauf), entscheidet Alfred in Panoptes selbst.
EINSTELLUNGEN = ("camping.waerme", "camping.socGrenze", "camping.weckzeit",
                 "camping.vorheizenMinuten", "camping.morgensHeizen", "camping.hoechstdauerStunden")
PHASEN = ("vorheizen", "pause", "heizen", "morgen", "gesperrt", "ende")
FEHLER_TEXT = {"nicht_gestartet": "Camping ist in Panoptes noch nicht bereit (gerade gestartet?). Bitte gleich noch einmal.",
               "nicht_geparkt": "Camping lässt sich nur im Stand starten (Gang P).",
               "fahrzustand_unbekannt": "Das Auto meldet gerade nicht, ob es steht. Bitte kurz warten und noch einmal.",
               "camping_aus": "Camping ist gar nicht an.", "art": "Unbekannte Rückmeldung",
               "an": "Ungültige Anfrage", "gesperrt_fahrt": "Während der Fahrt nicht möglich."}


def _zahl(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return None
    return int(x) if float(x).is_integer() else round(float(x), 2)


def _ms(x):
    v = _zahl(x)
    return int(v) if v and v > 10 ** 11 else None


def _txt(x, n=60):
    return str(x or "").replace("<", "").replace(">", "")[:n]


def lesen(pv):
    """GET /api/camping -> dict oder None (aelteres Panoptes: 403/404, oder kein Camping)."""
    try:
        d = pv._get("/api/camping")
    except urllib.error.HTTPError:
        return None
    if not isinstance(d, dict) or d.get("_status"):
        return None
    return d


def anzeige(d):
    """Was der Browser bekommt: nur bekannte Felder, Zahlen geprueft, keine Innentemperatur."""
    if not isinstance(d, dict):
        return None
    b = d.get("budget") if isinstance(d.get("budget"), dict) else None
    v = d.get("verbrauch") if isinstance(d.get("verbrauch"), dict) else {}
    t = d.get("tabelle") if isinstance(d.get("tabelle"), dict) else None
    g = d.get("geplant") if isinstance(d.get("geplant"), dict) else None
    out = {
        "aktiv": bool(d.get("aktiv")), "gestartet": d.get("gestartet") is not False,
        "trockenlauf": d.get("trockenlauf") is not False,                       # unbekannt = lieber 'heizt nicht' behaupten
        "heizweg": d.get("heizweg") if d.get("heizweg") in ("probelauf", "auto_an", "auto_an_und_cloud") else "probelauf",
        "fahrt": d.get("fahrt") if d.get("fahrt") in ("steht", "faehrt", "unbekannt") else "unbekannt",
        "phase": d.get("phase") if d.get("phase") in PHASEN else None,
        "seit": _ms(d.get("seit")), "soc": _zahl(d.get("soc")), "socGrenze": _zahl(d.get("socGrenze")),
        "v12": _zahl(d.get("v12")), "aussenC": _zahl(d.get("aussenC")),
        "waerme": _txt(d.get("waerme"), 12),
        "naechsterZyklusMs": _ms(d.get("naechsterZyklusMs")), "phaseEndeMs": _ms(d.get("phaseEndeMs")),
        "sperrGrund": _txt(d.get("sperrGrund"), 40) or None, "sitzheizung": bool(d.get("sitzheizung")),
        "fehler": _txt(d.get("fehler"), 80) or None,
        "budget": None if not b else {"intervallMin": _zahl(b.get("intervallMin")), "dauerMin": _zahl(b.get("dauerMin")),
                                      "gestreckt": bool(b.get("gestreckt")), "reichtBisMs": _ms(b.get("reichtBisMs")),
                                      "reichtBisWeck": b.get("reichtBisWeck") if isinstance(b.get("reichtBisWeck"), bool) else None},
        "tabelle": None if not t else {"stufe": _zahl(t.get("stufe")), "intervallMin": _zahl(t.get("intervallMin")),
                                       "dauerMin": _zahl(t.get("dauerMin"))},
        "verbrauch": {"gemessen": bool(v.get("gemessen")), "prozentProStunde": _zahl(v.get("prozentProStunde")),
                      "heizProzentProStunde": _zahl(v.get("heizProzentProStunde"))},
        "protokoll": [],
        # Planung (kommt mit Panoptes 0.1.17): nur wenn der Kern das Feld liefert, wird sie im Cockpit freigeschaltet
        "plan_moeglich": "geplant" in d,
        "geplant": None if not g else {"start": _ms(g.get("start")), "ende": _ms(g.get("ende")), "grund": _txt(g.get("grund"), 60) or None},
    }
    for e in (d.get("protokoll") or [])[-8:]:
        if isinstance(e, dict) and e.get("aktion") in ("ein", "aus"):
            out["protokoll"].append({"zeit": _ms(e.get("zeit")), "aktion": e["aktion"], "stufe": _zahl(e.get("stufe")),
                                     "geblaese": _zahl(e.get("geblaese")), "trockenlauf": e.get("trockenlauf") is not False,
                                     "ergebnis": _txt(e.get("ergebnis"), 60)})
    return out


def einstellungen(pv, sprache="de"):
    """Die sieben Camping-Einstellungen aus dem Schema des Autos (Typ, Grenzen, Optionen) mit dem aktuellen Wert."""
    stand = {"schema": pv._get("/api/einstellungen/schema?sprache=" + sprache), "werte": pv._get("/api/einstellungen")}
    nach_key = {f["key"]: f for f in ew.felder(stand["schema"])}
    liste = []
    for key in EINSTELLUNGEN:
        f = nach_key.get(key)
        if not f:
            continue
        w = ew.wert(stand["werte"], key)
        liste.append({"key": key, "typ": f.get("typ"), "min": _zahl(f.get("min")), "max": _zahl(f.get("max")), "schritt": _zahl(f.get("schritt")),
                      "einheit": _txt(f.get("einheit"), 6), "standard": f.get("standard"),
                      "wert": w if w is not None else f.get("standard"),
                      "optionen": [{"wert": _txt(o.get("wert"), 30), "titel": _txt(o.get("titel") or o.get("wert"), 60), "gesperrt": bool(o.get("gesperrt"))}
                                   for o in (f.get("optionen") or []) if isinstance(o, dict)],
                      "bearbeitbar": ew.bearbeitbar(f)})
    return liste, stand


def speichern(pv, neu, sprache="de"):
    """Nur Camping-Schluessel aus der Whitelist, geprueft wie im Kern; geschrieben ueber die Panoptes-Einstellungen."""
    from panoptes_source import einstellungen_schreiben
    nur = {k: v for k, v in (neu or {}).items() if k in EINSTELLUNGEN}
    if not nur:
        return {"ok": False, "fehler": {"_": "nichts_zu_speichern"}}
    liste, stand = einstellungen(pv, sprache)
    body, lokal = ew.vorbereiten(stand["schema"], stand["werte"], nur, ())
    if lokal:
        return {"ok": False, "fehler": dict(lokal)}
    if not body["werte"]:
        return {"ok": True, "gespeichert": {}}
    r = einstellungen_schreiben(pv, body)
    if r.get("_status") == 409:
        return {"ok": False, "grund": "veraltet"}
    return {"ok": bool(r.get("ok")), "gespeichert": r.get("gespeichert") or {}, "fehler": r.get("fehler") or {}}


def senden(pv, pfad, daten):
    """POST an /api/camping[/...]; HTTP-Fehler -> Antwort mit _status (409 = Kern lehnt ab, mit 'fehler')."""
    d = pv.senden(pfad, daten)
    ok = isinstance(d, dict) and d.get("ok") is not False and not d.get("_status")
    grund = d.get("fehler") if isinstance(d, dict) else None
    return {"ok": ok, "fehler": str(grund)[:40] if grund else None,
            "text": None if ok else FEHLER_TEXT.get(str(grund), "Panoptes hat das abgelehnt" + (" (%s)" % _txt(grund, 30) if grund else ""))}


def an_aus(pv, an):
    return senden(pv, "/api/camping", {"an": bool(an)})


def rueckmeldung(pv, art):
    if art not in ("zu_kalt", "passt", "zu_warm"):
        return {"ok": False, "fehler": "art", "text": FEHLER_TEXT["art"]}
    r = senden(pv, "/api/camping/rueckmeldung", {"art": art})
    return r


def weiter(pv):
    return senden(pv, "/api/camping/weiter", {})


def plan_senden(pv, start, ende):
    """VORBEREITET (Panoptes 0.1.17): POST /api/camping/plan {start, ende} - Feldnamen erst nach Zusage des Kerns festgeschrieben."""
    return senden(pv, "/api/camping/plan", {"start": start, "ende": ende})


def plan_loeschen(pv):
    return senden(pv, "/api/camping/plan", {"loeschen": True})
