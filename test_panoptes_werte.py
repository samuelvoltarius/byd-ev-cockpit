"""1.9.6: Reifendruck und Verbrauch kommen aus der Panoptes-Telemetrie; Unplausibles wird verworfen."""
import unittest

import panoptes_source as ps


class TestWerte(unittest.TestCase):
    def test_reifen_und_verbrauch(self):
        st = ps.aus_telemetrie({"soc": 66, "tyre_p_fl": 247, "tyre_p_fr": 242, "tyre_p_rl": "247", "tyre_p_rr": 247,
                                "consumption_50km": 16.3})
        self.assertEqual((st["tyre_fl"], st["tyre_fr"], st["tyre_rl"], st["tyre_rr"]), (247, 242, 247, 247))
        self.assertEqual(st["consumption_avg"], 16.3)

    def test_unplausibel_verworfen(self):
        st = ps.aus_telemetrie({"soc": 66, "tyre_p_fl": 0, "tyre_p_fr": 9999, "consumption_50km": 0, "tyre_p_rl": None})
        for k in ("tyre_fl", "tyre_fr", "tyre_rl", "consumption_avg"):
            self.assertNotIn(k, st)


if __name__ == "__main__":
    unittest.main()
