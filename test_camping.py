"""1.18: Camping planen (Panoptes >= 0.1.16.1). Nur die gekoppelte Panoptes-API, nie ein BYD-Cloud-Befehl, nie eine Innentemperatur,
Heizweg wird nie vom Cockpit gesetzt, Planung nur mit dem Feld 'geplant'. Alles gegen Attrappen."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import camping

_D = tempfile.mkdtemp()
_ALT = os.environ.get("EVCOCKPIT_CFGDIR")
os.environ["EVCOCKPIT_CFGDIR"] = _D
try:
    import evcockpit as ev
finally:
    if _ALT is None:
        os.environ.pop("EVCOCKPIT_CFGDIR", None)
    else:
        os.environ["EVCOCKPIT_CFGDIR"] = _ALT

NOW = 1792700000000
STATUS = {"aktiv": True, "gestartet": True, "trockenlauf": True, "heizweg": "probelauf", "fahrt": "steht", "phase": "pause", "seit": NOW - 3600000,
          "soc": 71.0, "socGrenze": 20, "v12": 13.7, "aussenC": 2.0, "innenC": 21.5, "waerme": "warm", "naechsterZyklusMs": NOW + 900000,
          "budget": {"intervallMin": 45, "dauerMin": 15, "gestreckt": False, "reichtBisMs": NOW + 28800000, "reichtBisWeck": True},
          "tabelle": {"stufe": 29, "intervallMin": 45, "dauerMin": 15}, "verbrauch": {"gemessen": True, "prozentProStunde": 1.2, "heizProzentProStunde": 0.7},
          "protokoll": [{"zeit": NOW - 60000, "aktion": "ein", "stufe": 29, "geblaese": 2, "trockenlauf": True, "ergebnis": "probe<script>"},
                        {"zeit": NOW, "aktion": "unbekannt"}]}
SCHEMA = {"gruppen": [{"id": "camping", "felder": [
    {"key": "camping.waerme", "typ": "auswahl", "optionen": [{"wert": w, "titel": w} for w in ("aus", "sparen", "mild", "warm", "sehr_warm")], "standard": "warm"},
    {"key": "camping.heizweg", "typ": "auswahl", "optionen": [{"wert": w, "titel": w} for w in ("probelauf", "auto_an", "auto_an_und_cloud")], "standard": "probelauf"},
    {"key": "camping.socGrenze", "typ": "int", "min": 5, "max": 80, "schritt": 1, "einheit": "%", "standard": 20},
    {"key": "camping.weckzeit", "typ": "zeit"},
    {"key": "camping.vorheizenMinuten", "typ": "int", "min": 0, "max": 60, "standard": 30},
    {"key": "camping.morgensHeizen", "typ": "bool", "standard": False},
    {"key": "camping.hoechstdauerStunden", "typ": "int", "min": 1, "max": 24, "standard": 12},
    {"key": "system.port", "typ": "int", "nurLesendExtern": True}]}]}


class FakePv:
    def __init__(self, status=None):
        self.status, self.gesendet, self.put = dict(status or STATUS), [], []
        self.werte = {"etag": "e1", "werte": {"camping.waerme": {"wert": "warm"}, "camping.socGrenze": {"wert": 20}}}

    def _get(self, pfad):
        if pfad == "/api/camping":
            return self.status
        if pfad.startswith("/api/einstellungen/schema"):
            return SCHEMA
        if pfad == "/api/einstellungen":
            return self.werte
        raise AssertionError(pfad)

    def senden(self, pfad, daten):
        self.gesendet.append((pfad, daten))
        if pfad == "/api/camping" and daten.get("an") and self.status.get("fahrt") != "steht":
            return {"ok": False, "fehler": "nicht_geparkt", "_status": 409}
        return {"ok": True}


class TestModul(unittest.TestCase):
    def test_nie_innentemperatur_und_gesaeubert(self):
        a = camping.anzeige(STATUS)
        self.assertNotIn("innenC", a)
        self.assertNotIn("21.5", json.dumps(a))
        self.assertEqual(len(a["protokoll"]), 1)                               # unbekannte Aktion verworfen
        self.assertNotIn("<", a["protokoll"][0]["ergebnis"])
        self.assertEqual((a["budget"]["reichtBisWeck"], a["tabelle"]["stufe"], a["phase"]), (True, 29, "pause"))

    def test_probelauf_ist_der_sichere_standard(self):
        self.assertTrue(camping.anzeige({"aktiv": False})["trockenlauf"])
        self.assertEqual(camping.anzeige({"aktiv": True, "heizweg": "quatsch"})["heizweg"], "probelauf")
        self.assertFalse(camping.anzeige({"aktiv": True, "trockenlauf": False, "heizweg": "auto_an"})["trockenlauf"])

    def test_planung_nur_mit_feld(self):
        self.assertFalse(camping.anzeige(STATUS)["plan_moeglich"])
        a = camping.anzeige(dict(STATUS, geplant={"start": NOW, "ende": NOW + 3600000, "grund": "nicht_geparkt"}))
        self.assertTrue(a["plan_moeglich"])
        self.assertEqual(a["geplant"]["grund"], "nicht_geparkt")
        self.assertTrue(camping.anzeige(dict(STATUS, geplant=None))["plan_moeglich"])

    def test_aelteres_panoptes(self):
        class Alt:
            def _get(self, p):
                raise urllib.error.HTTPError("u", 404, "nf", {}, None)
        self.assertIsNone(camping.lesen(Alt()))
        self.assertIsNone(camping.lesen(type("P", (), {"_get": lambda s, p: {"_status": 403}})()))

    def test_einstellungen_ohne_heizweg(self):
        liste, _ = camping.einstellungen(FakePv())
        keys = [f["key"] for f in liste]
        self.assertNotIn("camping.heizweg", keys)
        self.assertNotIn("system.port", keys)
        self.assertEqual(len(keys), 6)

    def test_speichern_nur_whitelist_und_geprueft(self):
        pv = FakePv()
        import panoptes_source
        gesendet = []
        panoptes_source.einstellungen_schreiben = lambda p, body: (gesendet.append(body), {"ok": True, "gespeichert": body["werte"]})[1]
        r = camping.speichern(pv, {"camping.waerme": "mild", "camping.heizweg": "auto_an_und_cloud", "system.port": 1})
        self.assertTrue(r["ok"])
        self.assertEqual(gesendet[0]["werte"], {"camping.waerme": "mild"})        # Heizweg und Fremdfelder nie
        self.assertFalse(camping.speichern(pv, {"camping.socGrenze": 3})["ok"])    # unter min 5
        self.assertFalse(camping.speichern(pv, {"camping.heizweg": "auto_an"})["ok"])
        self.assertEqual(len(gesendet), 1)

    def test_senden_fehlertexte(self):
        pv = FakePv(dict(STATUS, fahrt="faehrt"))
        r = camping.an_aus(pv, True)
        self.assertEqual((r["ok"], r["fehler"]), (False, "nicht_geparkt"))
        self.assertIn("Gang P", r["text"])
        self.assertTrue(camping.an_aus(FakePv(), False)["ok"])
        self.assertFalse(camping.rueckmeldung(FakePv(), "heiss")["ok"])


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ev.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d" % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.pv = FakePv()
        self.alt = (ev._panoptes_obj, ev._panoptes_gekoppelt)
        ev._panoptes_obj, ev._panoptes_gekoppelt = (lambda: self.pv), (lambda: True)
        ev._CAMPING.update(d=None, zu_alt_bis=0.0)

    def tearDown(self):
        ev._panoptes_obj, ev._panoptes_gekoppelt = self.alt

    def req(self, pfad, b=None):
        r = urllib.request.Request(self.url + pfad, data=json.dumps(b).encode() if b is not None else None,
                                   method="POST" if b is not None else "GET", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r) as a:
            return json.loads(a.read())

    def test_seite_zeigt_status_und_einstellungen(self):
        d = self.req("/camping")
        self.assertTrue(d["vorhanden"])
        self.assertTrue(d["status"]["trockenlauf"])
        self.assertNotIn("innenC", json.dumps(d))
        self.assertEqual(len(d["einstellungen"]), 6)

    def test_ohne_camping_ausgeblendet(self):
        self.pv.status = {"_status": 404}
        self.assertEqual(self.req("/camping"), {"ok": True, "vorhanden": False})

    def test_start_beenden_rueckmeldung(self):
        self.assertTrue(self.req("/camping/an", {"an": True})["ok"])
        self.assertTrue(self.req("/camping/rueckmeldung", {"art": "zu_kalt"})["ok"])
        self.assertFalse(self.req("/camping/rueckmeldung", {"art": "x"})["ok"])
        self.assertTrue(self.req("/camping/weiter", {})["ok"])
        self.assertEqual([p for p, _ in self.pv.gesendet], ["/api/camping", "/api/camping/rueckmeldung", "/api/camping/weiter"])

    def test_plan_nur_wenn_panoptes_ihn_kann(self):
        r = self.req("/camping/plan", {"start": "2026-10-23T22:00:00Z", "ende": None})
        self.assertFalse(r["ok"])
        self.assertIn("0.1.17", r["text"])
        self.assertEqual(self.pv.gesendet, [])
        self.pv.status = dict(STATUS, geplant=None)
        self.assertTrue(self.req("/camping/plan", {"start": "2026-10-23T22:00:00Z", "ende": "2026-10-24T06:00:00Z"})["ok"])
        self.assertEqual(self.pv.gesendet[-1], ("/api/camping/plan", {"start": "2026-10-23T22:00:00Z", "ende": "2026-10-24T06:00:00Z"}))
        self.assertTrue(self.req("/camping/plan", {"loeschen": True})["ok"])
        self.assertEqual(self.pv.gesendet[-1], ("/api/camping/plan", {"loeschen": True}))

    def test_kein_cloud_und_kein_heizweg_schreiben(self):
        quelle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "camping.py"), encoding="utf-8").read()
        for verboten in ("pybyd", "OPENAIR", "bydcloud", "vehicle_realtime", "heizweg\":"):
            self.assertNotIn(verboten, quelle.replace('"heizweg": d.get("heizweg")', ""))

    def test_nicht_gekoppelt(self):
        ev._panoptes_obj, ev._panoptes_gekoppelt = (lambda: None), (lambda: False)
        self.assertFalse(self.req("/camping/an", {"an": True})["ok"])
        self.assertEqual(self.req("/camping"), {"ok": True, "vorhanden": False})


if __name__ == "__main__":
    unittest.main()
