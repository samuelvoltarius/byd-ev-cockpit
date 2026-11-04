# -*- coding: utf-8 -*-
"""1.24 Planer-Ansicht (PLANER_VERTRAG.md, plan-ergebnis/1)."""
import os
import re
import unittest

import planer_ansicht as pa
import route_planer as rp

BEISPIEL = {
    "ok": True, "vertrag": "plan-ergebnis/1", "plan_id": "p_7f3a01", "erstellt": "2026-11-04T14:05:00Z", "gueltig_bis": "2026-11-04T16:05:00Z",
    "start": {"lat": 48.3064, "lon": 14.2861, "name": "Linz"}, "ziel": {"lat": 52.52, "lon": 13.405, "name": "Berlin"},
    "fahrzeug": {"name": "BYD Dolphin Surf", "akku_kwh": 43.2},
    "zeit": {"abfahrt_ca": "2026-11-04T14:10:00Z", "ankunft_ca": "2026-11-04T22:45:00Z", "fahr_min": 420, "lade_min": 95, "aufenthalt_min": 0,
             "gesamt_min": 515, "verkehr_min": 12, "inkl_verkehr": True},
    "akku": {"soc_start": 80, "soc_ankunft": 23, "reserve": 10}, "fahrbar": True, "nicht_fahrbar": None, "km": 731.6,
    "etappen": [
        {"nr": 1, "art": "laden", "name": "Lidl Regensburg", "lat": 49.0, "lon": 12.1, "km": 245.3, "ankunft_ca": "2026-11-04T17:00:00Z",
         "abfahrt_ca": "2026-11-04T17:28:00Z", "soc_an": 12, "soc_ab": 78, "lade_min": 28, "kwh": 29.1, "kw": 150, "cpo": "Lidl", "stecker": ["ccs"],
         "kosten": 13.95, "waehrung": "EUR", "bezahlen": {"karte": "Lidl Plus", "tarif": "App Deutschland", "eigene_karte": False, "adhoc": False,
                                                          "preis_stufe": "bestaetigt", "hinweis": "Preis laut Anbieter-Webseite"},
         "preis_unsicher": False, "live": {"frei": 2, "ladepunkte": 4, "stand_min": 3, "quelle": "MobiData BW"}, "geoeffnet_bei_ankunft": True, "umweg_km": 0.4},
        {"nr": 2, "art": "zwischenziel", "name": "Oma", "lat": 50.1, "lon": 12.5, "km": 400.0, "ankunft_ca": "2026-11-04T19:00:00Z",
         "abfahrt_ca": "2026-11-04T20:00:00Z", "aufenthalt_min": 60, "soc_an": 40, "soc_ab": 40, "laden": None}],
    "kosten": {"summe": 41.20, "sicher": 35.10, "unsicher": 6.10, "ohne_preis": 1, "waehrung": "EUR"},
    "verkehr": {"verzoegerung_min": 12, "eingerechnet": True, "quelle": "TomTom Traffic",
                "meldungen": [{"typ": "jam", "titel": "Stau", "km": 301.2, "verzoegerung_min": 8}]},
    "sperren": {"meldungen_n": 3, "voll_gesperrt_n": 0}, "warnungen": ["Achtung"], "hinweise": ["Schätzung: Regen"],
    "quellen": ["E-Control (AT)", "© OpenStreetMap-Mitwirkende (ODbL)"], "geometrie": [[48.3064, 14.2861], [52.52, 13.405]], "abweichung": {},
    "neues_feld_aus_spaeterer_version": {"x": 1}}


