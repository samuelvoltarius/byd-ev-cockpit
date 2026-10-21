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



class PrivatesZielTests(unittest.TestCase):
    """WALLBOX_VERTRAG §2: Tailscale, Namen nur mit privater Aufloesung, eigene Server gesperrt, Testschalter nur im Test."""

    def test_adressen(self):
        from network_safety import private_ziel
        self.assertEqual(private_ziel("100.86.70.71"), ("http", "100.86.70.71"))
        self.assertEqual(private_ziel("192.168.1.8"), ("http", "192.168.1.8"))
        for h in ("127.0.0.1", "169.254.169.254", "8.8.8.8", "0.0.0.0", "byd.serveone.at", "serveone.at", "a b", ""):
            with self.assertRaises(ValueError):
                private_ziel(h, aufloesen=lambda *a: [(0, 0, 0, "", ("192.168.1.2", 0))])

    def test_namen(self):
        from network_safety import private_ziel
        privat = lambda *a: [(0, 0, 0, "", ("192.168.1.9", 0)), (0, 0, 0, "", ("100.70.1.2", 0))]
        gemischt = lambda *a: [(0, 0, 0, "", ("192.168.1.9", 0)), (0, 0, 0, "", ("93.184.216.34", 0))]
        self.assertEqual(private_ziel("evcc.local", aufloesen=privat), ("http", "100.70.1.2"))
        with self.assertRaises(ValueError):
            private_ziel("evcc.example.com", aufloesen=gemischt)

    def test_testziel_nur_im_testlauf(self):
        from network_safety import private_ziel, testziel, open_lan_url
        with self.assertRaises(ValueError):
            private_ziel("demo.evcc.io", aufloesen=lambda *a: [(0, 0, 0, "", ("93.184.216.34", 0))])
        with testziel("demo.evcc.io"):
            self.assertEqual(private_ziel("demo.evcc.io"), ("https", "demo.evcc.io"))
        with self.assertRaises(ValueError):
            open_lan_url("https://demo.evcc.io:443/api/state", timeout=1)
        with self.assertRaises(ValueError):
            open_lan_url("http://demo.evcc.io/api/state", timeout=1)


if __name__ == "__main__":
    unittest.main()
