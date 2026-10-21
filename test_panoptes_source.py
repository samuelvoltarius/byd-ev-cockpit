"""Tests der Panoptes-Datenquelle (kein Netz)."""
import unittest

import panoptes_source as ps

SUMMARY = {"state": {"gear": "D", "locked": True, "parked": False},
           "range": {"totalKm": 210, "elecKm": 210, "socPct": 64},
           "charging": {"active": False, "kw": None}, "env": {"tempC": 9}}
GPS = {"hasLocation": True, "location": {"lat": 47.81, "lng": 13.05}}
FZ = {"odometer": {"totalKm": 18342.4}}


class Fake:
    """kopplung=False: altes Panoptes (kennt /auth/kopplung nicht -> 404). True: neuer Einmal-Code (v1.1)."""
    def __init__(self, antworten, gueltig="jwt-1", kopplung=False):
        self.antworten, self.gueltig, self.aufrufe, self.kopplung = antworten, gueltig, [], kopplung
        self.code_benutzt = False

    def __call__(self, url, daten=None, jwt="", methode=None):
        pfad = url.split(":8180", 1)[1]
        self.aufrufe.append((pfad, jwt))
        if pfad == "/auth/kopplung":
            if not self.kopplung:
                import urllib.error
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            ok = daten.get("code") == "byd-1-geheim" and not self.code_benutzt
            self.code_benutzt = self.code_benutzt or ok
            return {"success": ok, "jwt": self.gueltig if ok else None}
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
        self.assertEqual(ps.kennung_aus({"success": True, "autoId": "a-0123456789abcdef"}), "a-0123456789abcdef")
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
        self.assertEqual((st["soc"], st["odometer"], st["gear"], st["charging"]), (63.5, 18342.0, "P", "OFF"))
        self.assertNotIn("locked", st)          # door_lock der Telemetrie ist unzuverlaessig (meist -1) -> nie daraus ableiten
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
        f = Fake(antworten, kopplung=kw.pop("kopplung", False))
        gespeichert = []
        p = ps.Panoptes("http://100.1.2.3:8180", "byd-1-geheim", http=f,
                        jwt_gespeichert=lambda j, code_verbraucht=False: gespeichert.append(j), **kw)
        return p, f, gespeichert

    def test_telemetrie_reicht(self):
        tel = {"success": True, "telemetry": {"soc": 70, "odometer": 100, "lat": 47.8, "lon": 13.0}}
        p, f, g = self.neu({"/api/mqtt/telemetry": tel})
        st = p.lies()
        self.assertEqual((st["soc"], st["online"], st["_quelle"]), (70.0, "ON", "Panoptes"))
        # 1.9.8: nutzbare Akku-kWh hoechstens alle 6 h aus der Uebersicht (hier ohne Antwort -> kein Wert)
        self.assertEqual([a[0] for a in f.aufrufe], ["/auth/kopplung", "/auth/token", "/api/mqtt/telemetry",
                                                     "/api/vehicle/state", "/api/launcher/v1/summary"])
        self.assertNotIn("usable_kwh", st)
        p.lies()
        self.assertEqual([a[0] for a in f.aufrufe][-1], "/api/mqtt/telemetry")   # nicht schon wieder
        self.assertEqual(g, ["jwt-1"])                 # Token wird gemerkt (altes Panoptes: Rueckfall /auth/token)

    def test_neue_kopplung_einmal_code(self):
        tel = {"success": True, "telemetry": {"soc": 70, "lat": 47.8, "lon": 13.0}}
        p, f, g = self.neu({"/api/mqtt/telemetry": tel}, kopplung=True)
        self.assertEqual(p.lies()["soc"], 70.0)
        self.assertEqual([a[0] for a in f.aufrufe][:2], ["/auth/kopplung", "/api/mqtt/telemetry"])
        self.assertTrue(p.code_verbraucht)
        self.assertEqual(p.code, "")                   # Code nie wieder senden
        # JWT laeuft ab -> kein stilles Neu-Anmelden mit verbrauchtem Code, sondern "neu koppeln"
        f.gueltig = "jwt-2"
        self.assertIsNone(p.lies())
        self.assertEqual(p.letzter_fehler, "kopplung_abgelaufen")
        self.assertNotIn("/auth/token", [a[0] for a in f.aufrufe])

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


class TestSchloss(unittest.TestCase):
    """Alfred 21.10.: 'Verriegelt: Nein' bei verriegeltem Auto. Quelle ist /api/vehicle/state doors.overall
    (API-Bedeutung 1 = verriegelt, 2 = offen, -1 = unbekannt)."""
    def lies(self, overall, telemetrie_tuer=(-1, -1, -1, -1)):
        tel = {"success": True, "telemetry": {"soc": 71, "lat": 47.8, "lon": 13.0, "odometer": 1, "door_lock": list(telemetrie_tuer)}}
        fz = {"doors": {"overall": overall, "lf": overall, "scope": "driver_door", "source": "ota"}}
        f = Fake({"/api/mqtt/telemetry": tel, "/api/vehicle/state": fz, "/api/launcher/v1/summary": {}})
        p = ps.Panoptes("http://100.1.2.3:8180", "", jwt="jwt-1", http=f)
        return p.lies(), p, f

    def test_verriegelt(self):
        self.assertEqual(self.lies(1)[0]["locked"], "ON")

    def test_offen(self):
        self.assertEqual(self.lies(2)[0]["locked"], "OFF")

    def test_unbekannt_kein_nein(self):
        for o in (-1, 0, None):
            self.assertNotIn("locked", self.lies(o)[0])

    def test_nicht_jede_runde(self):
        st, p, f = self.lies(1)
        p.lies()
        self.assertEqual([a[0] for a in f.aufrufe].count("/api/vehicle/state"), 1)   # hoechstens alle 2 min
        self.assertEqual(p.lies()["locked"], "ON")                                       # zuletzt bekannter Wert bleibt


if __name__ == "__main__":
    unittest.main(verbosity=2)
