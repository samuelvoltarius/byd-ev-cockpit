"""Waechter-Aufnahmen aus Panoptes (ab 0.1.9, Kopplungs-Token nur lesend).

Freigegeben (Kern 3, kern-0190-cleanroom ae1ac1e): GET /api/recordings, /api/recordings/dates, /api/recordings/stats,
/video/id/<32 hex>, /thumb/id/<32 hex>. Alles andere (loeschen, behalten, Live, Stream, Snapshot) bleibt 403.

Grundsaetze: Liste und Vorschaubilder nur, wenn der Nutzer den Bereich oeffnet; ein Clip nur auf Klick; kein Live-Bild,
kein Vorabladen, nichts auf Platte. Bei available:false (Datentraeger fehlt) wird nichts abgerufen.
"""
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


def liste(pv, seite=1, datum="", art=""):
    """Eine Seite der Aufnahmen. -> {ok, aufnahmen, seiten, seite, gesamt} | {ok:False, grund}"""
    q = {"page": max(1, int(seite or 1)), "pageSize": SEITE}
    if datum and DATUM.fullmatch(datum):
        q["date"] = datum
    if art in ARTEN:
        q["type"] = art
    try:
        d = pv._get("/api/recordings?" + urllib.parse.urlencode(q))
    except urllib.error.HTTPError as e:
        return {"ok": False, "grund": "zu_alt" if e.code in (403, 404) else "fehler"}
    if d.get("_status") == 403 or (d.get("success") is False and not d.get("recordings")):
        return {"ok": False, "grund": "zu_alt"}       # Panoptes vor 0.1.9: Kopplung darf Aufnahmen nicht lesen
    if d.get("warming"):
        return {"ok": True, "aufnahmen": [], "warming": True, "progress": d.get("progress"), "seiten": 0, "seite": 1}
    auf = [x for x in (_knapp(a) for a in (d.get("recordings") or []) if isinstance(a, dict)) if x]
    return {"ok": True, "aufnahmen": auf, "seiten": int(d.get("totalPages") or 1), "seite": int(d.get("page") or 1),
            "gesamt": int(d.get("totalCount") or len(auf))}


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


def oeffnen(pv, art, rid, bereich=""):
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
        return _auf()
    except urllib.error.HTTPError as e:
        if e.code != 401:
            raise
        pv._anmelden()                                   # Token abgelaufen: einmal neu
        return _auf()
