import unittest
from unittest.mock import patch
import device_hub


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

    @patch("device_hub.probe")
    def test_discover(self, probe):
        probe.side_effect = lambda ip: {"ip": ip, "online": ip.endswith(".1")}
        results = device_hub.discover("192.168.1.0/30")
        self.assertEqual([x["ip"] for x in results], ["192.168.1.1"])


if __name__ == "__main__":
    unittest.main()
