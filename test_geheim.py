"""Regel S: Geheimnisse nie im Klartext auf der Platte (Windows: DPAPI). Unter Linux/macOS bleibt 0600."""
import importlib
import json
import os
import sys
import tempfile
import unittest

import geheim


@unittest.skipUnless(sys.platform == "win32", "DPAPI nur unter Windows")
class TestDpapi(unittest.TestCase):
    def test_rundlauf_und_fremddaten(self):
        g = geheim.schuetzen("jwt-abc.def")
        self.assertTrue(g.startswith("dpapi:") and "jwt-abc" not in g)
        self.assertEqual(geheim.entschuetzen(g), "jwt-abc.def")
        self.assertEqual(geheim.schuetzen(g), g)                         # nicht doppelt
        self.assertEqual(geheim.entschuetzen("dpapi:AAAA"), "")          # kaputt/fremd -> leer, kein Absturz
        self.assertEqual(geheim.schuetzen(""), "")

    def test_cockpit_schreibt_nie_klartext_und_migriert(self):
        d = tempfile.mkdtemp()
        roh = {"vin": "LDEMO", "panoptes_jwt": "geheim-jwt-123", "planer_token": "g:" + "ab" * 32, "password": "pw-xyz",
               "model": "BYD Dolphin Surf / Seagull (Active)"}
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
            json.dump(roh, f)                                           # alte Version: Klartext
        os.environ["EVCOCKPIT_CFGDIR"] = d
        import evcockpit
        evcockpit = importlib.reload(evcockpit)
        cfg = evcockpit.load_cfg()
        self.assertEqual((cfg["panoptes_jwt"], cfg["planer_token"], cfg["password"]),
                         ("geheim-jwt-123", "g:" + "ab" * 32, "pw-xyz"))    # im Speicher Klartext
        datei = open(os.path.join(d, "config.json"), encoding="utf-8").read()
        for klar in ("geheim-jwt-123", "ab" * 32, "pw-xyz"):
            self.assertNotIn(klar, datei)                               # beim Laden migriert
        self.assertIn("LDEMO", datei)                                   # Unkritisches bleibt lesbar
        evcockpit._CFG["planer_token"] = "g:" + "cd" * 32
        evcockpit.save_cfg(evcockpit._CFG)
        self.assertNotIn("cd" * 32, open(os.path.join(d, "config.json"), encoding="utf-8").read())
        self.assertEqual(evcockpit.load_cfg()["planer_token"], "g:" + "cd" * 32)


class TestFelder(unittest.TestCase):
    def test_alle_geheimen_felder(self):
        for f in ("password", "control_pin", "panoptes_jwt", "panoptes_code", "planer_token", "ha_src_token",
                  "ha_pass", "pv_token", "charger_token"):
            self.assertIn(f, geheim.FELDER)


if __name__ == "__main__":
    unittest.main()
