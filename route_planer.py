"""Route im Cockpit (1.10): der Routenplaner (byd.serveone.at/ev/api) ueber den Geraete-Schluessel des Cockpits.

Regel 2: Start und Ziel verlassen den Rechner NUR bei "Route berechnen" (das ist die Anfrage selbst) und bei
"Ins Auto schicken" - kein Dauerversand, nichts im Hintergrund. Koordinaten nur im POST-Body, nie in URL oder Log.
Der Schluessel bleibt im Cockpit-Prozess; der Browser sieht ihn nie.
"""
import socket
import urllib.error

import planer_bridge as pb

MODI = ("kompromiss", "billig", "schnell")


def _punkt(p):
    """[lat, lon] pruefen -> (lat, lon) oder ValueError."""
    try:
        lat, lon = float(p[0]), float(p[1])
    except (TypeError, ValueError, IndexError, KeyError):
        raise ValueError("Ort fehlt")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
        raise ValueError("Ort ungültig")
    return round(lat, 6), round(lon, 6)


def _zahl(v, std, lo, hi):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return std
    return max(lo, min(hi, v))


def anfrage_body(w, auto_pos, auto_soc, fahrzeug, auto_kennung=""):
    """Body fuer POST plan aus dem, was der Nutzer im Reiter gewaehlt hat.
    Start = Autoposition, solange der Nutzer keinen anderen Start angibt."""
    start = _punkt(w["start"]) if w.get("start") else (_punkt(auto_pos) if auto_pos else None)
    if start is None:
        raise ValueError("Autoposition gerade nicht verfügbar – Start eingeben")
    ziel = _punkt(w.get("ziel"))
    if not fahrzeug:
        raise ValueError("Kein Fahrzeugprofil im Planer gefunden – bitte in den Einstellungen wählen")
    soc = w.get("soc_start")
    b = {"start": list(start), "ziel": list(ziel), "fahrzeug": fahrzeug,
         "soc_start": _zahl(soc if soc not in (None, "") else auto_soc, 80, 1, 100),
         "soc_ziel_min": _zahl(w.get("soc_ziel_min"), 15, 0, 80),
         "modus": w.get("modus") if w.get("modus") in MODI else "kompromiss"}
    if auto_kennung:
        b["auto"] = auto_kennung
    return b


def _oeffnung(s):
    """Oeffnungszeit eines Stopps als Text; ohne Angabe ehrlich 'unbekannt'. Vertrag §10: oeffnung_text je Stopp."""
    if isinstance(s.get("oeffnung_text"), str) and s["oeffnung_text"].strip():
        return s["oeffnung_text"].strip()[:60]
    o = s.get("offen") or (s.get("saeule") or {}).get("offen")
    if isinstance(o, dict):
        if o.get("rund_um_die_uhr") or o.get("immer"):
            return "rund um die Uhr geöffnet"
        if o.get("bei_ankunft") is False or o.get("jetzt_bei_ankunft") is False:
            return "bei Ankunft geschlossen"
        if o.get("bis"):
            return "offen bis " + str(o["bis"])[:5]
    elif isinstance(o, str) and o.strip():
        return o.strip()[:60]
    return "Öffnungszeit unbekannt"


def kurz(d):
    """Planer-Antwort -> was der Reiter zeigt (keine Rohdaten, nichts Unnoetiges)."""
    if d.get("fehler"):
        raise ValueError(str(d["fehler"])[:160])
    r = d.get("route") or {}
    stopps = []
    for s in d.get("stopps") or []:
        sa = s.get("saeule") or {}
        stopps.append({"name": sa.get("name") or sa.get("betreiber") or "Ladestopp",
                       "betreiber": sa.get("betreiber") or sa.get("cpo") or "",
                       "lat": sa.get("lat"), "lon": sa.get("lon"), "kw": sa.get("kw"),
                       "km": sa.get("km_auf_route"), "soc_an": s.get("soc_vorher"), "soc_ab": s.get("soc_nachher"),
                       "dauer_min": s.get("ladedauer_min"), "kwh": s.get("kwh"),
                       "preis": s.get("kosten_beste_option"), "eigene_karte": bool(s.get("mit_eigener_karte")),
                       "oeffnung": _oeffnung(s), "geschlossen": s.get("geoeffnet_bei_ankunft") is False,
                       "bevorzugt": bool(s.get("bevorzugtes_netz"))})
    kosten = ((d.get("kosten") or {}).get("basis") or {}).get("gesamt")
    return {"km": r.get("km"), "minuten": r.get("minuten"), "geometrie": r.get("geometrie") or [],
            "soc_start": d.get("soc_start"), "soc_ankunft": d.get("soc_ankunft"), "stopps": stopps,
            "lade_min": round(sum(float(x["dauer_min"] or 0) for x in stopps)),
            "kosten": kosten, "fahrzeug": (d.get("fahrzeug") or {}).get("name") or "",
            "modus": d.get("modus") or "", "warnungen": [str(w)[:200] for w in (d.get("warnungen") or [])][:6],
            "vorlieben": _vorlieben(d.get("filter") or {}),
            "meine_karten": d.get("meine_karten") or None}


def _vorlieben(f):
    """Tatsaechlich angewandte Ladenetz-Vorlieben aus plan.filter (Vertrag §10); nichts gesetzt -> None."""
    netze = [str(x)[:60] for x in (f.get("bevorzugt") or [])][:20]
    if not netze and not f.get("nur_offen"):
        return None
    return {"netze": netze, "modus": "nur" if f.get("netze_modus") == "nur" else "bevorzugen",
            "umweg_min": f.get("umweg_max_min") or 0, "nur_offen": bool(f.get("nur_offen"))}


