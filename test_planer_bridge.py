"""Tests der Planer-Anbindung (kein Netz)."""
import json
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
            if pfad == "modell-verbrauch":
                return 200, {"ok": True, "modell_kwh": 7.5, "akku_kwh": 43.2}
            return 200, {"ok": True}
        self.lokal = {}

        def speichern(d):
            self.lokal = json.loads(json.dumps(d))
        self.b = pb.Bruecke(anfrage=anfrage, uhr=lambda: self.t[0],
                            speicher=(lambda: json.loads(json.dumps(self.lokal)), speichern))
        self.cfg = {"planer": True, "planer_token": TOK, "planer_fahrten": True,
                    "planer_fahrzeug": "BYD Dolphin Surf Comfort", "planer_auto": "evc-1a2b3c4d"}

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

    def fahre_eine_fahrt(self, cfg=None):
        cfg = cfg or self.cfg
        km, soc = 1000.0, 80.0
        for _ in range(3):
            self.b.nach_abfrage(cfg, {"online": "OFF", "soc": soc, "odometer": km}); self.t[0] += 300
        while km < 1050:
            km += 3; soc -= 0.4
            self.b.nach_abfrage(cfg, {"online": "ON", "soc": round(soc), "odometer": km, "temp_out": 12})
            self.t[0] += 90
        for _ in range(3):
            self.b.nach_abfrage(cfg, {"online": "ON", "soc": round(soc), "odometer": km}); self.t[0] += 300

    def test_fahrt_bleibt_lokal_nur_faktor_geht_raus(self):
        self.fahre_eine_fahrt()
        pfade = [c[0] for c in self.calls]
        self.assertNotIn("fahrt", pfade)                    # 410 seit 21.10. - nie mehr senden
        frage = [c[2] for c in self.calls if c[0] == "modell-verbrauch"]
        self.assertEqual(len(frage), 1)
        self.assertEqual(frage[0]["fahrzeug"], "BYD Dolphin Surf Comfort")
        for k in ("soc_start", "soc_ende", "lat", "lon"):
            self.assertNotIn(k, frage[0])                   # nur km/dauer/temp
        faktor = [c[2] for c in self.calls if c[0] == "mein-faktor"]
        self.assertEqual(len(faktor), 1)
        self.assertEqual(faktor[0]["fahrten"], 1)
        self.assertEqual(faktor[0]["quelle"], "ev-cockpit")
        self.assertEqual(faktor[0]["auto"], "evc-1a2b3c4d")
        self.assertTrue(pb.FAKTOR_MIN <= faktor[0]["faktor"] <= pb.FAKTOR_MAX)
        self.assertEqual(len(self.lokal["BYD Dolphin Surf Comfort"]), 1)   # Verhaeltnis bleibt lokal
        self.assertEqual(self.b.status["fahrten"], 1)

    def test_soc_traegt_auto_kennung(self):
        self.b.nach_abfrage(self.cfg, {"online": "ON", "soc": 50})
        self.assertEqual(self.calls[0][2], {"soc": 50.0, "quelle": "ev-cockpit", "auto": "evc-1a2b3c4d"})

    def test_soc_mit_anzeigename(self):
        self.b.nach_abfrage(dict(self.cfg, model="BYD Dolphin Surf (Comfort, 43,2 kWh) mit sehr langem Namen"),
                            {"online": "ON", "soc": 50})
        self.assertEqual(self.calls[0][2]["auto_name"], "BYD Dolphin Surf (Comfort, 43,")   # max. 30 Zeichen
        self.assertNotIn("vin", self.calls[0][2])

    def test_mit_panoptes_meldet_das_cockpit_nichts(self):
        cfg = dict(self.cfg, panoptes=True, panoptes_url="http://auto:8180", panoptes_code="123456")
        self.b.nach_abfrage(cfg, {"online": "ON", "soc": 50})
        self.fahre_eine_fahrt(cfg)
        self.assertEqual(self.calls, [])
        self.assertTrue(self.b.status["panoptes"])


    def test_fahrten_ohne_eigenes_haekchen_nicht(self):
        cfg = dict(self.cfg, planer_fahrten=False)
        km = 1000.0
        for i in range(30):
            self.b.nach_abfrage(cfg, {"online": "ON", "soc": 80 - i // 3, "odometer": km}); km += 3 if 2 < i < 25 else 0
            self.t[0] += 120
        self.assertEqual([c for c in self.calls if c[0] in ("fahrt", "modell-verbrauch", "mein-faktor")], [])


class TestRoute(unittest.TestCase):
    PLAN = {"titel": "Salzburg → Wien", "km": 302.7, "minuten": 161, "soc_ankunft": 18, "erstellt": "2026-10-21T08:00:00Z",
            "schon_abgeholt": True, "stopps": [{"name": "A"}, {"name": "B"}], "geometrie": [[47.8, 13.0]] * 50}

    def test_route_mit_status(self):
        calls = []

        def anfrage(pfad, token, daten=None):
            calls.append(pfad)
            if pfad.startswith("meine-route"):
                return 200, {"ok": True, "plan": dict(self.PLAN, status={"status": "navigation", "stopp": 1})}
            return 404, {}
        r = pb.route_kurz(TOK, "evc-1a2b3c4d", anfrage=anfrage)
        self.assertEqual(calls, ["meine-route?auto=evc-1a2b3c4d"])
        self.assertEqual(r, {"titel": "Salzburg → Wien", "km": 302.7, "minuten": 161, "stopps": 2, "soc_ankunft": 18,
                             "erstellt": "2026-10-21T08:00:00Z", "abgeholt": True, "status": "Navigation läuft", "stopp": 1})
        self.assertNotIn("geometrie", r)                 # nur das Noetige fuer die Startseite

    def test_status_extra_abfragen_und_keine_route(self):
        def anfrage(pfad, token, daten=None):
            if pfad.startswith("meine-route"):
                return 200, {"ok": True, "plan": self.PLAN}
            return 200, {"ok": True, "status": {"status": "angenommen", "stopp": 0}}
        self.assertEqual(pb.route_kurz(TOK, anfrage=anfrage)["status"], "im Auto angekommen")
        self.assertIsNone(pb.route_kurz(TOK, anfrage=lambda p, t, d=None: (200, {"ok": True, "plan": None})))
        with self.assertRaises(RuntimeError):
            pb.route_kurz(TOK, anfrage=lambda p, t, d=None: (401, {}))


class TestFaktor(unittest.TestCase):
    def test_schrumpfung_und_grenzen(self):
        self.assertEqual(pb.faktor_aus([]), 1.0)
        self.assertAlmostEqual(pb.faktor_aus([1.2]), 1.0 + 0.2 * 1 / 5)
        self.assertAlmostEqual(pb.faktor_aus([1.1, 1.3]), 1.0 + 0.2 * 2 / 6)
        self.assertEqual(pb.faktor_aus([2.5] * 100), pb.FAKTOR_MAX)
        self.assertEqual(pb.faktor_aus([0.4] * 100), pb.FAKTOR_MIN)

    def test_kennung_zufaellig_ohne_vin(self):
        a, b = pb.neue_auto_kennung(), pb.neue_auto_kennung()
        self.assertNotEqual(a, b)
        self.assertRegex(a, r"^evc-[0-9a-f]{8}$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
