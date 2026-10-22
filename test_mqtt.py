"""1.17.1: MQTT-Server nicht mit Home Assistant verwechseln (Fall Alfred 23.10.: WinError 10061), verstaendliche Texte,
Broker aus der HA-Integration lesen (nur Host/Port, nur wenn erreichbar), keine fest eingebaute Adresse."""
import os
import socket
import tempfile
import unittest

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
import wallbox_quellen as wq


class TestFehlertext(unittest.TestCase):
    def test_windows_deutsch_verweigert(self):
        e = ConnectionRefusedError(10061, "Es konnte keine Verbindung hergestellt werden, da der Zielcomputer die Verbindung verweigerte")
        t = ev._mqtt_fehlertext(e, "192.168.0.30", 1883)
        self.assertIn("kein MQTT-Server", t)
        self.assertIn("192.168.0.30:1883", t)
        self.assertNotIn("WinError", t)

    def test_leer_zeitueberschreitung_name(self):
        self.assertIn("fehlt", ev._mqtt_fehlertext(OSError("x"), ""))
        self.assertIn("antwortet nicht", ev._mqtt_fehlertext(socket.timeout("timed out"), "10.0.0.9"))
        self.assertIn("kennt das Netz nicht", ev._mqtt_fehlertext(socket.gaierror(11001, "x"), "broker.lan"))


class TestVorschlag(unittest.TestCase):
    def setUp(self):
        for k in ("ha_refresh", "ha_oauth_url", "pv_token", "pv_url", "ha_src_token", "ha_src_url"):
            ev._CFG.pop(k, None)
        self.alt = wq._ha_http

    def tearDown(self):
        wq._ha_http = self.alt

    def test_ohne_ha_kein_raten(self):
        self.assertEqual(ev._mqtt_vorschlag(), {"quelle": None, "grund": "ha_nicht_angemeldet"})

    def test_aus_ha_nur_erreichbar(self):
        ev._CFG.update(pv_url="http://192.168.0.30:8123", pv_token="t")
        wq._ha_http = lambda m, u, t, d=None, timeout=4.0: [{"domain": "met", "title": "Wetter"}, {"domain": "mqtt", "title": "192.168.0.94"}]
        self.assertEqual(ev._mqtt_vorschlag(pruefe=lambda h, p: None), {"quelle": "Home Assistant", "host": "192.168.0.94", "port": 1883})

        def zu(h, p):
            raise ConnectionRefusedError()
        self.assertEqual(ev._mqtt_vorschlag(pruefe=zu)["quelle"], None)

    def test_addon_heisst_ha_selbst(self):
        ev._CFG.update(pv_url="http://192.168.0.30:8123", pv_token="t")
        wq._ha_http = lambda m, u, t, d=None, timeout=4.0: [{"domain": "mqtt", "title": "core-mosquitto"}]
        self.assertEqual(ev._mqtt_vorschlag(pruefe=lambda h, p: None)["host"], "192.168.0.30")


class TestWizard(unittest.TestCase):
    def test_ha_adresse_landet_nie_im_mqtt_feld(self):
        self.assertNotIn("value=ha.ip", ev.WIZARD)
        self.assertNotIn("nur noch den Zugriffstoken eintragen", ev.WIZARD)
        self.assertIn("mqttAuto()", ev.WIZARD)


if __name__ == "__main__":
    unittest.main()
