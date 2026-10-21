"""Live-Belegung der Ladesaeulen: lokaler Durchreicher fuer das gemeinsame Kartenmodul panoptes-karte.

Die Auswertung (Zustaende, DE-Gueltigkeit, 120-m-Maske, Beschriftung, Pflicht-Quellenangabe) macht das Modul
(static/panoptes-karte-1.0.0.js, Vertrag https://byd.serveone.at/tiles/lib/README.md). Dieser Teil sorgt nur dafuer,
dass die Anfrage vom eigenen Rechner aus sauber zum Planer geht:
  - POST, Mittelpunkt (nochmal) auf 0,05 Grad gerundet, radius <= 12, limit <= 200 - nie Koordinaten in der URL;
  - die eigenen Ladekarten (nur Tarif-IDs) werden angehaengt, damit preis_meine kommt;
  - je Rasterzelle hoechstens alle 2 min eine Anfrage.
Die Planer-Antwort geht unveraendert an die Seite zurueck.
"""
import json
import time
import urllib.request

URL = "https://byd.serveone.at/ev/api/umkreis"
RASTER = 0.05
RADIUS_KM = 12
TAKT_S = 120


def runde(lat, lon):
    """Mittelpunkt aufs Raster (~5 km) - genauer muss der Server es nicht wissen."""
    r = lambda x: round(round(float(x) / RASTER) * RASTER, 2)
    return r(lat), r(lon)


def anfrage(body, karten=()):
    """Seiten-Anfrage -> bereinigter Body fuer den Planer (nur diese Felder)."""
    la, lo = runde(body["lat"], body["lon"])
    try:
        radius = max(1.0, min(float(body.get("radius") or 8), RADIUS_KM))
    except (TypeError, ValueError):
        radius = 8.0
    frage = {"lat": la, "lon": lo, "radius": radius, "kwh": 20, "limit": 200}
    ids = sorted(int(i) for i in karten or ())
    if ids:
        frage["karten"] = ids
    return frage


def _post(daten, timeout=12):
    req = urllib.request.Request(URL, data=json.dumps(daten).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "ev-cockpit"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


class Live:
    """Je Anfrage (Zelle, Radius, Karten) hoechstens alle 2 min eine Abfrage beim Planer."""

    def __init__(self, post=_post, uhr=time.time):
        self.post, self.uhr = post, uhr
        self.cache = {}

    def abfrage(self, body, karten=()):
        frage = anfrage(body, karten)
        k, jetzt = json.dumps(frage, sort_keys=True), self.uhr()
        if k in self.cache and jetzt - self.cache[k][0] < TAKT_S:
            return self.cache[k][1]
        d = self.post(frage)
        self.cache = {x: v for x, v in self.cache.items() if jetzt - v[0] < TAKT_S}
        self.cache[k] = (jetzt, d)
        return d