class TestErgebnis(unittest.TestCase):
    def test_beispiel_aus_dem_vertrag(self):
        e = pa.ergebnis(BEISPIEL)
        self.assertEqual(e["plan_id"], "p_7f3a01")
        self.assertEqual((e["zeit"]["verkehr_min"], e["zeit"]["inkl_verkehr"]), (12, True))
        self.assertEqual([x["art"] for x in e["etappen"]], ["laden", "zwischenziel"])
        l = e["etappen"][0]
        self.assertEqual((l["soc_an"], l["soc_ab"], l["kosten"], l["karte"]), (12, 78, 13.95, "Lidl Plus"))
        self.assertEqual(l["live"], {"frei": 2, "ladepunkte": 4, "stand_min": 3, "quelle": "MobiData BW"})
        self.assertEqual(e["kosten"]["summe"], 41.2)
        self.assertEqual(e["verkehr"]["meldungen"][0]["titel"], "Stau")
        self.assertEqual(e["quellen"][1], "© OpenStreetMap-Mitwirkende (ODbL)")
        self.assertNotIn("neues_feld_aus_spaeterer_version", e)             # unbekannte Felder ignorieren

    def test_unbekanntes_bleibt_none(self):
        e = pa.ergebnis({"vertrag": "plan-ergebnis/1", "plan_id": "nicht gueltig", "etappen": [{"art": "laden", "kosten": None, "live": None}],
                         "zeit": {"ankunft_ca": "morgen"}, "verkehr": None})
        self.assertIsNone(e["plan_id"])
        self.assertIsNone(e["etappen"][0]["kosten"])
        self.assertIsNone(e["etappen"][0]["live"])
        self.assertIsNone(e["zeit"]["ankunft_ca"])
        self.assertIsNone(e["verkehr"])

    def test_nicht_fahrbar(self):
        d = dict(BEISPIEL, fahrbar=False, nicht_fahrbar={"von_km": 120, "bis_km": 260, "text": "Keine Säule zwischen km 120 und 260."})
        e = pa.ergebnis(d)
        self.assertFalse(e["fahrbar"])
        self.assertEqual(pa.reicht(e), {"stufe": "nein", "satz": "Keine Säule zwischen km 120 und 260."})

    def test_reicht(self):
        r = pa.reicht(pa.ergebnis(BEISPIEL))
        self.assertEqual((r["stufe"], r["an"], r["n"]), ("ja", 23, 1))
        knapp = dict(BEISPIEL, akku={"soc_start": 80, "soc_ankunft": 6, "reserve": 10})
        self.assertEqual(pa.reicht(pa.ergebnis(knapp))["stufe"], "knapp")
        self.assertEqual(pa.reicht(pa.ergebnis(dict(BEISPIEL, akku={})))["stufe"], "unbekannt")

    def test_alte_form_wird_umgerechnet(self):
        k = rp.kurz({"route": {"km": 281, "minuten": 165, "geometrie": [[48.3, 14.3], [47.0, 15.4]]}, "soc_start": 80, "soc_ankunft": 21,
                     "stopps": [{"saeule": {"name": "IONITY", "lat": 47.3, "lon": 14.7, "km_auf_route": 160, "kw": 350}, "soc_vorher": 14,
                                 "soc_nachher": 70, "ladedauer_min": 25, "kwh": 24, "kosten_beste_option": 9.4}],
                     "kosten": {"basis": {"gesamt": 9.4}}, "fahrzeug": {"name": "BYD"}})
        e = pa.aus_alt(k, "Salzburg", "Graz")
        self.assertIsNone(e["vertrag"])
        self.assertIsNone(e["plan_id"])
        self.assertEqual((e["etappen"][0]["soc_an"], e["etappen"][0]["kosten"], e["ziel"]["name"]), (14, 9.4, "Graz"))
        self.assertEqual(pa.reicht(e)["stufe"], "ja")


class TestBremse(unittest.TestCase):
    def test_zehn_je_minute_und_nur_eine_gleichzeitig(self):
        t = [1000.0]
        b = pa.Bremse(uhr=lambda: t[0])
        self.assertIsNone(b.los())
        self.assertIn("läuft schon", b.los())                       # zweite Planung waehrend die erste laeuft
        b.fertig()
        for _ in range(9):
            self.assertIsNone(b.los()); b.fertig()
        self.assertIn("eine Minute", b.los())                        # 11. innerhalb einer Minute
        t[0] += 61
        self.assertIsNone(b.los()); b.fertig()


class TestPlanerAufrufe(unittest.TestCase):
    def test_kompakt_und_fehlercodes(self):
        gesehen = []

        def anfrage(pfad, tok, body, timeout=12):
            gesehen.append((pfad, body))
            return 429, {"ok": False, "code": "zu_oft", "fehler": "x"}
        with self.assertRaises(ValueError) as c:
            rp.planen_roh("g:" + "0" * 64, {"ausgabe": "kompakt"}, anfrage)
        self.assertEqual(str(c.exception), rp.CODE_TEXT["zu_oft"])
        self.assertEqual(gesehen[0][1]["ausgabe"], "kompakt")
        self.assertEqual(rp.planen_roh("t", {}, lambda *a, **k: (200, BEISPIEL)), BEISPIEL)

    def test_an_auto_mit_plan_id(self):
        gesendet = []
        ok = lambda pfad, tok, body, timeout=12: (gesendet.append((pfad, body)) or (200, {"ok": True, "gueltig_bis": "x"}))
        rp.an_auto_plan_id("t", "p_7f3a01", "a-1", ok)
        self.assertEqual(gesendet, [("an-auto", {"plan_id": "p_7f3a01", "auto": "a-1"})])
        with self.assertRaises(ValueError) as c:
            rp.an_auto_plan_id("t", "p_7f3a01", "", lambda *a, **k: (410, {"ok": False, "code": "plan_abgelaufen"}))
        self.assertIn("neu planen", str(c.exception))
        with self.assertRaises(ValueError):
            rp.an_auto_plan_id("t", "../x", "", ok)
        self.assertEqual(len(gesendet), 1)


class TestSeite(unittest.TestCase):
    def test_verdrahtet_und_regeln(self):
        src = open(os.path.join(os.path.dirname(__file__), "evcockpit.py"), encoding="utf-8").read()
        for x in ('"/routenplaner"', '"/rp/vorgaben"', '("/rp/plan", "/rp/an-auto")', 'body.update(ausgabe="kompakt", geometrie="kurz")', "_RP_BREMSE.los()"):
            self.assertIn(x, src)
        s = pa.SEITE
        self.assertIn("q.length<3", s)                               # Ortssuche ab 3 Zeichen
        self.assertIn(",300)", s)                                    # und 300 ms Pause
        self.assertNotIn("setInterval", s)                           # nie automatisch planen
        self.assertNotIn("navigator.geolocation", s)                 # nie die Ortung des PCs
        self.assertIn("p_quellen", s)                                # Pflicht-Namensnennungen
        self.assertIn('href="/routenplaner"', __import__("neu_look").hub_html("1"))

    def test_englisch(self):
        import evcockpit as ev
        for t in re.findall(r"__T\('([^']+)'\)", pa.SEITE):
            self.assertIn(t, ev._I18N, t)


if __name__ == "__main__":
    unittest.main()
