import unittest
from unittest.mock import patch
from evcc_backend import get_evcc_state, validate_evcc_address


class FakeResponse:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size):
        return (b'{"grid":{"power":-2500},"pvPower":5000,'
                b'"battery":{"power":-800,"soc":72},"homePower":1700,"tariffGrid":0.31,'
                b'"loadpoints":[{"title":"Garage","chargePower":2300,'
                b'"password":"must-not-leak"}],"config":"/private/evcc.yaml"}')


class EvccBackendTests(unittest.TestCase):
    def test_address_validation(self):
        self.assertEqual(validate_evcc_address("192.168.1.8"), "http://192.168.1.8:7070")
        for host in ("127.0.0.1", "8.8.8.8", "example.com"):
            with self.assertRaises(ValueError):
                validate_evcc_address(host)

    @patch("evcc_backend.open_lan_url", return_value=FakeResponse())
    def test_state(self, open_url):
        data = get_evcc_state("192.168.1.8")
        self.assertEqual(data["site"]["grid_w"], -2500)
        self.assertEqual(data["site"]["battery_w"], -800)
        self.assertEqual(data["site"]["battery_soc"], 72)
        self.assertEqual(data["site"]["tariff_grid"], 0.31)
        self.assertEqual(len(data["loadpoints"]), 1)
        self.assertNotIn("raw", data)
        self.assertNotIn("password", data["loadpoints"][0])
        self.assertEqual(open_url.call_args.args[0], "http://192.168.1.8:7070/api/state")


class EvccSteuernTests(unittest.TestCase):
    """Steuern nur Modus/Ziel-Ladestand, nur ueber evcc, immer mit Zuruecklesen."""

    def setUp(self):
        self.calls = []

        class Ok:
            status = 200
            def __enter__(s): return s
            def __exit__(s, *a): return False

        def fake_open(url, timeout, method="GET"):
            self.calls.append((method, url))
            return Ok()
        self.patcher = patch("evcc_backend.open_lan_url", side_effect=fake_open)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def lies(self, mode="pv", limit=80):
        return lambda host, port: {"loadpoints": [{"title": "Garage", "mode": mode, "limitSoc": limit}]}

    def test_modus_und_zuruecklesen(self):
        from evcc_backend import set_loadpoint
        r = set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies("pv"))
        self.assertEqual(self.calls, [("POST", "http://192.168.1.8:7070/api/loadpoints/1/mode/pv")])
        self.assertEqual(r, {"ok": True, "mode": "pv", "limit_soc": 80})

    def test_neues_evcc_meldet_smart(self):
        # Aktuelles evcc: pv/minpv sind Aliase und kommen als "smart" zurueck -> gilt als uebernommen
        from evcc_backend import set_loadpoint
        self.assertTrue(set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies("smart"))["ok"])
        self.assertTrue(set_loadpoint("192.168.1.8", 7070, 1, mode="minpv", read_state=self.lies("smart"))["ok"])
        self.assertFalse(set_loadpoint("192.168.1.8", 7070, 1, mode="now", read_state=self.lies("smart"))["ok"])

    def test_anmeldung_verlangt(self):
        import urllib.error
        from evcc_backend import set_loadpoint
        self.patcher.stop()
        with patch("evcc_backend.open_lan_url",
                   side_effect=urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)):
            with self.assertRaisesRegex(ValueError, "Anmeldung"):
                set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies())
        self.patcher.start()

    def test_ziel_ladestand(self):
        from evcc_backend import set_loadpoint
        r = set_loadpoint("192.168.1.8", 7070, 1, limit_soc=90, read_state=self.lies(limit=80))
        self.assertEqual(self.calls[0][1], "http://192.168.1.8:7070/api/loadpoints/1/limitsoc/90")
        self.assertFalse(r["ok"])                  # evcc hat 80 behalten -> ehrlich "nicht uebernommen"

    def test_nur_erlaubtes(self):
        from evcc_backend import set_loadpoint
        for kw in ({"mode": "fast"}, {"limit_soc": 10}, {"limit_soc": 101}, {"limit_soc": "90"},
                   {}, {"mode": "pv", "limit_soc": 80}):
            with self.assertRaises(ValueError):
                set_loadpoint("192.168.1.8", 7070, 1, read_state=self.lies(), **kw)
        for lp in (0, 21, "1", True):
            with self.assertRaises(ValueError):
                set_loadpoint("192.168.1.8", 7070, lp, mode="pv", read_state=self.lies())
        with self.assertRaises(ValueError):
            set_loadpoint("8.8.8.8", 7070, 1, mode="pv", read_state=self.lies())
        self.assertEqual(self.calls, [])           # nichts wurde gesendet


if __name__ == "__main__":
    unittest.main()
