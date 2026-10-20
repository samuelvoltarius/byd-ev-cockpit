"""Tests der Live-Belegung (Vertrag chargers-live, kein Netz)."""
import unittest

import live_saeulen as ls

ANTWORT = {"live_abdeckung_km": 2.5, "stationen": [
    {"name": "Frei DC", "lat": 47.80, "lon": 13.04, "kw": 150, "ladepunkte": 4, "frei": 2, "belegt_n": 2,
     "status_bekannt": True, "entfernung_km": 1.0},
    {"name": "Voll", "lat": 47.81, "lon": 13.05, "kw": 22, "ladepunkte": 2, "frei": 0, "belegt_n": 2,
     "status_bekannt": True, "entfernung_km": 2.0},
    {"name": "Kaputt", "lat": 47.82, "lon": 13.06, "kw": 11, "ladepunkte": 1, "frei": 0, "belegt_n": 0,
     "defekt_n": 1, "status_bekannt": True, "entfernung_km": 2.4},
    {"name": "Zu weit", "lat": 47.9, "lon": 13.1, "kw": 50, "ladepunkte": 2, "frei": 1,
     "status_bekannt": True, "entfernung_km": 6.0},
    {"name": "Ohne Status", "lat": 47.80, "lon": 13.05, "kw": 50, "ladepunkte": 2, "frei": 0,
     "status_bekannt": False, "entfernung_km": 0.5},
]}


class TestKarte(unittest.TestCase):
    def test_filter_und_farben(self):
        d = ls.fuer_karte(ANTWORT)
        p = {f["properties"]["name"]: f["properties"] for f in d["features"]}
        self.assertEqual(set(p), {"Frei DC", "Voll", "Kaputt"})
        self.assertEqual((p["Frei DC"]["zustand"], p["Frei DC"]["dc"]), ("frei", 1))
        self.assertEqual(p["Voll"]["zustand"], "belegt")
        self.assertEqual(p["Kaputt"]["zustand"], "aus")
        self.assertEqual(p["Kaputt"]["lbl"], "außer Betrieb")
        self.assertEqual(p["Frei DC"]["lbl"], "2/4 frei · 150 kW")
        self.assertEqual(d["abdeckung_km"], 2.5)

    def test_kein_live(self):
        self.assertEqual(ls.fuer_karte({"live_abdeckung_km": 0, "stationen": []}),
                         {"abdeckung_km": 0, "features": []})

    def test_raster(self):
        self.assertEqual(ls.runde(47.8123, 13.0471), (47.8, 13.05))


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
