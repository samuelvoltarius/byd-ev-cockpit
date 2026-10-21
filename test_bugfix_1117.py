"""1.11.7 - Bugfixes aus DOPPELUNGEN.md: F5 (/save mischt), F6 (kein stiller OSM-Rueckfall), F7 (eine Reichweiten-Rechnung)."""
import os
import tempfile
import unittest

_alt = os.environ.get("EVCOCKPIT_CFGDIR")
os.environ["EVCOCKPIT_CFGDIR"] = tempfile.mkdtemp()
try:
    import evcockpit as ev
finally:
    os.environ.pop("EVCOCKPIT_CFGDIR", None) if _alt is None else os.environ.__setitem__("EVCOCKPIT_CFGDIR", _alt)

QUELLE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()


class TestReichweite(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(ev._CFG)

    def tearDown(self):
        ev._CFG.clear(); ev._CFG.update(self.cfg)

    def test_eine_rechnung(self):
        ev._CFG.clear(); ev._CFG.update(battery_kwh=43.2)
        self.assertEqual(ev.reichweite_geschaetzt(71, 16.3), 188)

    def test_modell_statt_60(self):
        ev._CFG.clear(); ev._CFG.update(model="BYD Dolphin Surf / Seagull (Comfort/Design)")
        self.assertEqual(ev.reichweite_geschaetzt(50, 20), round(43.2 * 0.5 / 20 * 100))
        ev._CFG.clear(); ev._CFG.update(model="Anderes / unbekannt")
        self.assertIsNone(ev.reichweite_geschaetzt(50, 20))                 # keine geratene Akkugroesse

    def test_unplausibel(self):
        ev._CFG.clear(); ev._CFG.update(battery_kwh=43.2)
        for soc, v in ((0, 16), (50, 0), (50, 2), (50, None), (None, 16)):
            self.assertIsNone(ev.reichweite_geschaetzt(soc, v))

    def test_nur_noch_eine_stelle(self):
        self.assertNotIn('float(_CFG.get("battery_kwh") or 60.0)', QUELLE)
        self.assertEqual(QUELLE.count("reichweite_geschaetzt("), 4)        # Definition + Cloud + HA + Panoptes


class TestSpeichernUndKarte(unittest.TestCase):
    def test_save_mischt_in_bestehende_config(self):
        i = QUELLE.index('weg = {k for k in ("install_id", "battery_quelle", "auth_blocked") if k not in c}')
        self.assertIn("c = dict({k: v for k, v in _CFG.items() if k not in weg}, **c)", QUELLE[i:i + 400])

    def test_kein_stiller_osm_rueckfall(self):
        self.assertNotIn(".catch(()=>osm())", QUELLE)
        self.assertIn("Community-Karte gerade nicht erreichbar", QUELLE)


if __name__ == "__main__":
    unittest.main()
