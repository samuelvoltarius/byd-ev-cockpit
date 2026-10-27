"""1.19.0: Schnellknoepfe, Wallbox-Zeile, Gestaltungs-Werte, Aufraeumen."""
import os
import tempfile
import unittest

_D = tempfile.mkdtemp()
os.environ["EVCOCKPIT_CFGDIR"] = _D
import evcockpit as ev  # noqa: E402


class Seite(unittest.TestCase):
    def test_schnellknoepfe_und_wallbox(self):
        h = ev.HTML if hasattr(ev, "HTML") else ""
        if not h:
            h = next(v for k, v in vars(ev).items() if isinstance(v, str) and "id=statuszeile" in v)
        for s in ('id=sq_lock', 'id=sq_heat', 'id=kt_wb', 'async function wbZeile', 'byd-design.css v1', '--lime:#22c55e'):
            self.assertIn(s, h)
        self.assertNotIn("quicknav\"", h.replace("quicknav{", ""))   # Schnellnavigation bleibt weg

    def test_kein_hupen_kein_blinken(self):
        h = next(v for k, v in vars(ev).items() if isinstance(v, str) and "id=statuszeile" in v)
        self.assertNotIn("cmd('find')", h)
        self.assertNotIn("p_find", h)
        self.assertNotIn("_find_car", open(ev.__file__, encoding="utf-8").read())
        import sicherheit
        self.assertIn("find", sicherheit.NIE)

    def test_energy_hub_weg(self):
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(ev.__file__), "energy_hub.py")))


if __name__ == "__main__":
    unittest.main()