def fuer_auto(k, start, ziel, start_name, ziel_name, fahrzeug=""):
    """Gekuerzte Route -> flache Form fuer POST an-auto (Vertrag autopost.bereinigen)."""
    geo = [[round(float(p[0]), 6), round(float(p[1]), 6)] for p in (k.get("geometrie") or [])]
    if len(geo) < 2:
        raise ValueError("Keine Strecke zum Senden")
    stopps = [{"lat": s["lat"], "lon": s["lon"], "name": s["name"], "km": s["km"], "kw": s["kw"], "cpo": s["betreiber"],
               "soc_an": s["soc_an"], "soc_ab": s["soc_ab"], "dauer_min": s["dauer_min"], "kwh": s["kwh"],
               **({"preis": s["preis"]} if s.get("preis") is not None else {})}
              for s in (k.get("stopps") or [])][:20]
    return {"geometrie": geo, "stopps": stopps,
            "start": {"lat": start[0], "lon": start[1], "name": (start_name or "Start")[:80]},
            "ziel": {"lat": ziel[0], "lon": ziel[1], "name": (ziel_name or "Ziel")[:80]},
            "km": k.get("km"), "minuten": k.get("minuten"), "soc_start": k.get("soc_start"),
            "soc_ankunft": k.get("soc_ankunft"), "titel": ((start_name or "Start") + " → " + (ziel_name or "Ziel"))[:120],
            "fahrzeug": fahrzeug}


PLAN_TIMEOUT = 90          # der Browser bricht nach 100 s ab; der Server muss vorher mit Klartext antworten


def grund(e):
    """Fehlertext aus dem echten Grund (Timeout ist nicht 503 ist nicht 'kein Netz')."""
    import ssl
    r = getattr(e, "reason", None)
    if isinstance(e, (socket.timeout, TimeoutError)) or isinstance(r, (socket.timeout, TimeoutError)):
        return "Routenplaner antwortet gerade zu langsam"
    if isinstance(e, urllib.error.HTTPError) or isinstance(e, RuntimeError) and "antwortet" in str(e):
        code = getattr(e, "code", None) or "".join(ch for ch in str(e) if ch.isdigit())[:3]
        return "Routenplaner antwortet mit Fehler %s" % code if str(code) not in ("502", "503", "504") \
            else "Routenplaner startet gerade neu oder ist ausgelastet"
    if isinstance(r, ssl.SSLError) or isinstance(e, ssl.SSLError):
        return "Verbindung zum Routenplaner unsicher (Zertifikat) – abgebrochen"
    if isinstance(e, (urllib.error.URLError, ConnectionError, OSError)):
        return "Keine Verbindung zum Routenplaner – Internet prüfen"
    return "Routenplaner-Fehler (%s)" % type(e).__name__


def planen(token, body, anfrage=pb._anfrage, warte=None):
    try:
        code, d = anfrage("plan", token, body, timeout=PLAN_TIMEOUT)
        if code in (502, 503, 504):              # Planer startet sanft neu (~1 s Luecke): einmal nach 2 s wiederholen
            (warte or __import__("time").sleep)(2)
            code, d = anfrage("plan", token, body, timeout=PLAN_TIMEOUT)
    except (socket.timeout, TimeoutError):
        raise ValueError("Der Routenplaner hat nach %d s nicht geantwortet – bitte gleich noch einmal versuchen" % PLAN_TIMEOUT)
    except urllib.error.URLError as e:
        if isinstance(getattr(e, "reason", None), (socket.timeout, TimeoutError)):
            raise ValueError("Der Routenplaner hat nach %d s nicht geantwortet – bitte gleich noch einmal versuchen" % PLAN_TIMEOUT)
        raise ValueError("Routenplaner nicht erreichbar – Internetverbindung prüfen")
    if code == 429:
        raise ValueError("Zu viele Anfragen – bitte eine Minute warten")
    if code in (502, 503, 504):
        raise ValueError("Der Routenplaner wird gerade neu gestartet oder ist ausgelastet (HTTP %d) – bitte in einer Minute erneut" % code)
    if code != 200:
        raise ValueError((d or {}).get("fehler") or "Planer antwortet %s" % code)
    return kurz(d)


def orte(token, q, anfrage=pb._anfrage):
    q = (q or "").strip()[:120]
    if len(q) < 3:
        return []
    pfad, body = ("ziel-aus-text", {"text": q}) if ("http" in q or "," in q and any(c.isdigit() for c in q)) \
        else ("orte", {"q": q, "limit": 6})
    code, d = anfrage(pfad, token, body)
    if pfad == "ziel-aus-text":
        o = (d or {}).get("ort") if code == 200 else None
        if o:
            return [{"name": o.get("name") or q, "lat": o.get("lat"), "lon": o.get("lon")}]
        code, d = anfrage("orte", token, {"q": q, "limit": 6})
    if code != 200:
        raise ValueError("Ortssuche antwortet %s" % code)
    return [{"name": o.get("name") or o.get("kurz"), "lat": o.get("lat"), "lon": o.get("lon")}
            for o in (d.get("orte") or []) if o.get("lat") is not None][:6]


def an_auto(token, plan, auto="", anfrage=pb._anfrage):
    body = {"plan": plan}
    if auto:
        body["auto"] = auto
    code, d = anfrage("an-auto", token, body)
    if code != 200 or not (d or {}).get("ok"):
        raise ValueError((d or {}).get("fehler") or "Planer antwortet %s" % code)
    return d
