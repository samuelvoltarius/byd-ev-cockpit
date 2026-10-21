"""1.12.2: Boersenpreis - ein Wert show_price, aus = Anzeige leer und nichts abgerufen; Ring in %."""
import os
import tempfile
import unittest

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


class TestPreisSchalter(unittest.TestCase):
    def test_aus_leert_anzeige(self):
        ev._STATE.update(price_now=12.3, price_bars=[{"h": "10", "ct": 1}], price_src="x")
        ev._preis_schalten(False)
        for k in ev._PREIS_FELDER:
            self.assertNotIn(k, ev._STATE)
        self.assertTrue(ev._PREIS_WACH.is_set())
        ev._PREIS_WACH.clear()

    def test_status_zeile_ohne_ladestand(self):
        i = ev.COCKPIT.index("function zeilen(s)")
        self.assertNotIn("__T('Ladestand')", ev.COCKPIT[i:ev.COCKPIT.index("function energieRing", i)])


if __name__ == "__main__":
    unittest.main()
