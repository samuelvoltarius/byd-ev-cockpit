import unittest
from unittest.mock import patch
from io import BytesIO

from goe_diagnostics import _safe_host, fetch_goe_snapshot


class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return b'{"car":2,"pha":7,"nrg":[0,0,0,0,0,0,0,0,0,0,0,3.5]}'


class GoEDiagnosticsTests(unittest.TestCase):
    def test_private_ip(self):
        self.assertEqual(_safe_host("192.168.1.20"), "192.168.1.20")
        for address in ("8.8.8.8", "127.0.0.1", "example.com"):
            with self.assertRaises(ValueError):
                _safe_host(address)

    @patch("goe_diagnostics.urllib.request.urlopen", return_value=Response())
    def test_snapshot(self, urlopen):
        snap = fetch_goe_snapshot("192.168.1.20")
        self.assertEqual(snap.charging_state, 2)
        self.assertEqual(snap.total_power_w, 3500)
        self.assertEqual(snap.phases_raw, 7)
        self.assertIn("/api/status?filter=car,nrg,pha", urlopen.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
