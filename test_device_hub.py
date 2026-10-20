import unittest
from unittest.mock import patch
import device_hub


class FakeResponse:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, size): return b'{"version":"1.2.3","loadpoints":[],"config":"private"}'


class DiscoveryTests(unittest.TestCase):
    def test_lan_validation(self):
        self.assertEqual(device_hub.lan_address("192.168.0.5"), "192.168.0.5")
        for value in ("127.0.0.1", "8.8.8.8", "example.com"):
            with self.assertRaises(ValueError):
                device_hub.lan_address(value)

    def test_subnet_limit(self):
        for subnet in ("192.168.0.0/16", "8.8.8.0/24"):
            with self.assertRaises(ValueError):
                device_hub.discover(subnet)

    def test_automatic_network_needs_no_cidr_knowledge(self):
        self.assertEqual(device_hub.automatic_lan_network("192.168.50.23"),
                         "192.168.50.0/24")
        with self.assertRaises(ValueError):
            device_hub.automatic_lan_network("8.8.8.8")

    @patch("device_hub.probe")
    def test_discover(self, probe):
        probe.side_effect = lambda ip: {"ip": ip, "online": ip.endswith(".1")}
        results = device_hub.discover("192.168.1.0/30")
        self.assertEqual([x["ip"] for x in results], ["192.168.1.1"])

    @patch("device_hub.open_lan_url", return_value=FakeResponse())
    def test_evcc_probe_is_minimized(self, open_url):
        result = device_hub.probe("192.168.1.20")
        self.assertEqual(result["vendor"], "evcc")
        self.assertEqual(result["port"], 7070)
        self.assertEqual(result["model"], "1.2.3")
        self.assertNotIn("data", result)


if __name__ == "__main__":
    unittest.main()
