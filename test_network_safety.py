import unittest
import urllib.error

from network_safety import _NoRedirect, open_lan_url, private_ipv4, private_ipv4_network


class NetworkSafetyTests(unittest.TestCase):
    def test_only_rfc1918_literals_are_accepted(self):
        for address in ("10.1.2.3", "172.16.0.1", "172.31.255.254", "192.168.4.5"):
            self.assertEqual(private_ipv4(address), address)
        for address in (
            "0.0.0.0", "127.0.0.1", "169.254.1.1", "198.51.100.1",
            "203.0.113.1", "240.0.0.1", "::1", "example.com",
        ):
            with self.assertRaises(ValueError):
                private_ipv4(address)

    def test_network_must_fit_inside_rfc1918(self):
        self.assertEqual(str(private_ipv4_network("192.168.4.9/24")), "192.168.4.0/24")
        for cidr in ("192.168.0.0/16", "198.51.100.0/24", "0.0.0.0/24"):
            with self.assertRaises(ValueError):
                private_ipv4_network(cidr)

    def test_redirects_are_rejected(self):
        handler = _NoRedirect()
        request = type("Request", (), {"full_url": "http://192.168.1.5/api/state"})()
        with self.assertRaises(urllib.error.HTTPError) as caught:
            handler.redirect_request(request, None, 302, "Found", {}, "http://127.0.0.1/")
        caught.exception.close()

    def test_url_helper_revalidates_its_target(self):
        for url in ("https://192.168.1.5/state", "http://127.0.0.1/state",
                    "http://user:pass@192.168.1.5/state"):
            with self.assertRaises(ValueError):
                open_lan_url(url, timeout=1)


if __name__ == "__main__":
    unittest.main()
