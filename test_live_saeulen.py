"""Tests der Live-Belegung (Vertrag chargers-live v2, kein Netz)."""
import unittest

import live_saeulen as ls

ANTWORT = {"live_quellen": [{"land": "AT", "quelle": "E-Control (AT)", "lizenz": "x", "url": "https://e-control.at"}],
           "stationen": [
    {"name": "Frei DC", "lat": 47.80, "lon": 13.04, "kw": 150, "ladepunkte": 4, "frei": 2, "belegt_n": 2,
     "status_bekannt": True, "entfernung_km": 1.0, "live_quelle": "E-Control (AT)", "live_alter_s": 60},
    {"name": "Voll", "lat": 47.81, "lon": 13.05, "kw": 22, "ladepunkte": 2, "frei": 0, "belegt_n": 2,
     "status_bekannt": True, "entfernung_km": 2.0, "live_alter_s": 600},
    {"name": "Kaputt", "lat": 47.82, "lon": 13.06, "kw": 11, "ladepunkte": 1, "frei": 0, "belegt_n": 0,
     "defekt_n": 1, "status_bekannt": True, "entfernung_km": 2.4},
    {"name": "Ohne Status", "lat": 47.80, "lon": 13.05, "kw": 50, "ladepunkte": 2, "frei": 0,
     "status_bekannt": False, "entfernung_km": 6.0},
    {"name": "Ausserhalb", "lat": 48.2, "lon": 13.5, "kw": 22, "frei": 1, "status_bekannt": True, "entfernung_km": 30},
]}


class TestKarte(unittest.TestCase):
    def test_zustaende_v2(self):
        d = ls.fuer_karte(ANTWORT)
        p = {f["properties"]["name"]: f["properties"] for f in d["features"]}
        self.assertEqual(set(p), {"Frei DC", "Voll", "Kaputt", "Ohne Status"})     # alle im Radius, auch unbekannt
        self.assertEqual((p["Frei DC"]["zustand"], p["Frei DC"]["dc"]), ("frei", 1))
        self.assertEqual(p["Frei DC"]["lbl"], "2/4 frei · 150 kW")
        self.assertEqual(p["Frei DC"]["quelle"], "E-Control (AT)")
        self.assertEqual(p["Voll"]["zustand"], "belegt")
        self.assertEqual(p["Voll"]["lbl"], "0/2 frei · 22 kW · Stand vor 10 min")   # aelter als 5 min
        self.assertEqual((p["Kaputt"]["zustand"], p["Kaputt"]["lbl"]), ("aus", "außer Betrieb"))
        self.assertEqual((p["Ohne Status"]["zustand"], p["Ohne Status"]["dc"]), ("unbekannt", 1))
        self.assertEqual(p["Ohne Status"]["lbl"], "Status unbekannt · 50 kW")
        self.assertEqual(d["quellen"], [{"land": "AT", "quelle": "E-Control (AT)", "lizenz": "x", "url": "https://e-control.at"}])

    def test_alter_in_stunden_und_lizenz_de(self):
        st = dict(ANTWORT["stationen"][1], live_alter_s=4 * 3600)
        d = ls.fuer_karte({"stationen": [st], "live_quellen": [
            {"land": "DE", "quelle": "MobiData BW", "lizenz": "je Quelle: CC BY 4.0 (EnBW AG), CC0", "url": "https://mobidata-bw.de"}]})
        self.assertTrue(d["features"][0]["properties"]["lbl"].endswith("· Stand vor 4 h"))
        self.assertIn("CC BY 4.0 (EnBW AG)", d["quellen"][0]["lizenz"])        # Pflicht-Namensnennung

    def test_osm_maske_je_station_120m(self):
        d = ls.fuer_karte(ANTWORT)
        m = d["osm_maske"]
        self.assertEqual(m["type"], "MultiPolygon")
        self.assertEqual(len(m["coordinates"]), 4)
        ring = m["coordinates"][0][0]
        self.assertEqual(len(ring), 9)
        self.assertAlmostEqual(ring[0][0], ring[-1][0], places=6)     # Ring geschlossen
        self.assertAlmostEqual(ring[0][1], ring[-1][1], places=6)
        # Ostpunkt ~120 m oestlich, Nordpunkt ~120 m noerdlich der Station (47.80, 13.04)
        self.assertAlmostEqual((ring[0][0] - 13.04) * 111.32 * 0.6717, 0.12, places=2)
        self.assertAlmostEqual((ring[2][1] - 47.80) * 111.32, 0.12, places=2)

    def test_kein_live(self):
        self.assertEqual(ls.fuer_karte({"stationen": []}), {"features": [], "osm_maske": None, "quellen": []})

    def test_raster(self):
        self.assertEqual(ls.runde(47.8123, 13.0471), (47.8, 13.05))


class TestKarten(unittest.TestCase):
    def test_preis_eigene_karte(self):
        st = dict(ANTWORT["stationen"][0], preis_meine={"tarif_id": 4, "karte": "Fastned Gold", "preis_kwh": 0.395},
                  karte_hinweis="Preis deiner Karte für diesen Betreiber (laut Preisblatt)")
        p = ls.fuer_karte({"stationen": [st]})["features"][0]["properties"]
        self.assertEqual(p["preis"], "Fastned Gold: 0,40 €/kWh")
        self.assertIn("Preisblatt", p["hinweis"])
        self.assertNotIn("preis", ls.fuer_karte(ANTWORT)["features"][0]["properties"])

    def test_karten_ids_gehen_mit_und_eigener_zwischenspeicher(self):
        calls = []
        live = ls.Live(post=lambda d: calls.append(d) or ANTWORT, uhr=lambda: 0.0)
        live.abfrage(47.8, 13.05)
        live.abfrage(47.8, 13.05, karten=[7, 4])
        live.abfrage(47.8, 13.05, karten=[4, 7])           # gleiche Karten -> aus dem Zwischenspeicher
        self.assertEqual(len(calls), 2)
        self.assertNotIn("karten", calls[0])
        self.assertEqual(calls[1]["karten"], [4, 7])


class TestTakt(unittest.TestCase):
    def test_je_zelle_hoechstens_alle_2_min(self):
        calls, t = [], [0.0]
        live = ls.Live(post=lambda d: calls.append(d) or ANTWORT, uhr=lambda: t[0])
        live.abfrage(47.8123, 13.0471)
        live.abfrage(47.8001, 13.0502)            # gleiche Zelle
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], {"lat": 47.8, "lon": 13.05, "radius": 12, "kwh": 20, "limit": 200})
        t[0] += ls.TAKT_S
        live.abfrage(47.8123, 13.0471)
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
