"""Waechter-Aufnahmen aus Panoptes (ab 0.1.9, Kopplungs-Token nur lesend).

Freigegeben (Kern 3, kern-0190-cleanroom ae1ac1e): GET /api/recordings, /api/recordings/dates, /api/recordings/stats,
/video/id/<32 hex>, /thumb/id/<32 hex>. Alles andere (loeschen, behalten, Live, Stream, Snapshot) bleibt 403.

Grundsaetze: Liste und Vorschaubilder nur, wenn der Nutzer den Bereich oeffnet; ein Clip nur auf Klick; kein Live-Bild,
kein Vorabladen, nichts auf Platte. Bei available:false (Datentraeger fehlt) wird nichts abgerufen.
"""
import json
import re
import urllib.error
import urllib.parse
import urllib.request


ID = re.compile(r"[0-9a-f]{32}")
DATUM = re.compile(r"\d{4}-\d{2}-\d{2}")
ARTEN = ("normal", "sentry", "proximity", "replay", "oemDashcam")
SEITE = 24
FELDER = ("id", "type", "timestamp", "date", "time", "dateFormatted", "timeFormatted", "sizeFormatted", "available",
          "peakSeverity", "peakProximity", "personCount", "vehicleCount", "bikeCount", "animalCount", "actors",
          "place", "cameraId", "cameras", "bucketLabel")


def _knapp(a):
    d = {k: a.get(k) for k in FELDER if k in a}
    d["available"] = a.get("available") is not False
    if not ID.fullmatch(str(d.get("id") or "")):
        return None                                  # ohne gueltige ID kein Clip/Bild -> gar nicht zeigen
    return d


def kamera_recht_fehlt(d):
    """Ab Panoptes 0.1.30: 403 {"grund":"nicht_erlaubt","recht":"kamera","text":...} -> {"grund":"kamera_recht","text"} | None."""
    if isinstance(d, dict) and d.get("grund") == "nicht_erlaubt" and d.get("recht") == "kamera":
        t = str(d.get("text") or "Kamera-Recht fehlt – in Panoptes unter Gekoppelte Geräte einschalten.")[:200]
        return {"grund": "kamera_recht", "text": t}
    return None


def liste(pv, seite=1, datum="", art="", groesse=SEITE):
    """Eine Seite der Aufnahmen. -> {ok, aufnahmen, seiten, seite, gesamt} | {ok:False, grund}"""
    q = {"page": max(1, int(seite or 1)), "pageSize": max(1, min(SEITE, int(groesse)))}
    if datum and DATUM.fullmatch(datum):
        q["date"] = datum
    if art in ARTEN:
        q["type"] = art
    try:
        d = pv._get("/api/recordings?" + urllib.parse.urlencode(q))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            try:
                k = kamera_recht_fehlt(json.loads(e.read().decode("utf-8") or "{}"))
            except Exception:
                k = None
            if k:
                return dict(k, ok=False)
        return {"ok": False, "grund": "zu_alt" if e.code in (403, 404) else "fehler"}
    k = kamera_recht_fehlt(d)
    if k:
        return dict(k, ok=False)
    if d.get("_status") == 403 or (d.get("success") is False and not d.get("recordings")):
        return {"ok": False, "grund": "zu_alt"}       # Panoptes vor 0.1.9: Kopplung darf Aufnahmen nicht lesen
    if d.get("warming"):
        return {"ok": True, "aufnahmen": [], "warming": True, "progress": d.get("progress"), "seiten": 0, "seite": 1}
    auf = [x for x in (_knapp(a) for a in (d.get("recordings") or []) if isinstance(a, dict)) if x]
    return {"ok": True, "aufnahmen": auf, "seiten": int(d.get("totalPages") or 1), "seite": int(d.get("page") or 1),
            "gesamt": int(d.get("totalCount") or len(auf))}


EREIGNIS_ARTEN = ("sentry", "proximity")    # Waechter-Ereignisse; Fahrtkamera/Dashcam zaehlen nicht


def letztes(pv, liste_=None):
    """Neuestes Waechter-Ereignis (je Art die neueste, davon die juengste). -> dict | None; {'grund': 'zu_alt'} vor 0.1.9."""
    liste_ = liste_ or liste
    beste = None
    for art in EREIGNIS_ARTEN:
        d = liste_(pv, 1, "", art, 1)
        if not d.get("ok"):
            if d.get("grund") in ("zu_alt", "kamera_recht"):
                return {k: d[k] for k in ("grund", "text") if k in d}
            continue
        for a in d.get("aufnahmen") or []:
            if beste is None or (a.get("timestamp") or 0) > (beste.get("timestamp") or 0):
                beste = a
    return beste


def tage(pv):
    try:
        d = pv._get("/api/recordings/dates")
    except Exception:
        return []
    roh = d.get("dates") if isinstance(d, dict) else d
    out = []
    for x in roh or []:
        t = x.get("date") if isinstance(x, dict) else x
        if isinstance(t, str) and DATUM.fullmatch(t):
            out.append({"date": t, "anzahl": x.get("count") if isinstance(x, dict) else None})
    return out[:120]


def oeffnen(pv, art, rid, bereich="", warte=None):
    """Clip ('video') oder Vorschaubild ('thumb') als offene Antwort (der Aufrufer reicht sie durch und schliesst sie).
    Range wird weitergegeben, damit der Browser im Clip springen kann."""
    if art not in ("video", "thumb") or not ID.fullmatch(rid or ""):
        raise ValueError("ungültige Aufnahme")
    if not pv.jwt:
        pv._anmelden()

    def _auf():
        kopf = {"Authorization": "Bearer " + pv.jwt, "User-Agent": "ev-cockpit"}
        if bereich and re.fullmatch(r"bytes=\d*-\d*", bereich):
            kopf["Range"] = bereich
        return urllib.request.urlopen(urllib.request.Request(pv.url + "/%s/id/%s" % (art, rid), headers=kopf), timeout=20)
    try:
        r = _auf()
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        pv._anmelden()                                   # Token abgelaufen: einmal neu
        r = _auf()
    # Panoptes erzeugt ein Vorschaubild beim ersten Abruf und antwortet solange 202 (JSON) - kurz warten, neu fragen
    for _ in range(4):
        if art != "thumb" or r.status != 202:
            break
        r.close()
        (warte or __import__("time").sleep)(1.5)
        r = _auf()
    if art == "thumb" and r.status != 200:
        r.close()
        raise urllib.error.HTTPError(pv.url, 503, "Vorschau wird noch erstellt", {}, None)
    return r
