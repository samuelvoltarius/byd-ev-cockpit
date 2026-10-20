import json
import unittest
from unittest.mock import MagicMock, patch

from evcockpit import _charger_rows, _fetch_chargers_server


class ChargerServerTests(unittest.TestCase):
    def test_open_glance_response_keeps_power_price_and_source(self):
        payload = {"elements": [{
            "type": "node", "id": "AT*TEST", "lat": 47.8, "lon": 13.05,
            "tags": {"amenity": "charging_station", "name": "Ladepark",
                     "operator": "Testwerke", "charging_station:output": "300 kW",
                     "capacity": "4", "socket:type2_combo": "4",
                     "x:price_eur_kwh": "0.59", "x:source": "E-Control"},
        }]}
        rows = _charger_rows(payload, 47.8, 13.05)
        self.assertEqual(rows[0]["kw"], 300)
        self.assertEqual(rows[0]["eur_kwh"], 0.59)
        self.assertEqual(rows[0]["source"], "E-Control")
        self.assertIn("type2 combo", rows[0]["sockets"])

    @patch("urllib.request.urlopen")
    def test_configured_server_uses_read_only_endpoint_and_token(self, urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({"elements": []}).encode()
        urlopen.return_value.__enter__.return_value = response

        rows = _fetch_chargers_server(47.8, 13.05, 15000,
                                      "https://server.example:8464", "secret")

        self.assertEqual(rows, [])
        request = urlopen.call_args.args[0]
        self.assertIn("/chargers?lat=47.800000&lon=13.050000&radius=15000", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(request.get_header("X-copilot-token"), "secret")


if __name__ == "__main__":
    unittest.main()
