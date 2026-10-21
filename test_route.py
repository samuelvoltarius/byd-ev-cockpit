"""1.10: Route-Reiter - Start = Autoposition, nur auf Klick, flache Form fuer an-auto, ehrliche Oeffnungszeiten."""
import os
import unittest

import route_planer as rp

PLAN = {"route": {"km": 199.4, "minuten": 128, "geometrie": [[48.2, 16.36], [47.6, 15.8], [47.07, 15.43]]},
        "fahrzeug": {"name": "BYD Dolphin Surf"}, "soc_start": 71, "soc_ankunft": 22.4, "modus": "kompromiss",
        "stopps": [{"saeule": {"name": "Lidl Gleisdorf", "betreiber": "Lidl", "lat": 47.1, "lon": 15.7, "kw": 150,
                               "km_auf_route": 160, "offen": {"bis": "22:00"}},
                    "soc_vorher": 18, "soc_nachher": 60, "ladedauer_min": 21, "kwh": 18.5, "kosten_beste_option": 7.2,
                    "mit_eigener_karte": True},
                   {"saeule": {"name": "Ohne Angabe", "lat": 47.2, "lon": 15.6, "kw": 50}, "soc_vorher": 30,
                    "soc_nachher": 50, "ladedauer_min": 9}],
        "kosten": {"basis": {"gesamt": 9.9}}, "warnungen": ["Stau A2"]}


class Fake:
    def __init__(self, antworten):
        self.antworten, self.aufrufe = antworten, []

    def __call__(self, pfad, token, daten=None, timeout=12):
        self.aufrufe.append((pfad, daten))
        return self.antworten.get(pfad, (404, {}))


