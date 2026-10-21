"""Tests der Panoptes-Datenquelle (kein Netz)."""
import unittest

import panoptes_source as ps

SUMMARY = {"state": {"gear": "D", "locked": True, "parked": False},
           "range": {"totalKm": 210, "elecKm": 210, "socPct": 64},
           "charging": {"active": False, "kw": None}, "env": {"tempC": 9}}
GPS = {"hasLocation": True, "location": {"lat": 47.81, "lng": 13.05}}
FZ = {"odometer": {"totalKm": 18342.4}}


class Fake:
    def __init__(self, antworten, gueltig="jwt-1"):
        self.antworten, self.gueltig, self.aufrufe = antworten, gueltig, []

    def __call__(self, url, daten=None, jwt=""):
        pfad = url.split(":8180", 1)[1]
        self.aufrufe.append((pfad, jwt))
        if pfad == "/auth/token":
            return {"success": daten.get("token") == "byd-1-geheim", "jwt": self.gueltig}
        if jwt != self.gueltig:
            raise ps.NichtAngemeldet()
        a = self.antworten.get(pfad)
        if isinstance(a, Exception):
            raise a
        return a


class TestIdentitaet(unittest.TestCase):
    def test_kennung(self):
        self.assertEqual(ps.kennung_aus({"auto": "pan-3f9a2c", "fahrzeug": "X", "quelle": "panoptes"}), "pan-3f9a2c")
        self.assertEqual(ps.kennung_aus({"auto": "LGXC1234567890123"}), "LGXC1234567890123")  # Format ok
        self.assertEqual(ps.kennung_aus({"auto": "a b/../c"}), "")      # nichts Unsauberes in URLs
        self.assertEqual(ps.kennung_aus({}), "")

    def test_noch_nicht_da(self):
        p = ps.Panoptes("http://100.1.2.3:8180", "byd-1-geheim",
                        http=Fake({"/api/planer/identitaet": RuntimeError("404")}))
        self.assertEqual(ps.identitaet(p), "")
        p2 = ps.Panoptes("http://100.1.2.3:8180", "byd-1-geheim",
                         http=Fake({"/api/planer/identitaet": {"auto": "pan-1"}}))
        self.assertEqual(ps.identitaet(p2), "pan-1")


class TestUmrechnung(unittest.TestCase):
    def test_telemetrie(self):
        st = ps.aus_telemetrie({"soc": 63.5, "odometer": 18342, "ev_range_km": 205, "ext_temp": 8,
                                "lat": 47.8, "lon": 13.0, "gear": "p", "is_charging": 0, "door_lock": [1, 1, 1, 1]})
        self.assertEqual((st["soc"], st["odometer"], st["gear"], st["charging"], st["locked"]),
                         (63.5, 18342.0, "P", "OFF", "ON"))
        self.assertEqual((st["latitude"], st["longitude"]), (47.8, 13.0))

    def test_zuendung_fuer_die_befehlssperre(self):
        self.assertEqual(ps.aus_telemetrie({"soc": 50, "power_level": 2, "speed": 0})["power_level"], 2)
        self.assertEqual(ps.aus_telemetrie({"soc": 50, "power_level": "0"})["power_level"], 0)
        self.assertNotIn("power_level", ps.aus_telemetrie({"soc": 50}))

    def test_uebersicht(self):
        st = ps.aus_uebersicht(SUMMARY, GPS, FZ)
        self.assertEqual((st["soc"], st["range_km"], st["temp_out"], st["gear"], st["locked"], st["odometer"]),
                         (64.0, 210.0, 9.0, "D", "ON", 18342.4))
        self.assertEqual(st["longitude"], 13.05)
        self.assertNotIn("charge_power", st)          # kw None -> nicht behaupten

    def test_leere_werte_werden_nicht_erfunden(self):
        self.assertEqual(ps.aus_telemetrie({"soc": None, "lat": 0, "lon": 0}), {})
        self.assertEqual(ps.aus_uebersicht({}, {"hasLocation": False, "location": {"lat": 1, "lng": 2}}), {})


class TestPanoptes(unittest.TestCase):
    def neu(self, antworten, **kw):
        f = Fake(antworten)
        gespeichert = []
        p = ps.Panoptes("http://100.1.2.3:8180", "byd-1-geheim", http=f, jwt_gespeichert=gespeichert.append, **kw)
        return p, f, gespeichert

    def test_telemetrie_reicht(self):
        tel = {"success": True, "telemetry": {"soc": 70, "odometer": 100, "lat": 47.8, "lon": 13.0}}
        p, f, g = self.neu({"/api/mqtt/telemetry": tel})
        st = p.lies()
        self.assertEqual((st["soc"], st["online"], st["_quelle"]), (70.0, "ON", "Panoptes"))
        self.assertEqual([a[0] for a in f.aufrufe], ["/auth/token", "/api/mqtt/telemetry"])
        self.assertEqual(g, ["jwt-1"])                 # Token wird gemerkt

    def test_ohne_mqtt_einzelendpunkte(self):
        p, f, _ = self.neu({"/api/mqtt/telemetry": {"success": False}, "/api/launcher/v1/summary": SUMMARY,
                            "/api/gps": GPS, "/api/vehicle/state": FZ})
        st = p.lies()
        self.assertEqual((st["soc"], st["odometer"], st["latitude"]), (64.0, 18342.4, 47.81))
        # Kilometerstand nicht bei jeder Abfrage
        f.aufrufe.clear()
        p.lies()
        self.assertNotIn("/api/vehicle/state", [a[0] for a in f.aufrufe])

    def test_abgelaufenes_token_wird_erneuert(self):
        tel = {"success": True, "telemetry": {"soc": 70}}
        p, f, g = self.neu({"/api/mqtt/telemetry": tel, "/api/launcher/v1/summary": SUMMARY, "/api/gps": GPS,
                            "/api/vehicle/state": FZ}, jwt="altes")
        self.assertEqual(p.lies()["soc"], 70.0)
        self.assertEqual(g, ["jwt-1"])

    def test_falscher_code_none(self):
        f = Fake({})
        p = ps.Panoptes("http://100.1.2.3:8180", "falsch", http=f)
        self.assertIsNone(p.lies())

    def test_auto_aus_none(self):
        p, f, _ = self.neu({"/api/mqtt/telemetry": OSError("timeout"), "/api/launcher/v1/summary": OSError("timeout")})
        self.assertIsNone(p.lies())

    def test_ohne_url_none(self):
        self.assertIsNone(ps.Panoptes("", "byd-1-geheim").lies())


if __name__ == "__main__":
    unittest.main(verbosity=2)
