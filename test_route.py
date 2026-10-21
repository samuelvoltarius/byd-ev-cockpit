"""1.10: Route-Reiter - Start = Autoposition, nur auf Klick, flache Form fuer an-auto, ehrliche Oeffnungszeiten."""
import os
import unittest

import route_planer as rp

PLAN = {"route": {"km": 199.4, "minuten": 128, "geometrie": [[48.2, 16.36], [47.6, 15.8], [47.07, 15.43]]},
        "fahrzeug": {"name": "BYD Dolphin Surf"}, "soc_start": 71, "soc_ankunft": 22.4, "modus": "kompromiss",
        "stopps": [{"saeule": {"name": "Lidl Gleisdorf", "betreiber": "Lidl", "lat": 47.1, "lon": 15.7, "kw": 150,
                               "km_auf_route": 160, "offen": {"bis": "22:00"}},
                    "soc_vorher": 18, "soc_nachher": 60, "ladedauer_min": 21, "kwh": 18.5, "kosten_beste_option": 7.2,
                    "mit_eigener_karte": True},
                   {"saeule": {"name": "Ohne Angabe", "lat": 47.2, "lon": 15.6, "kw": 50}, "soc_vorher": 30,
                    "soc_nachher": 50, "ladedauer_min": 9}],
        "kosten": {"basis": {"gesamt": 9.9}}, "warnungen": ["Stau A2"]}


class Fake:
    def __init__(self, antworten):
        self.antworten, self.aufrufe = antworten, []

    def __call__(self, pfad, token, daten=None, timeout=12):
        self.aufrufe.append((pfad, daten))
        return self.antworten.get(pfad, (404, {}))


class TestRoute(unittest.TestCase):
    def test_start_ist_autoposition(self):
        b = rp.anfrage_body({"ziel": [47.07, 15.43]}, (48.2063, 16.3655), 71, "BYD Dolphin Surf", "a-1")
        self.assertEqual((b["start"], b["soc_start"], b["fahrzeug"], b["auto"]), ([48.2063, 16.3655], 71, "BYD Dolphin Surf", "a-1"))
        b = rp.anfrage_body({"start": [47.0, 15.0], "ziel": [47.07, 15.43], "soc_start": "55"}, (48.2, 16.3), 71, "X")
        self.assertEqual((b["start"], b["soc_start"]), ([47.0, 15.0], 55))
        with self.assertRaises(ValueError):
            rp.anfrage_body({"ziel": [47.07, 15.43]}, None, 71, "X")       # weder Auto noch eigener Start
        with self.assertRaises(ValueError):
            rp.anfrage_body({"ziel": [0, 0]}, (48.2, 16.3), 71, "X")
        self.assertEqual(rp.anfrage_body({"ziel": [1, 2], "modus": "rm -rf"}, (3, 4), None, "X")["modus"], "kompromiss")

    def test_kurz_und_oeffnung(self):
        f = Fake({"plan": (200, PLAN)})
        k = rp.planen("g:" + "a" * 64, {"start": [1, 2]}, anfrage=f)
        self.assertEqual(f.aufrufe[0][0], "plan")
        self.assertEqual((k["km"], k["soc_ankunft"], k["kosten"], k["lade_min"]), (199.4, 22.4, 9.9, 30))
        self.assertEqual([s["oeffnung"] for s in k["stopps"]], ["offen bis 22:00", "Öffnungszeit unbekannt"])
        self.assertTrue(k["stopps"][0]["eigene_karte"])

    def test_fehler_ehrlich(self):
        with self.assertRaises(ValueError):
            rp.planen("t", {}, anfrage=Fake({"plan": (200, {"fehler": "kein Fahrzeugprofil hinterlegt"})}))
        with self.assertRaisesRegex(ValueError, "Minute"):
            rp.planen("t", {}, anfrage=Fake({"plan": (429, {})}))

    def test_an_auto_flach(self):
        k = rp.kurz(PLAN)
        p = rp.fuer_auto(k, [48.2, 16.36], [47.07, 15.43], "Mein Auto", "Graz", "BYD Dolphin Surf")
        self.assertEqual(len(p["geometrie"]), 3)
        self.assertEqual(set(p["stopps"][0]), {"lat", "lon", "name", "km", "kw", "cpo", "soc_an", "soc_ab", "dauer_min", "kwh", "preis"})
        self.assertNotIn("preis", p["stopps"][1])
        self.assertEqual(p["titel"], "Mein Auto → Graz")
        f = Fake({"an-auto": (200, {"ok": True, "gueltig_bis": "x"})})
        rp.an_auto("t", p, "a-1", anfrage=f)
        self.assertEqual(f.aufrufe[0][1]["auto"], "a-1")

    def test_ortssuche(self):
        f = Fake({"orte": (200, {"orte": [{"name": "Graz", "lat": 47.07, "lon": 15.43}]})})
        self.assertEqual(rp.orte("t", "Gr", anfrage=f), [])                 # unter 3 Zeichen: gar nicht fragen
        self.assertEqual(f.aufrufe, [])
        self.assertEqual(rp.orte("t", "Graz", anfrage=f)[0]["name"], "Graz")
        f = Fake({"ziel-aus-text": (200, {"ok": True, "ort": {"lat": 47.0, "lon": 15.0, "name": "Pin"}})})
        self.assertEqual(rp.orte("t", "https://maps.example/x", anfrage=f)[0]["name"], "Pin")

    def test_koordinaten_nie_in_der_url(self):
        q = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "route_planer.py"), encoding="utf-8").read()
        self.assertNotIn("?start", q)
        self.assertNotIn("?ziel", q)
        e = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()
        self.assertIn("Start und Ziel gehen nur beim Klick auf „Route berechnen“", e)
        self.assertIn("Am Fahrzeug wird nichts ausgelöst", e)


if __name__ == "__main__":
    unittest.main()
