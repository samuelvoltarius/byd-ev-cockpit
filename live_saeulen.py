"""Live-Belegung der Ladesaeulen fuer die Karte (Ebene `chargers-live`).

Vertrag (21.10.2026, Planer + Karten-Sitzung, gilt fuer /ev/, EV-Cockpit und Panoptes):
  - `POST /ev/api/umkreis` mit auf 0,05 Grad gerundetem Mittelpunkt, radius <= 12, limit 200,
    beim Rasterwechsel und alle 2 min. POST, damit keine Koordinaten in einem Zugriffslog landen.
  - In die Ebene nur Stationen mit `status_bekannt` und `entfernung_km <= live_abdeckung_km`.
  - DC ab 50 kW. frei > 0 normal, frei 0 und belegt > 0 rot, frei 0 ohne belegt grau (ausser Betrieb).
Live gibt es derzeit nur in Oesterreich (E-Control).
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


def zustand(st):
    if (st.get("frei") or 0) > 0:
        return "frei"
    belegt = st.get("belegt_n")
    return "belegt" if belegt is None or belegt > 0 else "aus"


def fuer_karte(antwort):
    """Planer-Antwort -> {"abdeckung_km", "features"} fuer die Kartenebene."""
    abd = float(antwort.get("live_abdeckung_km") or 0)
    feats = []
    for st in antwort.get("stationen") or []:
        if not st.get("status_bekannt") or st.get("lat") is None or st.get("lon") is None:
            continue
        if st.get("entfernung_km") is not None and st["entfernung_km"] > abd:
            continue
        z, kw = zustand(st), st.get("kw") or 0
        lbl = "außer Betrieb" if z == "aus" else "%s/%s frei%s" % (
            st.get("frei") or 0, st.get("ladepunkte") or "?", (" · %g kW" % kw) if kw else "")
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [st["lon"], st["lat"]]},
                      "properties": {"dc": 1 if kw >= 50 else 0, "zustand": z, "kw": kw, "lbl": lbl,
                                     "name": (st.get("name") or "")[:60]}})
    return {"abdeckung_km": abd if feats else 0, "features": feats}


def _post(daten, timeout=12):
    req = urllib.request.Request(URL, data=json.dumps(daten).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "ev-cockpit"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8") or "{}")


class Live:
    """Je Rasterzelle hoechstens alle 2 min eine Abfrage beim Planer."""

    def __init__(self, post=_post, uhr=time.time):
        self.post, self.uhr = post, uhr
        self.cache = {}

    def abfrage(self, lat, lon):
        la, lo = runde(lat, lon)
        k, jetzt = (la, lo), self.uhr()
        if k in self.cache and jetzt - self.cache[k][0] < TAKT_S:
            return self.cache[k][1]
        d = fuer_karte(self.post({"lat": la, "lon": lo, "radius": RADIUS_KM, "kwh": 20, "limit": 200}))
        d["mitte"] = [la, lo]
        self.cache = {k: v for k, v in self.cache.items() if jetzt - v[0] < TAKT_S}
        self.cache[k] = (jetzt, d)
        return d
