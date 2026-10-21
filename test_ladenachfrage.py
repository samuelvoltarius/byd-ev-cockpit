"""1.13: Ladenachfrage aus dem Auto anzeigen und beantworten (LADENACHFRAGE_VERTRAG GEBAUT)."""
import unittest
import urllib.error

import ladenachfrage as ln
import route_planer as rp

ROH = {"ok": True, "an": True, "anzahl": 2, "spaeter": 0, "jetztZeigen": False, "offen": [
    {"id": 7, "start": 1792600000000, "ende": 1792603600000, "kwh": 31.24, "dc": True, "quelle": "fehlt", "spaeter": False,
     "lat": 47.1, "lng": 15.4, "ort": {"bekannt": True, "name": "Lidl <b>Graz</b>"},
     "vorschlaege": [{"art": "ortskreis", "tarifId": "t1", "name": "Lidl Graz", "preisKwh": 0.35},
                     {"art": "planer_stopp", "name": "IONITY", "cpo": "IONITY", "preisKwh": None}],
     "auswahl": [{"art": "karte", "id": 4, "anzeige": "Fastned Gold", "preisKwh": None}, {"art": "adhoc", "preisKwh": None},
                 {"art": "zuhause", "preisKwh": 0.3}, {"art": "zuhause_gratis", "preisKwh": 0, "vorgeschlagen": True}]},
    {"id": 8, "start": 1792500000000, "kwh": 9.0, "dc": None, "ort": {"bekannt": False}, "vorschlaege": [], "auswahl": []}]}


class TestAnzeige(unittest.TestCase):
    def test_ohne_koordinaten_und_gekuerzt(self):
        a = ln.anzeige(ROH)
        self.assertEqual(a["anzahl"], 2)
        e = a["offen"][0]
        self.assertNotIn("lat", e)
        self.assertNotIn("lat", str(a))
        self.assertEqual(e["ort"], "Lidl bGraz/b")
        self.assertEqual([x["art"] for x in e["auswahl"]], ["karte", "adhoc", "zuhause", "zuhause_gratis"])
        self.assertEqual(a["offen"][1]["ort"], "")
        self.assertIsNone(a["offen"][1]["dc"])

    def test_aelteres_panoptes(self):
        class Pv:
            def _get(self, pfad):
                raise urllib.error.HTTPError("u", 404, "nf", {}, None)
        self.assertIsNone(ln.lesen(Pv()))
        self.assertIsNone(ln.anzeige(None))


class TestAntwort(unittest.TestCase):
    def test_karte(self):
        self.assertEqual(ln.antwort_body({"id": "7", "art": "karte", "karteId": "4", "preisKwh": 0.59}),
                         {"id": 7, "art": "karte", "preisKwh": 0.59, "karteId": 4})

    def test_gratis_ohne_preis_und_ort_merken(self):
        b = ln.antwort_body({"id": 7, "art": "zuhause_gratis", "preisKwh": 9, "ort_merken": " Garage "})
        self.assertEqual(b, {"id": 7, "art": "zuhause_gratis", "ortMerken": {"name": "Garage", "radiusM": 100}})

    def test_ungueltig(self):
        for w in ({"id": 0, "art": "adhoc", "preisKwh": 1}, {"id": 7, "art": "boerse", "preisKwh": 1},
                  {"id": 7, "art": "adhoc"}, {"id": 7, "art": "adhoc", "preisKwh": -1}, {"id": 7, "art": "adhoc", "preisKwh": 9},
                  {"id": 7, "art": "adhoc", "preisKwh": "nan"}, {"id": 7, "art": "karte", "preisKwh": 0.5}):
            with self.assertRaises(ValueError):
                ln.antwort_body(w)

    def test_null_ist_gratis_erlaubt(self):
        self.assertEqual(ln.antwort_body({"id": 7, "art": "adhoc", "preisKwh": 0})["preisKwh"], 0)

    def test_ergebnis(self):
        self.assertEqual(ln.ergebnis({"ok": True, "ergebnisse": [{"id": 7, "hinweis": "zu_hoch"}], "ortMerken": "keine_position"})["hinweis"],
                         "Preis ungewöhnlich hoch – bitte prüfen · Ort nicht gemerkt: das Auto kennt die Position dieser Ladung nicht")
        r = ln.ergebnis({"ok": False, "fehler": {"preisKwh": "x"}, "_status": 400})
        self.assertFalse(r["ok"])
        self.assertIn("preisKwh", r["error"])
        self.assertEqual(ln.ergebnis({"_status": 409})["error"], "Die Ladung läuft noch")


class TestSenden(unittest.TestCase):
    def test_http_fehler_wird_antwort(self):
        import io
        import panoptes_source as ps

        def http(url, daten=None, jwt="", **k):
            raise urllib.error.HTTPError(url, 400, "bad", {}, io.BytesIO(b'{"ok":false,"fehler":{"preisKwh":"x"}}'))
        q = ps.Panoptes("http://x", "", jwt="j", http=http)
        self.assertEqual(q.senden("/api/laden/nachfrage", {"id": 1}), {"ok": False, "fehler": {"preisKwh": "x"}, "_status": 400})


