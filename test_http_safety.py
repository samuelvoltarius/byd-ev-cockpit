import unittest

from evcockpit import _same_origin_request


class RequestSafetyTests(unittest.TestCase):
    def test_same_origin_browser_request(self):
        headers = {"Host": "192.168.1.20:8099", "Origin": "http://192.168.1.20:8099",
                   "Sec-Fetch-Site": "same-origin"}
        self.assertTrue(_same_origin_request(headers))

    def test_cross_origin_browser_request(self):
        headers = {"Host": "192.168.1.20:8099", "Origin": "https://attacker.example",
                   "Sec-Fetch-Site": "cross-site"}
        self.assertFalse(_same_origin_request(headers))

    def test_local_cli_without_browser_headers(self):
        self.assertTrue(_same_origin_request({"Host": "127.0.0.1:8099"}))


if __name__ == "__main__":
    unittest.main()