class TestRoute(unittest.TestCase):
    def test_start_ist_autoposition(self):
        b = rp.anfrage_body({"ziel": [47.07, 15.43]}, (48.2063, 16.3655), 71, "BYD Dolphin Surf", "a-1")
        self.assertEqual((b["start"], b["soc_start"], b["fahrzeug"], b["auto"]), ([48.2063, 16.3655], 71, "BYD Dolphin Surf", "a-1"))
        b = rp.anfrage_body({"start": [47.0, 15.0], "ziel": [47.07, 15.43], "soc_start": "55"}, (48.2, 16.3), 71, "X")
        self.assertEqual((b["start"], b["soc_start"]), ([47.0, 15.0], 55))
        with self.assertRaises(ValueError):
            rp.anfrage_body({"ziel": [47.07, 15.43]}, None, 71, "X")       # weder Auto noch eigener Start
        with self.assertRaises(ValueError):
            rp.anfrage_body({"ziel": [0, 0]}, (48.2, 16.3), 71, "X")
        self.assertEqual(rp.anfrage_body({"ziel": [1, 2], "modus": "rm -rf"}, (3, 4), None, "X")["modus"], "kompromiss")

    def test_kurz_und_oeffnung(self):
        f = Fake({"plan": (200, PLAN)})
        k = rp.planen("g:" + "a" * 64, {"start": [1, 2]}, anfrage=f)
        self.assertEqual(f.aufrufe[0][0], "plan")
        self.assertEqual((k["km"], k["soc_ankunft"], k["kosten"], k["lade_min"]), (199.4, 22.4, 9.9, 30))
        self.assertEqual([s["oeffnung"] for s in k["stopps"]], ["offen bis 22:00", "Öffnungszeit unbekannt"])
        self.assertTrue(k["stopps"][0]["eigene_karte"])

    def test_fehler_ehrlich(self):
        with self.assertRaises(ValueError):
            rp.planen("t", {}, anfrage=Fake({"plan": (200, {"fehler": "kein Fahrzeugprofil hinterlegt"})}))
        with self.assertRaisesRegex(ValueError, "Minute"):
            rp.planen("t", {}, anfrage=Fake({"plan": (429, {})}))

    def test_an_auto_flach(self):
        k = rp.kurz(PLAN)
        p = rp.fuer_auto(k, [48.2, 16.36], [47.07, 15.43], "Mein Auto", "Graz", "BYD Dolphin Surf")
        self.assertEqual(len(p["geometrie"]), 3)
        self.assertEqual(set(p["stopps"][0]), {"lat", "lon", "name", "km", "kw", "cpo", "soc_an", "soc_ab", "dauer_min", "kwh", "preis"})
        self.assertNotIn("preis", p["stopps"][1])
        self.assertEqual(p["titel"], "Mein Auto → Graz")
        f = Fake({"an-auto": (200, {"ok": True, "gueltig_bis": "x"})})
        rp.an_auto("t", p, "a-1", anfrage=f)
        self.assertEqual(f.aufrufe[0][1]["auto"], "a-1")

    def test_ortssuche(self):
        f = Fake({"orte": (200, {"orte": [{"name": "Graz", "lat": 47.07, "lon": 15.43}]})})
        self.assertEqual(rp.orte("t", "Gr", anfrage=f), [])                 # unter 3 Zeichen: gar nicht fragen
        self.assertEqual(f.aufrufe, [])
        self.assertEqual(rp.orte("t", "Graz", anfrage=f)[0]["name"], "Graz")
        f = Fake({"ziel-aus-text": (200, {"ok": True, "ort": {"lat": 47.0, "lon": 15.0, "name": "Pin"}})})
        self.assertEqual(rp.orte("t", "https://maps.example/x", anfrage=f)[0]["name"], "Pin")

    def test_koordinaten_nie_in_der_url(self):
        q = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "route_planer.py"), encoding="utf-8").read()
        self.assertNotIn("?start", q)
        self.assertNotIn("?ziel", q)
        e = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()
        self.assertIn("Start und Ziel gehen nur beim Klick auf „Route berechnen“", e)
        self.assertIn("Am Fahrzeug wird nichts ausgelöst", e)

    def test_planer_haengt_nicht_still(self):
        for code in (502, 503, 504):
            with self.assertRaisesRegex(ValueError, "neu gestartet oder ist ausgelastet"):
                rp.planen("t", {}, anfrage=Fake({"plan": (code, {})}), warte=lambda s: None)

    def test_503_einmal_wiederholen(self):
        antworten = [(503, {}), (200, PLAN)]
        gewartet = []
        k = rp.planen("t", {}, anfrage=lambda *a, **kw: antworten.pop(0), warte=gewartet.append)
        self.assertEqual((k["km"], gewartet), (199.4, [2]))
        import socket

        def zu_langsam(*a, **k):
            raise socket.timeout("timed out")
        with self.assertRaisesRegex(ValueError, "nicht geantwortet"):
            rp.planen("t", {}, anfrage=zu_langsam)
        e = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()
        self.assertIn("setTimeout(()=>ab.abort(),100000)", e)             # der Browser wartet nie endlos
        self.assertGreaterEqual(rp.PLAN_TIMEOUT, 90)                         # Proxy nie kuerzer als der Planer braucht

    def test_grund_statt_typname(self):
        import socket, urllib.error
        self.assertIn("zu langsam", rp.grund(socket.timeout()))
        self.assertIn("zu langsam", rp.grund(urllib.error.URLError(socket.timeout())))
        self.assertIn("startet gerade neu", rp.grund(RuntimeError("Planer antwortet 503")))
        self.assertIn("Fehler 500", rp.grund(RuntimeError("Planer antwortet 500")))
        self.assertIn("Internet", rp.grund(urllib.error.URLError(ConnectionRefusedError())))
        e = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()
        self.assertNotIn('fehler="Planer nicht erreichbar', e)              # Fehler werden nicht mehr zwischengespeichert

    def test_vertrag_10_ladenetze_und_oeffnung(self):
        d = dict(PLAN, filter={"bevorzugt": ["LIDL_AT"], "netze_modus": "nur", "umweg_max_min": 10, "nur_offen": True})
        d["stopps"] = [dict(PLAN["stopps"][0], oeffnung_text="Mi 05:00–22:00", geoeffnet_bei_ankunft=False, bevorzugtes_netz=True)]
        k = rp.kurz(d)
        self.assertEqual(k["vorlieben"], {"netze": ["LIDL_AT"], "modus": "nur", "umweg_min": 10, "nur_offen": True})
        self.assertEqual((k["stopps"][0]["oeffnung"], k["stopps"][0]["geschlossen"], k["stopps"][0]["bevorzugt"]),
                         ("Mi 05:00–22:00", True, True))
        self.assertIsNone(rp.kurz(dict(PLAN, filter={"bevorzugt": [], "nur_offen": False}))["vorlieben"])

    def test_karte_preis_quelle_je_stopp(self):
        d = dict(PLAN, kosten={"basis": {"gesamt": 9.9, "beschreibung": "bester Mix aus deinen Karten",
                                         "wahl": [{"stopp": 0, "gewaehlt": "Lidl Plus", "tarif_id": 4, "preis_kwh": 0.29,
                                                   "herkunft": {"stufe": "bestaetigt", "text": "bestaetigt, geprueft heute"}}]}})
        d["stopps"] = [dict(PLAN["stopps"][0], zahlungsarten=[{"tarif_id": 4, "msp": "Lidl", "tarif": "Plus", "preis_kwh": 0.29}]),
                       dict(PLAN["stopps"][1], zahlungsarten=[{"tarif_id": 9, "msp": "IONITY", "tarif": "Direkt", "preis_kwh": 0.69,
                                                               "herkunft": {"text": "laut Website"}}])]
        k = rp.kurz(d)
        self.assertEqual((k["stopps"][0]["karte"], k["stopps"][0]["preis_kwh"], k["stopps"][0]["preis_quelle"]),
                         ("Lidl Plus", 0.29, "bestaetigt, geprueft heute"))
        self.assertEqual((k["stopps"][1]["karte"], k["stopps"][1]["preis_kwh"], k["stopps"][1]["preis_quelle"]),
                         ("IONITY Direkt", 0.69, "laut Website"))                 # ohne Wahl: erste Zahlungsart
        self.assertEqual((k["kosten"], k["kosten_text"]), (9.9, "bester Mix aus deinen Karten"))

    def test_abfahrt_und_zwischenstopps(self):
        w = {"ziel": [47.07, 15.43], "abfahrt": "2026-10-22T12:00:00+02:00",
             "via": [{"lat": 47.8, "lon": 14.6, "name": "Kirchdorf", "aufenthalt_min": 20}, {"lat": 47.5, "lon": 14.9}]}
        b = rp.anfrage_body(w, (48.3, 14.28), 40, "X")
        self.assertEqual(b["abfahrt"], "2026-10-22T12:00:00+02:00")
        self.assertEqual(b["via"], [{"lat": 47.8, "lon": 14.6, "name": "Kirchdorf", "aufenthalt_min": 20}, {"lat": 47.5, "lon": 14.9, "name": ""}])
        self.assertNotIn("abfahrt", rp.anfrage_body({"ziel": [1, 2], "abfahrt": "morgen; rm"}, (3, 4), 40, "X"))
        self.assertEqual(len(rp.anfrage_body({"ziel": [1, 2], "via": [{"lat": 1, "lon": 1}] * 9}, (3, 4), 40, "X")["via"]), 5)
        with self.assertRaises(ValueError):
            rp.anfrage_body({"ziel": [1, 2], "via": [{"lat": "x"}]}, (3, 4), 40, "X")

    def test_fahrtplan_und_zwischenziele(self):
        d = dict(PLAN, fahrtplan={"abfahrt_ca": "2026-10-22T10:00:00Z", "ankunft_ca": "2026-10-22T13:32:50Z", "gesamt_min": 213, "geheim": 1},
                 zwischenziele=[{"nr": 1, "name": "Kirchdorf", "ankunft_ca": "2026-10-22T11:50:07Z", "aufenthalt_min": 20, "lat": 47.8}])
        k = rp.kurz(d)
        self.assertEqual((k["fahrtplan"]["ankunft_ca"], k["fahrtplan"]["gesamt_min"]), ("2026-10-22T13:32:50Z", 213))
        self.assertNotIn("geheim", k["fahrtplan"])
        self.assertEqual(k["zwischenziele"][0]["name"], "Kirchdorf")
        self.assertNotIn("lat", k["zwischenziele"][0])                      # nur was die Anzeige braucht
        self.assertIsNone(rp.kurz(PLAN)["fahrtplan"])

    LADEN = {"ok": True, "version": 1, "quelle": "auto", "stand": "2026-10-22T08:00:00Z",
             "laden": {"karten": [{"id": 4, "anzeige": "Fastned · Gold"}], "nurMeineKarten": False,
                       "netze": [{"cpo": "Lidl", "anzeige": "Lidl"}], "netzeModus": "nur", "umwegMaxMin": 10, "nurOffen": True,
                       "ankunftSocMin": 20},
             "planer": {"karten": [4], "nur_meine_karten": 0, "soc_ziel_min": 20,
                        "filter": {"bevorzugt": ["Lidl"], "netze_modus": "nur", "umweg_max_min": 10, "nur_offen": True, "ausschluss": []},
                        "vorlieben_quelle": "auto"}}

    def test_laden_stueck_unveraendert_im_plan(self):
        b = rp.mit_laden({"start": [1, 2], "ziel": [3, 4], "soc_ziel_min": 15}, self.LADEN)
        self.assertEqual(b["filter"], self.LADEN["planer"]["filter"])          # keine eigene Umrechnung
        self.assertEqual((b["karten"], b["vorlieben_quelle"]), ([4], "auto"))
        self.assertEqual(b["soc_ziel_min"], 15)                                # das Feld im Route-Reiter gilt

    def test_ohne_planer_stueck_wie_bisher(self):
        body = {"start": [1, 2], "ziel": [3, 4]}
        self.assertEqual(rp.mit_laden(body, dict(self.LADEN, planer=None, quelle="standard")), body)
        self.assertEqual(rp.mit_laden(body, {}), body)
        self.assertNotIn("filter", rp.mit_laden(body, None))                   # kein leeres filter.bevorzugt

    def test_laden_lesen_vor_0110(self):
        import urllib.error

        class Pv:
            def _get(self, pfad):
                raise urllib.error.HTTPError("u", 404, "nf", {}, None)
        self.assertIsNone(rp.laden_lesen(Pv()))

    def test_laden_anzeige(self):
        a = rp.laden_anzeige(self.LADEN)
        self.assertEqual((a["quelle"], a["karten"], a["netze"], a["modus"], a["ankunft"]), ("auto", ["Fastned · Gold"], ["Lidl"], "nur", 20))


if __name__ == "__main__":
    unittest.main()
