"""Live-Belegung der Ladesaeulen fuer die Karte (Ebene `chargers-live`).

Vertrag v2 (21.10.2026, Planer + Karten-Sitzung, gilt fuer /ev/, EV-Cockpit und Panoptes;
F:/surfmate/deploy/server/tiles/README.md "Vertrag Live-Belegung"):
  - `POST /ev/api/umkreis` mit auf 0,05 Grad gerundetem Mittelpunkt, radius <= 12, limit 200,
    beim Rasterwechsel und alle 2 min. POST, damit keine Koordinaten in einem Zugriffslog landen.
  - ALLE Stationen im Radius kommen in die Ebene: frei / belegt (rot) / ausser Betrieb (grau) /
    Status unbekannt (grau mit "?"). DC-Symbol ab 50 kW.
  - OSM-Ebene `chargers` je Station ausblenden: 8-Eck mit 120 m um jede Station der Ebene, damit nie
    eine OSM-Saeule ohne Ersatz verschwindet (auch an Grenzen).
  - Quellenangabe aus `live_quellen`; ist der Status aelter als 5 min: "Stand vor x min".
"""
import json
import math
import time
import urllib.request

URL = "https://byd.serveone.at/ev/api/umkreis"
RASTER = 0.05
RADIUS_KM = 12
TAKT_S = 120
MASKE_KM = 0.12
ALT_S = 300


def runde(lat, lon):
    """Mittelpunkt aufs Raster (~5 km) - genauer muss der Server es nicht wissen."""
    r = lambda x: round(round(float(x) / RASTER) * RASTER, 2)
    return r(lat), r(lon)


def zustand(st):
    if not st.get("status_bekannt"):
        return "unbekannt"
    if (st.get("frei") or 0) > 0:
        return "frei"
    belegt = st.get("belegt_n")
    return "belegt" if belegt is None or belegt > 0 else "aus"


def _achteck(lon, lat, km=MASKE_KM):
    ring = []
    for i in range(9):
        w = i / 8.0 * 2 * math.pi
        ring.append([round(lon + km / (111.32 * math.cos(math.radians(lat))) * math.cos(w), 6),
                     round(lat + km / 111.32 * math.sin(w), 6)])
    return [ring]


def fuer_karte(antwort):
    """Planer-Antwort -> {"features", "osm_maske" (MultiPolygon oder None), "quellen"} fuer die Kartenebene."""
    feats = []
    for st in antwort.get("stationen") or []:
        if st.get("lat") is None or st.get("lon") is None:
            continue
        if st.get("entfernung_km") is not None and st["entfernung_km"] > RADIUS_KM:
            continue
        z, kw = zustand(st), st.get("kw") or 0
        kw_txt = (" · %g kW" % kw) if kw else ""
        if z == "aus":
            lbl = "außer Betrieb"
        elif z == "unbekannt":
            lbl = "Status unbekannt" + kw_txt
        else:
            lbl = "%s/%s frei%s" % (st.get("frei") or 0, st.get("ladepunkte") or "?", kw_txt)
        alter = st.get("live_alter_s")
        if z != "unbekannt" and isinstance(alter, (int, float)) and alter > ALT_S:
            lbl += " · Stand vor %d min" % round(alter / 60.0)
        props = {"dc": 1 if kw >= 50 else 0, "zustand": z, "kw": kw, "lbl": lbl,
                 "name": (st.get("name") or "")[:60], "quelle": st.get("live_quelle") or ""}
        pm = st.get("preis_meine")
        if isinstance(pm, dict) and pm.get("preis_kwh") is not None:      # Preis der eigenen Ladekarte
            props["preis"] = "%s: %s €/kWh" % (str(pm.get("karte") or "Deine Karte")[:40],
                                              ("%.2f" % float(pm["preis_kwh"])).replace(".", ","))
        if st.get("karte_hinweis"):
            props["hinweis"] = str(st["karte_hinweis"])[:120]
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [st["lon"], st["lat"]]},
                      "properties": props})
    maske = ({"type": "MultiPolygon",
              "coordinates": [_achteck(*f["geometry"]["coordinates"]) for f in feats]} if feats else None)
    quellen = [{"land": q.get("land"), "quelle": q.get("quelle"), "url": q.get("url")}
               for q in (antwort.get("live_quellen") or []) if isinstance(q, dict) and q.get("quelle")]
    return {"features": feats, "osm_maske": maske, "quellen": quellen}


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

    def abfrage(self, lat, lon, karten=()):
        la, lo = runde(lat, lon)
        karten = tuple(sorted(int(i) for i in karten or ()))
        k, jetzt = (la, lo, karten), self.uhr()
        if k in self.cache and jetzt - self.cache[k][0] < TAKT_S:
            return self.cache[k][1]
        frage = {"lat": la, "lon": lo, "radius": RADIUS_KM, "kwh": 20, "limit": 200}
        if karten:
            frage["karten"] = list(karten)     # nur Tarif-IDs, damit der Planer den Preis der eigenen Karte rechnet
        d = fuer_karte(self.post(frage))
        self.cache = {k: v for k, v in self.cache.items() if jetzt - v[0] < TAKT_S}
        self.cache[k] = (jetzt, d)
        return d
