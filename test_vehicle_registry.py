import unittest
from vehicle_registry import normalize_vehicles


class VehicleRegistryTests(unittest.TestCase):
    def test_multiple_brands_and_loadpoints(self):
        state = {
            "vehicles": {
                "audi": {"title": "Audi Q4", "capacity": 77},
                "vw": {"title": "VW ID.4", "capacity": 77},
                "byd": {"title": "BYD Dolphin"},
            },
            "loadpoints": [
                {"title": "Garage", "vehicleName": "audi", "vehicleSoc": 62,
                 "connected": True, "charging": True, "chargePower": 7200},
                {"title": "Carport", "vehicleName": "vw", "vehicleSoc": 34,
                 "connected": True, "charging": False, "chargePower": 0},
            ],
        }
        vehicles = {v["id"]: v for v in normalize_vehicles(state)}
        self.assertEqual(len(vehicles), 3)
        self.assertEqual(vehicles["audi"]["soc"], 62)
        self.assertEqual(vehicles["vw"]["loadpoint"], "Carport")
        self.assertIsNone(vehicles["byd"]["loadpoint"])

    def test_unconfigured_vehicle_on_loadpoint(self):
        result = normalize_vehicles({"loadpoints": [{"vehicleName": "other", "vehicleSoc": 50}]})
        self.assertEqual(result[0]["id"], "other")
        self.assertEqual(result[0]["soc"], 50)


if __name__ == "__main__":
    unittest.main()
