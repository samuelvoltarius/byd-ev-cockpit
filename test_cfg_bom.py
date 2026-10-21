"""Konfiguration mit BOM (z. B. von Hand im Editor gespeichert) wird gelesen statt still verworfen."""
import importlib
import json
import os
import tempfile
import unittest


class TestBom(unittest.TestCase):
    def test_config_mit_bom(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8-sig") as f:
            json.dump({"vin": "LDEMO000000000003", "model": "BYD Dolphin Surf / Seagull (Active)"}, f)
        alt = os.environ.get("EVCOCKPIT_CFGDIR")
        os.environ["EVCOCKPIT_CFGDIR"] = d
        try:
            import evcockpit
            evcockpit = importlib.reload(evcockpit)
            self.assertEqual(evcockpit.load_cfg().get("model"), "BYD Dolphin Surf / Seagull (Active)")
        finally:
            if alt is None:
                os.environ.pop("EVCOCKPIT_CFGDIR", None)
            else:
                os.environ["EVCOCKPIT_CFGDIR"] = alt


if __name__ == "__main__":
    unittest.main()
