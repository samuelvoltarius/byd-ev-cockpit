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


if __name__ == "__main__":
    unittest.main()
