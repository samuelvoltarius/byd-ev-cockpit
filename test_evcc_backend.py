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
        self.frei = patch("evcc_backend.STEUERN_FREIGEGEBEN", True)   # Logik testen, als waere freigegeben
        self.frei.start()

    def tearDown(self):
        self.frei.stop()
        self.patcher.stop()

    def lies(self, mode="pv", limit=80, **feld):
        return lambda host, port: {"loadpoints": [dict({"title": "Garage", "mode": mode, "limitSoc": limit}, **feld)]}

    def test_modus_und_zuruecklesen(self):
        # Aelteres evcc (ohne alwaysCharge): meldet pv/minpv direkt, nur ein Schreibaufruf
        from evcc_backend import set_loadpoint
        r = set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies("pv"))
        self.assertEqual(self.calls, [("POST", "http://192.168.1.8:7070/api/loadpoints/1/mode/pv")])
        self.assertEqual(r, {"ok": True, "mode": "pv", "mode_roh": "pv", "limit_soc": 80})

    def test_neues_evcc_smart_exakt_unterschieden(self):
        # Neues evcc (0.317): smart + alwaysCharge off = pv, smart + on/once = minpv (WALLBOX_VERTRAG §4)
        from evcc_backend import set_loadpoint
        self.assertTrue(set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies("smart", alwaysCharge="off"))["ok"])
        self.assertFalse(set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies("smart", alwaysCharge="on"))["ok"])
        self.assertTrue(set_loadpoint("192.168.1.8", 7070, 1, mode="minpv", read_state=self.lies("smart", alwaysCharge="once"))["ok"])
        self.assertFalse(set_loadpoint("192.168.1.8", 7070, 1, mode="minpv", read_state=self.lies("smart", alwaysCharge="off"))["ok"])
        self.assertFalse(set_loadpoint("192.168.1.8", 7070, 1, mode="now", read_state=self.lies("smart", alwaysCharge="off"))["ok"])

    def test_neues_evcc_alwayscharge_wird_mitgesetzt(self):
        from evcc_backend import set_loadpoint
        set_loadpoint("192.168.1.8", 7070, 1, mode="pv", read_state=self.lies("smart", alwaysCharge="on"))
        set_loadpoint("192.168.1.8", 7070, 1, mode="minpv", read_state=self.lies("smart", alwaysCharge="off"))
        set_loadpoint("192.168.1.8", 7070, 1, mode="now", read_state=self.lies("smart", alwaysCharge="off"))
        self.assertEqual([u.split("7070")[1] for _, u in self.calls], [
            "/api/loadpoints/1/mode/pv", "/api/loadpoints/1/alwayscharge/off",
            "/api/loadpoints/1/mode/minpv", "/api/loadpoints/1/alwayscharge/on",
            "/api/loadpoints/1/mode/now"])

    def test_heizung_nie_steuern(self):
        from evcc_backend import set_loadpoint
        for feld in ({"chargerFeatureHeating": True}, {"chargerFeatureIntegratedDevice": True}):
            with self.assertRaises(PermissionError):
                set_loadpoint("192.168.1.8", 7070, 1, limit_soc=60, read_state=self.lies(**feld))
        self.assertEqual(self.calls, [])

    def test_modus_von(self):
        from evcc_backend import modus_von, normalize_loadpoints
        self.assertEqual([modus_von(*x) for x in (("smart", "off"), ("smart", "on"), ("smart", None), ("off", None), ("fast", None))],
                         ["pv", "minpv", None, "off", None])
        n = normalize_loadpoints({"loadpoints": [{"title": "Heat pump", "mode": "smart", "alwaysCharge": "off", "chargerFeatureHeating": True}]})
        self.assertEqual((n[0]["art"], n[0]["modus"]), ("heizung", "pv"))

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


class EvccSteuernAbgeschaltetTests(unittest.TestCase):
    """Code-Schalter aus: es geht KEIN Schreibaufruf an evcc raus (seit 1.14 an, nach dem Praxistest)."""

    def test_kein_schreibaufruf(self):
        import evcc_backend
        with patch("evcc_backend.STEUERN_FREIGEGEBEN", False), patch("evcc_backend.open_lan_url") as offen:
            for kw in ({"mode": "pv"}, {"mode": "now"}, {"mode": "off"}, {"limit_soc": 80}):
                with self.assertRaises(PermissionError):
                    evcc_backend.set_loadpoint("192.168.1.8", 7070, 1, read_state=lambda h, p: {}, **kw)
            offen.assert_not_called()

    @patch("evcc_backend.open_lan_url", return_value=FakeResponse())
    def test_lesen_bleibt_an(self, offen):
        self.assertEqual(get_evcc_state("192.168.1.8")["site"]["grid_w"], -2500)
        self.assertEqual(offen.call_args.kwargs.get("method", "GET"), "GET")


if __name__ == "__main__":
    unittest.main()
