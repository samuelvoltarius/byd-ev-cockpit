"""1.10.5: Fahrtenbuch aus Panoptes - keine Koordinaten, Monatsgrenzen, CSV, ehrlich vor 0.1.9."""
import datetime as dt
import unittest
import urllib.error

import fahrtenbuch as fb

T = {"id": 7, "startTime": 1792597329826, "endTime": 1792600865004, "distanceKm": 33.099998, "durationSeconds": 3535,
     "energyUsedKwh": 6.1000004, "tripCost": 0.0610000007, "currency": "€", "socStart": 85, "socEnd": 71, "extTempC": 14,
     "startLat": 48.2, "startLon": 16.3, "endLat": 47.8, "endLon": 13.0, "gradientProfile": [1, 2]}


class Pv:
    def __init__(self, antwort):
        self.antwort, self.pfade = antwort, []

    def _get(self, pfad):
        self.pfade.append(pfad)
        if isinstance(self.antwort, Exception):
            raise self.antwort
        return self.antwort(pfad) if callable(self.antwort) else self.antwort


class TestFahrtenbuch(unittest.TestCase):
    def test_keine_koordinaten(self):
        k = fb.knapp(T)
        for v in ("startLat", "startLon", "endLat", "endLon", "lat", "lon", "gradientProfile"):
            self.assertNotIn(v, k)
        self.assertEqual((k["km"], k["kwh"], k["verbrauch"], k["kosten"]), (33.1, 6.1, 18.4, 0.06))

    def test_monatsgrenzen(self):
        von, bis = fb.monat_grenzen("2026-02")
        self.assertEqual(dt.datetime.fromtimestamp(von / 1000), dt.datetime(2026, 2, 1))
        self.assertEqual(dt.datetime.fromtimestamp(bis / 1000).date(), dt.date(2026, 2, 28))
        for falsch in ("2026-13", "26-1", "2026-10; rm"):
            with self.assertRaises(ValueError):
                fb.monat_grenzen(falsch)

    def test_liste_seiten(self):
        pv = Pv({"success": True, "trips": [T] * fb.SEITE})
        d = fb.liste(pv, "2026-10", 100)
        self.assertTrue(d["mehr"])
        self.assertIn("limit=100&offset=100", pv.pfade[0])
        self.assertIn("from=", pv.pfade[0])

    def test_alle_bis_kurze_seite(self):
        seiten = [[T] * fb.SEITE, [T] * 3]
        d = fb.alle(Pv(lambda p: {"success": True, "trips": seiten.pop(0)}), "2026-10")
        self.assertEqual(len(d["fahrten"]), fb.SEITE + 3)

    def test_vor_019_ehrlich(self):
        self.assertEqual(fb.liste(Pv({"_status": 403}), "2026-10")["grund"], "zu_alt")
        self.assertEqual(fb.liste(Pv(urllib.error.HTTPError("u", 403, "f", {}, None)), "2026-10")["grund"], "zu_alt")

    def test_csv(self):
        de = fb.csv([fb.knapp(T)]).splitlines()
        self.assertTrue(de[0].startswith("Datum;Start;Ende;km"))
        self.assertIn(";33,1;", de[1])
        en = fb.csv([fb.knapp(T)], en=True).splitlines()
        self.assertIn(",33.1,", en[1])
        self.assertNotIn("48.2", "".join(de + en))                           # keine Koordinaten im Export


if __name__ == "__main__":
    unittest.main()
