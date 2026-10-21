"""Ohne gekoppeltes Panoptes arbeitet das Cockpit unveraendert (Vorgabe Koordination fuer 1.7).

Geprueft: Planer-Kennung, Datenquelle/Abfrage-Weg und Planer-Meldungen beruehren Panoptes nur, wenn es gekoppelt ist.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("EVCOCKPIT_CFGDIR", tempfile.mkdtemp(prefix="evc-test-"))
import evcockpit as e          # noqa: E402
import panoptes_source        # noqa: E402
import planer_bridge as pb     # noqa: E402


class TestOhnePanoptes(unittest.TestCase):
    def setUp(self):
        self.cfg_alt = dict(e._CFG)
        e._CFG.clear()
        e._CFG.update({"vin": "TESTVIN0000000000", "planer": True, "planer_token": "0" * 32,
                       "planer_auto": "evc-1a2b3c4d"})
        e._PANOPTES.update(key=None, obj=None)
        e._PAN_ID.update(t=0.0, auto="")

    def tearDown(self):
        e._CFG.clear()
        e._CFG.update(self.cfg_alt)

    def test_eigene_kennung_ohne_panoptes(self):
        with patch.object(panoptes_source, "identitaet", side_effect=AssertionError("Panoptes darf nicht gefragt werden")):
            self.assertEqual(e._planer_kennung(), "evc-1a2b3c4d")

    def test_keine_panoptes_runde_ohne_kopplung(self):
        with patch.object(panoptes_source.Panoptes, "lies", side_effect=AssertionError("kein Zugriff aufs Auto")):
            self.assertFalse(e._panoptes_runde({}))

    def test_planer_meldet_ohne_panoptes_selbst(self):
        calls = []
        b = pb.Bruecke(anfrage=lambda p, t, d=None: calls.append(p) or (200, {"ok": True}), uhr=lambda: 1000.0)
        b.nach_abfrage(dict(e._CFG), {"online": "ON", "soc": 55})
        self.assertEqual(calls, ["mein-soc"])
        self.assertFalse(b.status["panoptes"])

    def test_mit_panoptes_wird_dessen_kennung_genommen(self):
        e._CFG.update(panoptes=True, panoptes_url="http://100.1.2.3:8180", panoptes_code="byd-1-x")
        e._PANOPTES["obj"] = object()
        with patch.object(panoptes_source, "identitaet", return_value="pan-777"):
            self.assertEqual(e._planer_kennung(), "pan-777")
        e._PAN_ID.update(t=0.0, auto="")
        with patch.object(panoptes_source, "identitaet", return_value=""):   # Endpunkt fehlt noch -> eigene
            self.assertEqual(e._planer_kennung(), "evc-1a2b3c4d")


if __name__ == "__main__":
    unittest.main(verbosity=2)
