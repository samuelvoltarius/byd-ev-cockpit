"""1.17: Wallbox automatisch einrichten - vorhandene HA-Verbindung mitnutzen, Vorschlag je HA-Geraet (eine = vorausgewaehlt,
mehrere = Liste), Tuya in HA erkennen, Start-Hinweis einmalig. Alles mit Attrappen, nie eine echte Wallbox."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

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


def st(eid, state, **a):
    return {"entity_id": eid, "state": state, "attributes": a}


HAUS = [
    # Tuya-Wallbox ueber die HA-Tuya-Integration (Geraet "Garage Wallbox")
    st("switch.ladestation_garage_schalter", "on", friendly_name="Ladestation Garage Schalter"),
    st("number.ladestation_garage_ladestrom", "10", unit_of_measurement="A", min=6, max=16, friendly_name="Ladestation Garage Ladestrom"),
    st("sensor.ladestation_garage_leistung", "2.3", unit_of_measurement="kW", device_class="power", friendly_name="Ladestation Garage Leistung"),
    st("sensor.ladestation_garage_status", "charger_charging", friendly_name="Ladestation Garage Status"),
    # Rauschen: Waermepumpe mit Strom-Zahl, Steckdose, Temperatur
    st("number.waermepumpe_strom", "8", unit_of_measurement="A", friendly_name="Waermepumpe Strom"),
    st("switch.kaffeemaschine", "off", friendly_name="Kaffeemaschine"),
    st("sensor.wohnzimmer_temperatur", "21", unit_of_measurement="C"),
]
GERAET = {"switch.ladestation_garage_schalter": ("dev1", "Garage Wallbox"), "number.ladestation_garage_ladestrom": ("dev1", "Garage Wallbox"),
          "sensor.ladestation_garage_leistung": ("dev1", "Garage Wallbox"), "sensor.ladestation_garage_status": ("dev1", "Garage Wallbox")}


class TestHaGeraete(unittest.TestCase):
    def test_genau_eine_wallbox(self):
        g = wq.ha_geraete(HAUS, GERAET)
        self.assertEqual(len(g), 1)
        self.assertEqual((g[0]["name"], g[0]["leistungW"], g[0]["laedt"], g[0]["stromA"]), ("Garage Wallbox", 2300, True, 10))
        z = g[0]["zuordnung"]
        self.assertEqual((z["modus"], z["strom"], z["leistung"], z["laedt"]),
                         ("switch.ladestation_garage_schalter", "number.ladestation_garage_ladestrom",
                          "sensor.ladestation_garage_leistung", "sensor.ladestation_garage_status"))

    def test_ohne_geraete_info_nach_namen_gruppiert(self):
        g = wq.ha_geraete(HAUS)
        self.assertEqual([x["zuordnung"]["strom"] for x in g], ["number.ladestation_garage_ladestrom"])

    def test_zwei_wallboxen_liste(self):
        zwei = HAUS + [st("switch.carport_wallbox", "off", friendly_name="Carport Wallbox"),
                       st("sensor.carport_wallbox_power", "0", unit_of_measurement="W", device_class="power")]
        g = wq.ha_geraete(zwei)
        self.assertEqual(len(g), 2)

    def test_select_modus_vorsichtig_zugeordnet(self):
        s = [st("select.evcc_wallbox_mode", "pv", options=["off", "now", "minpv", "pv"], friendly_name="Wallbox Mode"),
             st("sensor.evcc_wallbox_power", "0", unit_of_measurement="W", device_class="power")]
        z = wq.ha_geraete(s)[0]["zuordnung"]
        self.assertEqual(z["modusOptionen"], {"aus": "off", "sofort": "now", "minpv": "minpv", "pv": "pv"})

    def test_vorlage_nur_gepruefte_ids(self):
        t = wq._vorlage(["switch.ok_1", "x; {{ 7 }}", "sensor.b"])
        self.assertIn('"switch.ok_1"', t)
        self.assertNotIn("{{ 7 }}", t)


class HaMitVorlage:
    """HA-Attrappe: /api/states, /api/template (device_id je Entitaet), config_entries."""

    def __init__(self, tuya=("localtuya",)):
        self.aufrufe, self.tuya = [], tuya

    def __call__(self, methode, url, token, daten=None, timeout=4.0):
        pfad = url.split(":8123", 1)[1]
        self.aufrufe.append((methode, pfad))
        if token != "gut":
            raise wq.WallboxFehler("anmeldung", 502)
        if pfad == "/api/states":
            return HAUS
        if pfad.startswith("/api/states/"):
            return next((x for x in HAUS if x["entity_id"] == pfad[12:]), None)
        if pfad == "/api/template":
            ids = json.loads(daten["template"].split(" in ", 1)[1].split(" -%}", 1)[0])
            return [[e] + list(GERAET.get(e, ("", ""))) for e in ids]
        if pfad == "/api/config/config_entries/entry":
            return [{"domain": d, "title": d} for d in self.tuya] + [{"domain": "met", "title": "Wetter"}]
        raise AssertionError("unerwarteter Aufruf " + pfad)


class TestAuto(unittest.TestCase):
    def test_auto_nur_lesend_mit_geraetenamen_und_tuya_hinweis(self):
        ha = HaMitVorlage()
        r = wq.HaQuelle("http://192.168.0.30:8123", "gut", [], http=ha).auto()
        self.assertEqual(r["geraete"][0]["name"], "Garage Wallbox")
        self.assertEqual(r["tuya_in_ha"], ["localtuya"])
        self.assertTrue(all(m == "GET" or p == "/api/template" for m, p in ha.aufrufe))   # nur lesen (template rendert nur)


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
        for k in ("wallbox", "wallbox_frei", "wallbox_ha_token", "wallbox_hinweis_weg", "ha_refresh", "ha_oauth_url", "pv_token", "pv_url",
                  "ha_src_token", "ha_src_url"):
            ev._CFG.pop(k, None)
        ev._STATE.pop("wallbox_hinweis", None)
        self.ha = HaMitVorlage()
        self.alt = wq.HaQuelle.__init__.__defaults__
        wq.HaQuelle.__init__.__defaults__ = (self.ha, lambda s: None)

    def tearDown(self):
        wq.HaQuelle.__init__.__defaults__ = self.alt

    def req(self, pfad, b=None):
        r = urllib.request.Request(self.url + pfad, data=json.dumps(b).encode() if b is not None else None,
                                   method="POST" if b is not None else "GET", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r) as a:
            return json.loads(a.read())

    def test_nicht_verbunden(self):
        self.assertEqual(self.req("/wallbox/auto")["ha"], {"verbunden": False})

    def test_vorhandene_ha_datenquelle_wird_mitgenutzt_und_uebernommen(self):
        ev._CFG.update(ha_src_url="http://192.168.0.30:8123", ha_src_token="gut")
        d = self.req("/wallbox/auto")["ha"]
        self.assertEqual((d["verbunden"], d["url"], len(d["geraete"])), (True, "http://192.168.0.30:8123", 1))
        e = self.req("/wallbox/einstellungen", {"quelle": "ha", "ha": {"url": d["url"], "ladepunkte": [d["geraete"][0]["zuordnung"]]}})
        self.assertTrue(e["ok"])
        self.assertFalse(e["ha"]["tokenGesetzt"])                      # keine zweite Anmeldung, kein Token-Duplikat
        s = self.req("/wallbox/status")
        self.assertEqual((s["ok"], s["ladepunkte"][0]["titel"], s["ladepunkte"][0]["steuernFrei"]), (True, "Garage Wallbox", False))
        self.assertEqual(self.req("/wallbox/auto"), {"ok": True, "eingerichtet": True})

    def test_start_hinweis_einmalig(self):
        ev._CFG.update(pv_url="http://192.168.0.30:8123", pv_token="gut")
        ev._wb_hinweis_pruefen(warte=0)
        self.assertEqual(ev._STATE["wallbox_hinweis"], {"name": "Garage Wallbox", "anzahl": 1})
        self.req("/wallbox/hinweis-weg", {})
        self.assertNotIn("wallbox_hinweis", ev._STATE)
        ev._wb_hinweis_pruefen(warte=0)
        self.assertNotIn("wallbox_hinweis", ev._STATE)                # einmal weg = weg


if __name__ == "__main__":
    unittest.main()
