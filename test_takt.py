"""1.9.8: Wie oft das Cockpit Panoptes fragt (jede Abfrage weckt die App im Auto) und Akku-kWh vom Auto."""
import os
import tempfile
import time
import unittest

import panoptes_source as ps

_D = tempfile.mkdtemp()
_ALT = os.environ.get("EVCOCKPIT_CFGDIR")
os.environ["EVCOCKPIT_CFGDIR"] = _D
try:
    import evcockpit as ev
finally:
    if _ALT is None:
        os.environ.pop("EVCOCKPIT_CFGDIR", None)
    else:
        os.environ["EVCOCKPIT_CFGDIR"] = _ALT


class TestTakt(unittest.TestCase):
    def setUp(self):
        self.cfg, self.state = dict(ev._CFG), dict(ev._STATE)
        ev._CFG.clear()
        ev._STATE.clear()
        ev._TAKT.update(sichtbar_ts=time.time(), schnell_bis=0.0)

    def tearDown(self):
        ev._CFG.clear(); ev._CFG.update(self.cfg)
        ev._STATE.clear(); ev._STATE.update(self.state)

    def test_standard_geparkt_5_fahrt_1(self):
        self.assertEqual(ev._panoptes_takt(), 300)
        ev._STATE["gear"] = "D"
        self.assertEqual(ev._panoptes_takt(), 60)
        ev._STATE.update(gear="P", charging="ON")
        self.assertEqual(ev._panoptes_takt(), 60)

    def test_auswahl_und_nur_manuell(self):
        ev._CFG["abfrage_geparkt"] = 30
        self.assertEqual(ev._panoptes_takt(), 1800)
        ev._CFG["abfrage_geparkt"] = 0
        self.assertIsNone(ev._panoptes_takt())                     # nur manuell
        ev._CFG["abfrage_geparkt"] = 7                              # nicht in der Auswahl -> Standard
        self.assertEqual(ev._panoptes_takt(), 300)
        self.assertEqual(ev.ABFRAGE_WAHL, (1, 2, 5, 10, 15, 30, 0))

    def test_tab_verborgen_pausiert(self):
        ev._TAKT["sichtbar_ts"] = time.time() - ev.SICHTBAR_FRIST - 1
        self.assertIsNone(ev._panoptes_takt())
        self.assertTrue(ev.abfrage_status()["pausiert"])
        ev._CFG["ha"] = True                                         # Werte gehen an Home Assistant -> weiter
        self.assertEqual(ev._panoptes_takt(), 300)

    def test_schnellphase_nach_nutzeraktion(self):
        ev._CFG["abfrage_geparkt"] = 0
        ev._WECKER.clear()
        ev.nutzer_aktion()
        self.assertTrue(ev._WECKER.is_set())
        self.assertEqual(ev._panoptes_takt(), 5)
        self.assertIsNone(ev._panoptes_takt(time.time() + ev.ABFRAGE_SCHNELL_DAUER + 1))   # hoechstens 60 s
        ev._WECKER.clear()

    def test_zaehler_heute(self):
        ev._TAKT.update(tag="2000-01-01", heute=99)
        ev._abfrage_zaehlen()
        self.assertEqual(ev.abfrage_status()["heute"], 1)


class TestAkkuVomAuto(unittest.TestCase):
    def test_uebersicht_liefert_usable_kwh(self):
        st = ps.aus_uebersicht({"battery": {"socPct": 71, "usableKwh": 44.1}})
        self.assertEqual(st["usable_kwh"], 44.1)
        self.assertNotIn("usable_kwh", ps.aus_uebersicht({"battery": {"socPct": 71, "usableKwh": 3}}))

    def test_quelltext_handeintrag_gewinnt(self):
        q = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()
        self.assertIn('_CFG.get("battery_quelle") != "manuell"', q)
        self.assertIn('c["battery_quelle"] = "manuell"', q)
        self.assertIn("b.battery_kwh_hand=KWH_HAND;", q)


if __name__ == "__main__":
    unittest.main()
