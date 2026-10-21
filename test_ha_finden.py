"""Home Assistant von selbst finden (mDNS + Probe), Anmeldung per HA-OAuth, Sensor-Vorschlaege."""
import socket
import struct
import unittest

import ha_finden as hf


def _n(name):
    return b"".join(bytes([len(t)]) + t.encode() for t in name.split(".")) + b"\0"


def _rr(name, typ, daten):
    return _n(name) + struct.pack(">HHIH", typ, 1, 120, len(daten)) + daten


def antwort():
    inst = "Home._home-assistant._tcp.local"
    txt = b"".join(bytes([len(x)]) + x for x in (b"location_name=Home", b"version=2026.10.2", b"internal_url=http://192.168.0.30:8123"))
    rr = [_rr(hf.DIENST, 12, _n(inst)), _rr(inst, 16, txt),
          _rr(inst, 33, struct.pack(">HHH", 0, 0, 8123) + _n("ha.local")), _rr("ha.local", 1, socket.inet_aton("192.168.0.30"))]
    return struct.pack(">HHHHHH", 0, 0x8400, 0, len(rr), 0, 0) + b"".join(rr)


class TestFinden(unittest.TestCase):
    def test_mdns_antwort_lesen(self):
        g = hf.aus_records(hf.lies_antwort(antwort()))
        self.assertEqual(g, [{"name": "Home", "url": "http://192.168.0.30:8123", "version": "2026.10.2", "quelle": "mDNS"}])

    def test_ohne_txt_url_aus_srv_und_a(self):
        recs = [(hf.DIENST, "PTR", "X._home-assistant._tcp.local"), ("X._home-assistant._tcp.local", "SRV", (8123, "ha.local")),
                ("ha.local", "A", "10.0.0.5")]
        self.assertEqual(hf.aus_records(recs)[0]["url"], "http://10.0.0.5:8123")

    def test_kaputte_antwort_bricht_nicht(self):
        self.assertEqual(hf.lies_antwort(b"\x00\x01kaputt"), [])

    def test_suche_kombiniert_ohne_doppelte(self):
        geprueft = []
        r = hf.suchen(["192.168.0.30", "http://192.168.0.30:8123/", ""],
                      mdns=lambda: [{"name": "Home", "url": "http://192.168.0.30:8123", "version": "1", "quelle": "mDNS"}],
                      probe=lambda u: geprueft.append(u) or False)
        self.assertEqual([g["url"] for g in r["gefunden"]], ["http://192.168.0.30:8123"])
        self.assertEqual(geprueft, ["http://homeassistant.local:8123"])        # bekannte Adresse schon per mDNS da

    def test_nichts_gefunden_ehrlich_leer(self):
        r = hf.suchen([], mdns=lambda: [], probe=lambda u: False)
        self.assertEqual(r["gefunden"], [])
        self.assertIn("http://homeassistant.local:8123", r["geprueft"])

    def test_adresse_normalisieren(self):
        self.assertEqual(hf.normal("192.168.0.30"), "http://192.168.0.30:8123")
        self.assertEqual(hf.normal("https://abc.ui.nabu.casa/"), "https://abc.ui.nabu.casa")


class TestAnmeldung(unittest.TestCase):
    def test_anmelde_url(self):
        u = hf.anmelde_url("http://ha:8123", "http://127.0.0.1:8098/", "http://127.0.0.1:8098/ha/callback", "s1")
        self.assertTrue(u.startswith("http://ha:8123/auth/authorize?"))
        self.assertIn("client_id=http%3A%2F%2F127.0.0.1%3A8098%2F", u)
        self.assertIn("redirect_uri=http%3A%2F%2F127.0.0.1%3A8098%2Fha%2Fcallback", u)

    def test_code_tauschen_und_zugang_mit_cache(self):
        aufrufe = []

        def token(ha, f):
            aufrufe.append(f["grant_type"])
            return {"access_token": "a%d" % len(aufrufe), "refresh_token": "r", "expires_in": 1800}
        d = hf.code_tauschen("http://ha", "c", "cid", token=token)
        self.assertEqual(d["refresh_token"], "r")
        uhr = [1000.0]
        z = hf.Zugang(token=token, uhr=lambda: uhr[0])
        a1 = z.access("http://ha", "r", "cid")
        self.assertEqual(z.access("http://ha", "r", "cid"), a1)              # 30 min wiederverwenden
        uhr[0] += 1790
        self.assertNotEqual(z.access("http://ha", "r", "cid"), a1)           # kurz vor Ablauf neu
        self.assertEqual(aufrufe, ["authorization_code", "refresh_token", "refresh_token"])

    def test_ohne_refresh_token_fehler(self):
        with self.assertRaises(ValueError):
            hf.code_tauschen("http://ha", "c", "cid", token=lambda ha, f: {"error": "invalid_request"})

    def test_state_zufaellig(self):
        self.assertNotEqual(hf.neuer_state(), hf.neuer_state())


class TestSensoren(unittest.TestCase):
    def test_pv_leistung_zuerst(self):
        st = [{"entity_id": "sensor.hausverbrauch", "state": "800", "attributes": {"unit_of_measurement": "W", "friendly_name": "Hausverbrauch"}},
              {"entity_id": "sensor.pv_energie_heute", "state": "12", "attributes": {"unit_of_measurement": "kWh", "device_class": "energy"}},
              {"entity_id": "sensor.fronius_ac_power", "state": "3200", "attributes": {"unit_of_measurement": "W", "device_class": "power"}},
              {"entity_id": "light.kueche", "state": "on", "attributes": {}},
              {"entity_id": "sensor.temperatur", "state": "21", "attributes": {"unit_of_measurement": "°C"}}]
        v = hf.sensoren_vorschlagen(st)
        self.assertEqual([x["id"] for x in v], ["sensor.fronius_ac_power", "sensor.pv_energie_heute", "sensor.hausverbrauch"])


class TestCockpitToken(unittest.TestCase):
    def test_token_wahl(self):
        import os, tempfile
        alt = os.environ.get("EVCOCKPIT_CFGDIR")
        os.environ["EVCOCKPIT_CFGDIR"] = tempfile.mkdtemp()
        try:
            import evcockpit as ev
        finally:
            os.environ.pop("EVCOCKPIT_CFGDIR", None) if alt is None else os.environ.__setitem__("EVCOCKPIT_CFGDIR", alt)
        cfg = dict(ev._CFG)
        try:
            ev._CFG.clear()
            self.assertEqual(ev._ha_token("http://ha:8123", "handtoken"), "handtoken")
            with self.assertRaises(ValueError):
                ev._ha_token("http://ha:8123")                              # weder angemeldet noch Token
            ev._CFG.update(ha_refresh="r", ha_oauth_url="http://ha:8123", ha_client_id="http://127.0.0.1:8098/")
            ev._HA_ZUGANG = hf.Zugang(token=lambda ha, f: {"access_token": "acc", "expires_in": 1800})
            self.assertEqual(ev._ha_token("http://ha:8123/"), "acc")
            with self.assertRaises(ValueError):
                ev._ha_token("http://anderes-ha:8123")                     # Anmeldung gilt nur fuer dieses HA
        finally:
            ev._CFG.clear(); ev._CFG.update(cfg); ev._HA_ZUGANG = None

    def test_refresh_token_verschluesselt(self):
        import geheim
        self.assertIn("ha_refresh", geheim.FELDER)


if __name__ == "__main__":
    unittest.main()
