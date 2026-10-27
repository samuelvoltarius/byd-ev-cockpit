"""1.18.1 (Inventur Regel 1): Der Poller laeuft auch ohne pybyd. Panoptes und HA werden versucht; nur die Cloud meldet den Hinweis."""
import os
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

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


class Stop(BaseException):
    """Beendet den Poller im Test (BaseException: der Poller faengt nur Exception)."""


class TestPollerOhnePybyd(unittest.TestCase):
    def test_panoptes_wird_versucht_obwohl_pybyd_fehlt(self):
        aufrufe = []

        def runde(cache):
            aufrufe.append(1)
            if len(aufrufe) >= 2:
                raise Stop()
            return True                                # Panoptes hat geliefert
        ev._CFG["vin"] = "lokal-test"
        with patch.dict(sys.modules, {"pybyd": None}), patch.object(ev, "_panoptes_runde", runde), \
                patch.object(ev, "_warte_panoptes", lambda s: None), patch.object(ev, "load_cache", lambda: {}):
            with self.assertRaises(Stop):
                ev._poller()
        self.assertEqual(len(aufrufe), 2)               # Thread lief weiter, statt sofort zu enden

    def test_cloud_ohne_pybyd_meldet_klar_und_stirbt_nicht(self):
        sleeps = []

        def schlaf(x):
            sleeps.append(x)
            raise Stop()
        ev._CFG.update(vin="x", datenquelle="byd")
        ev._CFG["username"] = "a@b.c"
        ev._STATE["_err"] = ""
        with patch.dict(sys.modules, {"pybyd": None}), patch.object(ev, "_panoptes_runde", lambda c: False), \
                patch.object(ev, "_cloud_an", lambda: True), patch.object(ev.time, "sleep", schlaf), patch.object(ev, "load_cache", lambda: {}):
            ev._STATE.pop("_auth_blocked", None)
            ev._CFG.pop("auth_blocked", None)
            with self.assertRaises(Stop):
                ev._poller()
        self.assertIn("pybyd", ev._STATE["_err"])
        self.assertIn("BYD-Cloud", ev._STATE["_err"])
        self.assertEqual(sleeps, [30])

    def test_kein_import_am_threadanfang(self):
        import inspect
        quelle = inspect.getsource(ev._poller)
        kopf = quelle.split("while True:")[0]
        self.assertNotIn("pybyd", kopf.replace("pybyd (BYD-Cloud)", "").replace("laufen ohne pybyd", "").replace("Nutzer ohne", ""))


if __name__ == "__main__":
    unittest.main()
