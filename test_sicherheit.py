"""Tests der Fernbefehl-Sperre (Vorfall 13.10.2026: Cloud-Befehl schaltete laufendes Auto ab)."""
import unittest

from sicherheit import befehl_erlaubt, FRISCH_S

T = 10_000.0


class TestSperre(unittest.TestCase):
    def ok(self, **z):
        return befehl_erlaubt(dict({"t": T}, **z), T + 5)[0]

    def test_panoptes_aus_erlaubt_an_gesperrt(self):
        self.assertTrue(self.ok(power_level=0, gear="P"))
        self.assertFalse(self.ok(power_level=2, gear="P"))          # der Fall vom 13.10.: P + an
        self.assertFalse(self.ok(power_level=1, gear="P"))          # ACC zaehlt als an

    def test_cloud_vehicle_state(self):
        self.assertTrue(self.ok(vehicle_state=0, gear="P", speed=0))
        self.assertFalse(self.ok(vehicle_state=2, gear="P"))
        self.assertFalse(self.ok(vehicle_state=-1))                  # UNKNOWN

    def test_panoptes_hat_vorrang_vor_cloud(self):
        self.assertFalse(self.ok(power_level=2, vehicle_state=0))
        self.assertTrue(self.ok(power_level=0, vehicle_state=-1))

    def test_fahren_immer_gesperrt(self):
        for g in ("D", "R", "N", "d"):
            self.assertFalse(self.ok(power_level=0, gear=g))
        self.assertFalse(self.ok(power_level=0, gear="P", speed=3))

    def test_unbekannt_und_alt_gesperrt(self):
        self.assertFalse(self.ok())
        self.assertFalse(befehl_erlaubt({}, T)[0])
        self.assertFalse(befehl_erlaubt(None, T)[0])
        self.assertFalse(befehl_erlaubt({"t": T, "power_level": 0}, T + FRISCH_S + 1)[0])
        self.assertFalse(self.ok(power_level="kaputt", vehicle_state=None))


class TestStillerBeweis(unittest.TestCase):
    def test_letzte_regulaere_abfrage(self):
        from sicherheit import aus_letzter_abfrage
        st = {"quelle": "BYD-Cloud", "vehicle_state": 0, "_zustand_t": T, "gear": "P", "speed": 0}
        z = aus_letzter_abfrage(st, T + 60)
        self.assertEqual(z, {"t": T, "vehicle_state": 0, "gear": "P", "speed": 0})
        self.assertTrue(befehl_erlaubt(z, T + 60)[0])
        self.assertIsNone(aus_letzter_abfrage(st, T + FRISCH_S + 1))                 # zu alt -> frisch fragen
        self.assertIsNone(aus_letzter_abfrage(dict(st, vehicle_state=-1), T))         # UNKNOWN
        self.assertIsNone(aus_letzter_abfrage(dict(st, vehicle_state=None), T))
        self.assertIsNone(aus_letzter_abfrage(dict(st, quelle="Home Assistant"), T))  # nur Cloud-Werte
        self.assertFalse(befehl_erlaubt(aus_letzter_abfrage(dict(st, vehicle_state=2), T), T)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
