import unittest
from unittest.mock import patch
from evcc_backend import get_evcc_state, validate_evcc_address


class FakeResponse:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size): return b'{"result":{"gridPower":-2500,"pvPower":5000,"loadpoints":[{"chargePower":2300}]}}'


class EvccBackendTests(unittest.TestCase):
    def test_address_validation(self):
        self.assertEqual(validate_evcc_address("192.168.1.8"), "http://192.168.1.8:7070")
        for host in ("127.0.0.1", "8.8.8.8", "example.com"):
            with self.assertRaises(ValueError):
                validate_evcc_address(host)

    @patch("evcc_backend.urllib.request.urlopen", return_value=FakeResponse())
    def test_state(self, urlopen):
        data = get_evcc_state("192.168.1.8")
        self.assertEqual(data["site"]["grid_w"], -2500)
        self.assertEqual(len(data["loadpoints"]), 1)
        self.assertEqual(urlopen.call_args.args[0], "http://192.168.1.8:7070/api/state")


if __name__ == "__main__":
    unittest.main()
