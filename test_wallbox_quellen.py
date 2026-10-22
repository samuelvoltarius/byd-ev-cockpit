"""WALLBOX_VERTRAG v1.1 im Cockpit: Home Assistant (Erkennung ohne Code je Modell) und Tuya (Tabelle/Erkennung, unbekannt
= nur lesen), Endpunkte mit Freigabe, Bestaetigung, Protokoll, Geheimnisse nur bei gleicher Adresse/Geraete-ID."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import wallbox_quellen as wq

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


class HaAttrappe:
    """Home Assistant mit einer Tuya-Wallbox (Tuya-Integration): Befehle wirken erst nach zwei Abfragen (traege)."""

    def __init__(self):
        self.s = {
            "switch.wallbox_laden": {"state": "off", "attributes": {"friendly_name": "Wallbox Laden"}},
            "number.wallbox_ladestrom": {"state": "16", "attributes": {"unit_of_measurement": "A", "min": 6, "max": 32,
                                                                       "friendly_name": "Wallbox Ladestrom"}},
            "sensor.wallbox_leistung": {"state": "0.0", "attributes": {"unit_of_measurement": "kW", "device_class": "power",
                                                                       "friendly_name": "Wallbox Leistung"}},
            "sensor.wallbox_status": {"state": "charger_free", "attributes": {"friendly_name": "Wallbox Status"}},
            "sensor.wohnzimmer_temperatur": {"state": "21", "attributes": {"unit_of_measurement": "C"}},
            "switch.kaffeemaschine": {"state": "off", "attributes": {}},
        }
        self.dienste, self.offen, self.token = [], [], "gut"

    def __call__(self, methode, url, token, daten=None, timeout=4.0):
        if token != self.token:
            raise wq.WallboxFehler("anmeldung", 502)
        pfad = url.split(":8123", 1)[1]
        if self.offen:
            n, f = self.offen[0]
            if n <= 0:
                f()
                self.offen.pop(0)
            else:
                self.offen[0] = (n - 1, f)
        if methode == "GET" and pfad == "/api/states":
            return [dict(v, entity_id=k) for k, v in self.s.items()]
        if methode == "GET" and pfad.startswith("/api/states/"):
            e = pfad[12:]
            return dict(self.s[e], entity_id=e) if e in self.s else None
        dom, dienst = pfad.split("/")[3:5]
        self.dienste.append((dom, dienst, daten))
        e = daten["entity_id"]

        def wirkt():
            if dienst in ("turn_on", "turn_off"):
                an = dienst == "turn_on"
                self.s[e]["state"] = "on" if an else "off"
                self.s["sensor.wallbox_status"]["state"] = "charger_charging" if an else "charger_free"
                self.s["sensor.wallbox_leistung"]["state"] = "3.7" if an else "0.0"
            elif dienst == "set_value":
                self.s[e]["state"] = str(daten["value"])
        self.offen.append((2, wirkt))
        return []


ZU = {"schluessel": "wallbox", "titel": "Carport", "modus": "switch.wallbox_laden", "strom": "number.wallbox_ladestrom",
      "leistung": "sensor.wallbox_leistung", "laedt": "sensor.wallbox_status"}


class TestHa(unittest.TestCase):
    def test_vorschlag_findet_tuya_wallbox_in_ha(self):
        v = wq.ha_vorschlag(HaAttrappe()("GET", "http://x:8123/api/states", "gut"))["vorschlag"]
        self.assertEqual((v["modus"], v["strom"], v["leistung"], v["laedt"]),
                         ("switch.wallbox_laden", "number.wallbox_ladestrom", "sensor.wallbox_leistung", "sensor.wallbox_status"))

    def test_ladepunkt_und_traeges_zuruecklesen(self):
        ha = HaAttrappe()
        q = wq.HaQuelle("http://192.168.1.10", "gut", [wq.pruefe_ha_zuordnung(ZU)], http=ha, schlaf=lambda s: None)
        lp = q.ladepunkte()[0]
        self.assertEqual((lp["id"], lp["modus"], lp["stromA"], lp["leistungW"], lp["laedt"]), ("ha:wallbox", "aus", 16, 0, False))
        self.assertEqual(lp["faehigkeiten"], {"modus": ["aus", "sofort"], "ziel": False, "strom": {"min": 6, "max": 32}, "plan": None})
        r = q.steuern("ha:wallbox", "modus", "sofort")
        self.assertTrue(r["uebernommen"])
        self.assertEqual(r["ladepunkt"]["modus"], "sofort")                      # zurueckgelesen wird das gesteuerte Feld
        lp = q.ladepunkte()[0]
        self.assertEqual((lp["leistungW"], lp["laedt"]), (3700, True))           # Leistung/Status folgen
        self.assertTrue(q.steuern("ha:wallbox", "strom", 10)["uebernommen"])
        self.assertEqual(ha.dienste[-1], ("number", "set_value", {"entity_id": "number.wallbox_ladestrom", "value": 10}))
        with self.assertRaises(wq.WallboxFehler):
            q.steuern("ha:wallbox", "strom", 40)
        with self.assertRaises(wq.WallboxFehler):
            q.steuern("ha:wallbox", "ziel", 80)

    def test_zuordnung_geprueft(self):
        for z in (dict(ZU, modus="light.flur"), dict(ZU, schluessel="Gross"), dict(ZU, strom="number.x; rm")):
            with self.assertRaises(wq.WallboxFehler):
                wq.pruefe_ha_zuordnung(z)
        with self.assertRaises(wq.WallboxFehler):
            wq.HaQuelle("http://8.8.8.8:8123", "gut", [])


class Zugriff:
    def __init__(self, dps):
        self.d, self.gesetzt = dict(dps), []

    def dps(self):
        return dict(self.d)

    def setze(self, w):
        self.gesetzt.append(w)
        self.d.update(w)


QCCDZ = {"18": False, "4": 16, "3": "charger_free", "9": 0, "10": 230}


class TestTuya(unittest.TestCase):
    def test_tabelle_ist_kern6_datei(self):
        self.assertEqual([m["id"] for m in wq.tabelle_laden()["modelle"]], ["qccdz-standard"])

    def test_erkannt_und_steuern(self):
        z = Zugriff(QCCDZ)
        q = wq.TuyaQuelle([({"schluessel": "garage", "titel": "Garage"}, z)], schlaf=lambda s: None)
        lp = q.ladepunkte()[0]
        self.assertEqual((lp["zuordnung"], lp["modell"], lp["modus"], lp["stromA"], lp["rohDps"]),
                         ("erkannt", "qccdz-standard", "aus", 16, None))
        self.assertEqual(lp["faehigkeiten"]["strom"], {"min": 6, "max": 16})
        self.assertTrue(q.steuern("tuya:garage", "strom", 10)["uebernommen"])
        self.assertTrue(q.steuern("tuya:garage", "modus", "sofort")["uebernommen"])
        self.assertEqual(z.gesetzt, [{"4": 10}, {"18": True}])
        for a, w in (("strom", 20), ("modus", "pv"), ("ziel", 80)):
            with self.assertRaises(wq.WallboxFehler):
                q.steuern("tuya:garage", a, w)

    def test_unbekannt_nur_lesen(self):
        z = Zugriff({"1": True, "2": 13, "101": "irgendwas"})
        q = wq.TuyaQuelle([({"schluessel": "x"}, z)], schlaf=lambda s: None)
        lp = q.ladepunkte()[0]
        self.assertEqual((lp["zuordnung"], lp["faehigkeiten"]["modus"], lp["rohDps"]["101"]), ("unbekannt", [], "irgendwas"))
        with self.assertRaises(wq.WallboxFehler) as f:
            q.steuern("tuya:x", "modus", "sofort")
        self.assertEqual(f.exception.code, "tuya_zuordnung_fehlt")
        self.assertEqual(z.gesetzt, [])

    def test_eigene_zuordnung_vor_erkennung(self):
        eigen = wq.pruefe_tuya_zuordnung({"schalter": {"dp": "1"}, "strom": {"dp": "2", "min": 6, "max": 32, "faktor": 1}})
        q = wq.TuyaQuelle([({"schluessel": "x", "zuordnung": eigen}, Zugriff({"1": True, "2": 13}))], schlaf=lambda s: None)
        lp = q.ladepunkte()[0]
        self.assertEqual((lp["zuordnung"], lp["modus"], lp["stromA"]), ("bekannt", "sofort", 13))
        with self.assertRaises(wq.WallboxFehler):
            wq.pruefe_tuya_zuordnung({"strom": {"dp": "2", "min": 6, "max": 99}})


class TestEndpunkte(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ev.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d" % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        for k in ("wallbox", "wallbox_frei", "wallbox_ha_token", "wallbox_tuya_keys"):
            ev._CFG.pop(k, None)
        self.ha = HaAttrappe()
        self.alt = wq.HaQuelle.__init__.__defaults__
        wq.HaQuelle.__init__.__defaults__ = (self.ha, lambda s: None)     # HA-Attrappe statt Netz, ohne Warten

    def tearDown(self):
        wq.HaQuelle.__init__.__defaults__ = self.alt

    def req(self, pfad, b=None):
        r = urllib.request.Request(self.url + pfad, data=json.dumps(b).encode() if b is not None else None,
                                   method="POST" if b is not None else "GET", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r) as a:
                return a.status, json.loads(a.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def einrichten(self, **ha):
        return self.req("/wallbox/einstellungen", {"quelle": "ha", "ha": dict({"url": "http://192.168.1.10:8123", "token": "gut",
                                                                                "ladepunkte": [ZU]}, **ha)})

    def bestaetigt(self, pfad, b):
        c, d = self.req(pfad, b)
        self.assertEqual((c, d.get("grund")), (409, "bestaetigung_noetig"), d)
        return self.req(pfad, dict(b, bestaetigung=d["bestaetigung"]))

    def test_ablauf_ha(self):
        c, d = self.einrichten()
        self.assertEqual((c, d["ha"]["tokenGesetzt"]), (200, True))
        self.assertNotIn('"gut"', json.dumps(d))                                  # Token nie in der Antwort
        c, d = self.req("/wallbox/status")
        self.assertEqual((d["ok"], d["ladepunkte"][0]["steuernFrei"]), (True, False))
        c, d = self.req("/wallbox/steuern", {"ladepunkt": "ha:wallbox", "aktion": "modus", "wert": "sofort"})
        self.assertEqual(c, 403)
        c, d = self.bestaetigt("/wallbox/freigabe", {"ladepunkt": "ha:wallbox", "an": True})
        self.assertEqual(d["freigaben"], ["ha:wallbox"])
        c, d = self.req("/wallbox/steuern", {"ladepunkt": "ha:wallbox", "aktion": "strom", "wert": 40})
        self.assertEqual(c, 400)                                                  # vor der Rueckfrage geprueft
        c, d = self.bestaetigt("/wallbox/steuern", {"ladepunkt": "ha:wallbox", "aktion": "strom", "wert": 10})
        self.assertEqual((c, d["uebernommen"], d["ladepunkt"]["stromA"]), (200, True, 10))
        self.assertEqual(self.ha.dienste, [("number", "set_value", {"entity_id": "number.wallbox_ladestrom", "value": 10})])
        prot = (ev.CFG_DIR / "wallbox_protokoll.jsonl").read_text("utf-8")
        self.assertIn('"aktion": "strom"', prot)
        self.assertNotIn("192.168", prot)

    def test_vorschlag_endpunkt(self):
        self.einrichten()
        c, d = self.req("/wallbox/ha/vorschlag", {"url": "http://192.168.1.10:8123"})
        self.assertEqual((c, d["vorschlag"]["strom"]), (200, "number.wallbox_ladestrom"))

    def test_adresswechsel_loescht_freigaben_und_token(self):
        self.einrichten()
        self.bestaetigt("/wallbox/freigabe", {"ladepunkt": "ha:wallbox", "an": True})
        c, d = self.req("/wallbox/einstellungen", {"quelle": "ha", "ha": {"url": "http://192.168.1.11:8123", "ladepunkte": [ZU]}})
        self.assertEqual((d["freigaben"], d["ha"]["tokenGesetzt"]), ([], False))
        c, d = self.req("/wallbox/einstellungen", {"quelle": "ha", "ha": {"url": "http://8.8.8.8:8123", "ladepunkte": [ZU]}})
        self.assertEqual(c, 400)

    def test_tuya_schluessel_nur_bei_gleicher_geraete_id(self):
        g = {"schluessel": "garage", "titel": "Garage", "geraeteId": "bf0123456789abcdefgh", "ip": "192.168.1.50", "version": "3.4"}
        c, d = self.req("/wallbox/einstellungen", {"quelle": "tuya", "tuya": {"geraete": [dict(g, localKey="Kq7#Zp2!Lm9$Xw4&")]}})
        self.assertEqual((c, d["tuya"]["geraete"][0]["localKeyGesetzt"]), (200, True))
        self.assertNotIn("Kq7#Zp2", json.dumps(d))
        c, d = self.req("/wallbox/einstellungen", {"quelle": "tuya", "tuya": {"geraete": [g]}})
        self.assertTrue(d["tuya"]["geraete"][0]["localKeyGesetzt"])                # gleiche ID: behalten
        c, d = self.req("/wallbox/einstellungen", {"quelle": "tuya", "tuya": {"geraete": [dict(g, geraeteId="bf9999999999999999zz")]}})
        self.assertFalse(d["tuya"]["geraete"][0]["localKeyGesetzt"])               # neue ID: verworfen
        for schlecht in (dict(g, ip="8.8.8.8"), dict(g, ip="127.0.0.1"), dict(g, version="3.1"), dict(g, localKey="kurz")):
            c, d = self.req("/wallbox/einstellungen", {"quelle": "tuya", "tuya": {"geraete": [schlecht]}})
            self.assertEqual(c, 400, schlecht)

    def test_tuya_unbekannt_nicht_freigebbar(self):
        lp = wq.tuya_ladepunkt({"schluessel": "x"}, {"1": True}, None, "unbekannt", None)
        q = type("Q", (), {"ladepunkte": lambda s: [lp]})()
        ev._CFG["wallbox"] = {"quelle": "tuya"}
        with patch.object(ev, "_wb_quelle", return_value=q):
            c, d = self.req("/wallbox/freigabe", {"ladepunkt": "tuya:x", "an": True})
        self.assertEqual((c, d["grund"]), (400, "tuya_zuordnung_fehlt"))


if __name__ == "__main__":
    unittest.main()