class TestFahrzeug(unittest.TestCase):
    def test_wirksam_aus_dem_auto(self):
        self.assertEqual(rp.fahrzeug_aus_laden({"fahrzeug": {"gewaehlt": None, "wirksam": "BYD Dolphin Surf 43", "quelle": "erkannt"}}),
                         "BYD Dolphin Surf 43")
        self.assertIsNone(rp.fahrzeug_aus_laden({"fahrzeug": {"wirksam": None}}))
        self.assertIsNone(rp.fahrzeug_aus_laden(None))

    def test_null_fahrzeug_im_stueck_ueberschreibt_nicht(self):
        b = rp.mit_laden({"fahrzeug": "A"}, {"planer": {"fahrzeug": None, "karten": [1]}})
        self.assertEqual((b["fahrzeug"], b["karten"]), ("A", [1]))


class Pv:
    def __init__(self, antworten):
        self.a, self.pfade = antworten, []

    def _get(self, pfad):
        self.pfade.append(pfad)
        a = self.a(pfad) if callable(self.a) else self.a
        if isinstance(a, Exception):
            raise a
        return a


KOSTEN = {"ok": True, "zeitraum": "monat", "von": 1, "bis": 2, "km": 812.4, "kwh_geladen": 140.2, "kosten_summe": 31.5,
          "kosten_je_100km": 3.88, "kwh_je_100km": 16.1, "ladungen": 9, "ladungen_ohne_preis": 2, "gratis_ladungen": 4,
          "vollstaendig": False, "waehrung": "EUR"}


class TestKosten(unittest.TestCase):
    def setUp(self):
        ln._CACHE.clear()

    def test_durchgereicht_nichts_gerechnet(self):
        pv = Pv(KOSTEN)
        k = ln.kosten(pv, "30t")
        self.assertEqual(pv.pfade, ["/api/laden/kosten?zeitraum=30t"])
        self.assertEqual((k["kosten_je_100km"], k["kwh_je_100km"], k["vollstaendig"], k["ladungen_ohne_preis"]), (3.88, 16.1, False, 2))

    def test_zeitraum_nur_erlaubte(self):
        pv = Pv(KOSTEN)
        ln.kosten(pv, "x&zeitraum=jahr")
        self.assertEqual(pv.pfade, ["/api/laden/kosten?zeitraum=monat"])

    def test_cache_und_leeren(self):
        t = [1000.0]
        pv = Pv(KOSTEN)
        ln.kosten(pv, "monat", uhr=lambda: t[0])
        t[0] += 100
        ln.kosten(pv, "monat", uhr=lambda: t[0])
        self.assertEqual(len(pv.pfade), 1)
        ln.cache_leeren()
        ln.kosten(pv, "monat", uhr=lambda: t[0])
        self.assertEqual(len(pv.pfade), 2)

    def test_aelteres_panoptes_ausblenden(self):
        for fehler in (urllib.error.HTTPError("u", 404, "nf", {}, None), {"_status": 403}):
            ln._CACHE.clear()
            pv = Pv(fehler)
            self.assertEqual(ln.kosten(pv, "monat"), {"ok": False, "fehlt": True})
            ln.cache_leeren()                              # 'fehlt' bleibt eine Stunde gemerkt
            ln.kosten(pv, "monat")
            self.assertEqual(len(pv.pfade), 1)

    def test_null_bei_wenig_km(self):
        k = ln.kosten(Pv(dict(KOSTEN, km=0.4, kosten_je_100km=None, kwh_je_100km=None)), "jahr")
        self.assertIsNone(k["kosten_je_100km"])


class TestLadungen(unittest.TestCase):
    def setUp(self):
        ln._CACHE.clear()

    def test_liste_ohne_koordinaten(self):
        pv = Pv({"ok": True, "seite": 0, "mehr": True, "ladungen": [
            {"id": 5, "start": 1792651200000, "ende": 1792654800000, "dc": True, "kwh": 31.2, "rate": -1, "kosten": -1, "waehrung": "EUR",
             "quelle": "fehlt", "tarifName": None, "ort": None, "lat": 47.1, "lng": 15.4},
            {"id": 6, "start": 1792560000000, "dc": False, "kwh": 18.4, "rate": 0, "kosten": 0, "quelle": "tarif", "tarifName": "Zuhause", "ort": "Garage"}],
            "monate": [{"monat": "2026-10", "ladungen": 2, "kwh": 49.6, "kosten": 0, "ohne_preis": 1, "vollstaendig": False}]})
        d = ln.ladungen(pv, 0, jetzt_ms=1792700000000)
        self.assertTrue(pv.pfade[0].startswith("/api/laden/ladungen?von="))
        self.assertIn("seite=0&anzahl=50", pv.pfade[0])
        self.assertNotIn("lat", str(d))
        a, b = d["ladungen"]
        self.assertEqual((a["rate"], a["kosten"], a["quelle"], a["ort"]), (None, None, "fehlt", ""))
        self.assertEqual((b["kosten"], b["ort"], b["tarif"]), (0, "Garage", "Zuhause"))
        self.assertEqual(d["monate"][0]["vollstaendig"], False)
        self.assertTrue(d["mehr"])


if __name__ == "__main__":
    unittest.main()
