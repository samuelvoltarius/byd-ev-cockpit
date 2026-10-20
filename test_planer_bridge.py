"""Tests der Planer-Anbindung (kein Netz)."""
import unittest

import planer_bridge as pb

TOK = "0123456789abcdef0123456789abcdef"


class TestToken(unittest.TestCase):
    def test_aus_link_und_nackt(self):
        self.assertEqual(pb.token_aus_link("https://byd.serveone.at/ev/#z=" + TOK), TOK)
        self.assertEqual(pb.token_aus_link("  " + TOK.upper() + " "), TOK)
        self.assertEqual(pb.token_aus_link("https://byd.serveone.at/ev/"), "")
        self.assertEqual(pb.token_aus_link(""), "")
        self.assertEqual(pb.oeffnen_url(TOK), "https://byd.serveone.at/ev/#z=" + TOK)


class TestProfil(unittest.TestCase):
    P = [{"name": "BYD Dolphin Surf Comfort", "akku_kwh": 43.2}, {"name": "BYD Dolphin Surf Active 30 kWh", "akku_kwh": 30},
         {"name": "BYD Dolphin 60,4 kWh (Comfort/Design)", "akku_kwh": 60.4}, {"name": "BYD Seal 82,5 kWh Design RWD", "akku_kwh": 82.5}]

    def test_modell_und_akku(self):
        self.assertEqual(pb.passendes_profil(self.P, "BYD Dolphin Surf", 43.2), "BYD Dolphin Surf Comfort")
        self.assertEqual(pb.passendes_profil(self.P, "BYD Dolphin Surf", 30), "BYD Dolphin Surf Active 30 kWh")
        self.assertEqual(pb.passendes_profil(self.P, "BYD Seal", 82.5), "BYD Seal 82,5 kWh Design RWD")
        self.assertEqual(pb.passendes_profil(self.P, "Tesla Model 3", 60), "")


class TestFahrtenschreiber(unittest.TestCase):
    def fahre(self, punkte):
        f, aus = pb.Fahrtenschreiber(), []
        for p in punkte:
            r = f.neu(*p)
            if r:
                aus.append(r)
        return aus

    def test_normale_fahrt(self):
        # (t, km, soc, laedt, temp): geparkt, 40 min Fahrt (Abfrage alle 90 s grob), geparkt
        p = [(0, 1000, 80, False, 10), (300, 1000, 80, False, 10)]
        t, km, soc = 600, 1000.0, 80.0
        while km < 1060:
            km += 2.4; soc -= 0.3; p.append((t, round(km, 1), round(soc), False, 9)); t += 90
        p += [(t, round(km, 1), round(soc), False, 9), (t + 300, round(km, 1), round(soc), False, 9)]
        r = self.fahre(p)
        self.assertEqual(len(r), 1)
        self.assertAlmostEqual(r[0]["km"], 60.0, delta=1.0)
        self.assertTrue(30 <= r[0]["dauer_min"] <= 45, r[0])
        self.assertEqual(r[0]["soc_start"], 80)
        self.assertLess(r[0]["soc_ende"], 80)
        self.assertEqual(r[0]["temp_c"], 9)

    def test_laden_unterwegs_verwirft(self):
        p = [(0, 1000, 50, False, None), (100, 1010, 48, False, None), (200, 1030, 45, False, None),
             (300, 1030, 46, True, None), (400, 1030, 60, True, None), (500, 1040, 59, False, None),
             (600, 1040, 59, False, None), (700, 1040, 59, False, None)]
        self.assertEqual(self.fahre(p), [])

    def test_kurze_fahrt_wird_nicht_gemeldet(self):
        p = [(0, 1000, 50, False, None), (600, 1005, 49, False, None), (1200, 1005, 49, False, None),
             (1800, 1005, 49, False, None)]
        self.assertEqual(self.fahre(p), [])

    def test_fehlende_werte_stoeren_nicht(self):
        f = pb.Fahrtenschreiber()
        self.assertIsNone(f.neu(0, None, 50, False))
        self.assertIsNone(f.neu(10, 1000, None, False))


class TestBruecke(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.t = [1000.0]

        def anfrage(pfad, token, daten=None):
            self.calls.append((pfad, token, daten))
            return 200, {"ok": True, "verbrauch_kwh_100km": 17.0}
        self.b = pb.Bruecke(anfrage=anfrage, uhr=lambda: self.t[0])
        self.cfg = {"planer": True, "planer_token": TOK, "planer_fahrten": True,
                    "planer_fahrzeug": "BYD Dolphin Surf Comfort"}

    def test_ohne_haekchen_nichts(self):
        self.b.nach_abfrage({"planer": False, "planer_token": TOK}, {"online": "ON", "soc": 50})
        self.b.nach_abfrage({"planer": True, "planer_token": ""}, {"online": "ON", "soc": 50})
        self.assertEqual(self.calls, [])

    def test_soc_nur_bei_aenderung_oder_takt(self):
        st = {"online": "ON", "soc": 50, "odometer": 1000}
        self.b.nach_abfrage(self.cfg, st)
        self.t[0] += 300
        self.b.nach_abfrage(self.cfg, st)                  # gleich, zu frueh
        self.t[0] += 300
        self.b.nach_abfrage(self.cfg, dict(st, soc=52))    # geaendert
        self.t[0] += 1000
        self.b.nach_abfrage(self.cfg, dict(st, soc=52))    # Takt abgelaufen
        socs = [c[2]["soc"] for c in self.calls if c[0] == "mein-soc"]
        self.assertEqual(socs, [50.0, 52.0, 52.0])
        self.assertEqual(self.calls[0][1], TOK)

    def test_schlafendes_auto_kein_soc(self):
        self.b.nach_abfrage(self.cfg, {"online": "OFF", "soc": 50, "odometer": 1000})
        self.assertEqual([c for c in self.calls if c[0] == "mein-soc"], [])

    def test_fahrt_wird_mit_profil_gemeldet(self):
        km, soc = 1000.0, 80.0
        for _ in range(3):
            self.b.nach_abfrage(self.cfg, {"online": "OFF", "soc": soc, "odometer": km}); self.t[0] += 300
        while km < 1050:
            km += 3; soc -= 0.4
            self.b.nach_abfrage(self.cfg, {"online": "ON", "soc": round(soc), "odometer": km, "temp_out": 12})
            self.t[0] += 90
        for _ in range(3):
            self.b.nach_abfrage(self.cfg, {"online": "ON", "soc": round(soc), "odometer": km}); self.t[0] += 300
        fahrten = [c[2] for c in self.calls if c[0] == "fahrt"]
        self.assertEqual(len(fahrten), 1)
        self.assertEqual(fahrten[0]["fahrzeug"], "BYD Dolphin Surf Comfort")
        self.assertNotIn("lat", fahrten[0])
        self.assertEqual(self.b.status["fahrten"], 1)

    def test_fahrten_ohne_eigenes_haekchen_nicht(self):
        cfg = dict(self.cfg, planer_fahrten=False)
        km = 1000.0
        for i in range(30):
            self.b.nach_abfrage(cfg, {"online": "ON", "soc": 80 - i // 3, "odometer": km}); km += 3 if 2 < i < 25 else 0
            self.t[0] += 120
        self.assertEqual([c for c in self.calls if c[0] == "fahrt"], [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
