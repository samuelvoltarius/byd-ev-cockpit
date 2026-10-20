import unittest

from evcockpit import _auth_failure, _friendly


class AuthSafetyTests(unittest.TestCase):
    def test_byd_3002_is_blocking(self):
        error = RuntimeError("Login failed: code=3002 message=wrong password")
        self.assertTrue(_auth_failure(error))
        self.assertIn("Automatische Versuche wurden gestoppt", _friendly(error))

    def test_transient_error_does_not_block_login(self):
        self.assertFalse(_auth_failure(TimeoutError("timed out")))


if __name__ == "__main__":
    unittest.main()
