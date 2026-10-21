"""Tests des lokalen Durchreichers fuer die Live-Belegung (kein Netz).
Die Auswertung selbst testet das gemeinsame Modul panoptes-karte (Karten-Sitzung, node --test)."""
import unittest

import live_saeulen as ls

ANTWORT = {"stationen": [{"id": 1, "lat": 47.8, "lon": 13.04}], "live_quellen": [{"land": "DE", "quelle": "EnBW AG",
                                                                                  "lizenz": "CC BY 4.0"}]}


class TestAnfrage(unittest.TestCase):
    def test_bereinigt_und_gerundet(self):
        f = ls.anfrage({"lat": 47.81234, "lon": 13.04711, "radius": 50, "limit": 9999, "boese": "x"}, karten=[7, 4])
        self.assertEqual(f, {"lat": 47.8, "lon": 13.05, "radius": 12, "kwh": 20, "limit": 200, "karten": [4, 7]})
        self.assertEqual(ls.anfrage({"lat": 47.8, "lon": 13.0, "radius": "x"})["radius"], 8.0)
        self.assertNotIn("karten", ls.anfrage({"lat": 47.8, "lon": 13.0}))

    def test_raster(self):
        self.assertEqual(ls.runde(47.8123, 13.0471), (47.8, 13.05))


class TestTakt(unittest.TestCase):
    def test_antwort_unveraendert_und_zwischengespeichert(self):
        calls, t = [], [0.0]
        live = ls.Live(post=lambda d: calls.append(d) or ANTWORT, uhr=lambda: t[0])
        self.assertIs(live.abfrage({"lat": 47.8123, "lon": 13.0471, "radius": 8}), ANTWORT)
        live.abfrage({"lat": 47.8001, "lon": 13.0502, "radius": 8})          # gleiche Zelle
        self.assertEqual(len(calls), 1)
        live.abfrage({"lat": 47.8, "lon": 13.05, "radius": 8}, karten=[2])  # andere Karten -> neu
        self.assertEqual(len(calls), 2)
        t[0] += ls.TAKT_S
        live.abfrage({"lat": 47.8123, "lon": 13.0471, "radius": 8})
        self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
