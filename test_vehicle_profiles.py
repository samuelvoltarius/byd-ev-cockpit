import tempfile
import unittest
from pathlib import Path
from vehicle_profiles import normalize_profile, read_profiles, write_profiles, combine_profiles


class ProfileTests(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vehicles.json"
            expected = [{"id": "audi1", "title": "Audi Q4", "brand": "Audi",
                         "source": "evcc", "external_id": "audi"}]
            self.assertEqual(read_profiles(path), [])
            self.assertEqual(write_profiles(path, expected), expected)
            self.assertEqual(read_profiles(path), expected)

    def test_no_credentials_in_profiles(self):
        p = normalize_profile({"id": "vw", "title": "VW ID.4",
                               "brand": "VW", "source": "evcc",
                               "password": "never-store"})
        self.assertNotIn("password", p)

    def test_capabilities_are_source_specific(self):
        saved = [
            {"id": "mybyd", "title": "BYD", "brand": "BYD", "source": "byd", "external_id": ""},
            {"id": "audi", "title": "Audi", "brand": "Audi", "source": "evcc", "external_id": "audi"},
        ]
        data = combine_profiles(saved, [{"id": "audi", "soc": 61}], {"soc": 75, "charging": "OFF"})
        self.assertEqual(data[0]["soc"], 75)
        self.assertTrue(data[0]["capabilities"]["remote_commands"])
        self.assertEqual(data[1]["soc"], 61)
        self.assertFalse(data[1]["capabilities"]["remote_commands"])


if __name__ == "__main__":
    unittest.main()
