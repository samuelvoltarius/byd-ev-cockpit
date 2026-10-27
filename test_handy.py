"""1.19.1: Steuern ueber Panoptes (/api/handy/v1) - Attrappen, nie ein echtes Auto. Aufsperren gibt es nicht."""
import io
import unittest
import urllib.error

import panoptes_source as ps


def fehler(code, body=b"{}"):
    return urllib.error.HTTPError("http://x", code, "x", {}, io.BytesIO(body))


class Handy(unittest.TestCase):
    def test_ok_mit_echo(self):
        gesehen = []

        def http(url, daten=None, jwt=""):
            gesehen.append((url, daten, jwt))
            return {"ok": True, "weg": "lokal", "bestaetigt": True}
        r = ps.handy_aktion("http://100.1.2.3:8180/", "J", "klima_an", {"tempC": 26, "minuten": 10}, http=http)
        self.assertEqual(r, {"ok": True, "weg": "lokal", "bestaetigt": True})
        self.assertEqual(gesehen, [("http://100.1.2.3:8180/api/handy/v1/aktion", {"tempC": 26, "minuten": 10, "aktion": "klima_an"}, "J")])

    def test_ohne_echo_nie_als_bestaetigt(self):
        r = ps.handy_aktion("http://h", "J", "zusperren", http=lambda *a, **k: {"ok": True, "weg": "cloud", "bestaetigt": False})
        self.assertTrue(r["ok"])
        self.assertFalse(r["bestaetigt"])

    def test_aufsperren_gibt_es_nicht(self):
        called = []
        r = ps.handy_aktion("http://h", "J", "aufsperren", http=lambda *a, **k: called.append(1) or {"ok": True})
        self.assertEqual((r["ok"], r["grund"], called), (False, "nicht_erlaubt", []))

    def test_alt_404_und_rechte_und_login(self):
        def h404(*a, **k):
            raise fehler(404)

        def h401(*a, **k):
            raise ps.NichtAngemeldet()
        self.assertEqual(ps.handy_aktion("http://h", "J", "zusperren", http=h404)["grund"], "nicht_vorhanden")
        self.assertEqual(ps.handy_aktion("http://h", "J", "zusperren", http=h401)["grund"], "nicht_angemeldet")
        self.assertEqual(ps.handy_aktion("http://h", "J", "zusperren", http=lambda *a, **k: {"_status": 403})["grund"], "nicht_erlaubt")
        self.assertEqual(ps.handy_aktion("http://h", "J", "zusperren", http=lambda *a, **k: {"ok": False, "grund": "gate"})["grund"], "gate")
        self.assertEqual(ps.handy_aktion("http://h", "", "zusperren")["grund"], "nicht_angemeldet")
        for g in ("nicht_vorhanden", "nicht_erlaubt", "nicht_angemeldet", "gate", "auto_laeuft", "ratenlimit"):
            self.assertIn(g, ps.HANDY_GRUENDE)

    def test_anfrage_mit_art(self):
        gesendet = []

        def roh(url, daten=None, timeout=0):
            gesendet.append(daten)
            return 200, {"ok": True, "id": "a" * 32}
        ps.kopplung_anfrage("http://h", "Cockpit", "1234", roh=roh, art="handy")
        ps.kopplung_anfrage("http://h", "Cockpit", "1234", roh=roh)
        self.assertEqual(gesendet[0]["art"], "handy")
        self.assertNotIn("art", gesendet[1])


if __name__ == "__main__":
    unittest.main()


class Pruefen(unittest.TestCase):
    def roh(self, antworten):
        def f(u, d=None, timeout=0, jwt=""):
            for pfad, a in antworten.items():
                if u.endswith(pfad):
                    if isinstance(a, Exception):
                        raise a
                    return a
            return (404, {})
        return f

    def test_version_entscheidet(self):
        z = lambda v: {"/api/ha/v1/zustand": (200, {"geraet": {"appVersion": v}})}
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(z("0.1.19.1"))), True)
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(z("0.1.20"))), True)
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(z("0.1.19"))), False)
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(z("0.1.17"))), False)
        self.assertEqual(ps.version_aus("0.1.19.1"), (0, 1, 19, 1))
        self.assertEqual(ps.version_aus("0.1.20"), (0, 1, 20, 0))
        self.assertIsNone(ps.version_aus("x"))

    def test_gemessenes_verhalten_am_auto_0191(self):
        # Alfreds Auto 0.1.19.1: Kopplungs-Token bekommt auf JEDEN Pfad 403-Text; die Version aus /ha/v1/zustand entscheidet
        a = {"/api/ha/v1/zustand": (200, {"geraet": {"appVersion": "0.1.19.1"}}), "/api/handy/v1/status": (403, {})}
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(a)), True)

    def test_ohne_version_json_antwort_entscheidet(self):
        alt = {"/api/handy/v1/status": (403, {})}
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(alt)), False)
        neu = {"/api/handy/v1/status": (403, {"ok": False, "grund": "nur_handy"})}
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh(neu)), True)
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=self.roh({"/api/handy/v1/status": (405, {})})), True)
        self.assertIsNone(ps.handy_vorhanden("http://h", "J", roh=self.roh({"/api/ha/v1/zustand": OSError("x"), "/api/handy/v1/status": OSError("x")})))


class ModellLack(unittest.TestCase):
    def test_felder_aus_zustand(self):
        z = {"geraet": {"modell": "BYD Dolphin Surf", "modellId": "seagull", "lack": {"id": "aurora-white", "name": "Aurora White", "hex": "#e8e8ec"}}}
        o = ps.modell_aus_zustand(z)
        self.assertEqual(o, {"pan_modell": "BYD Dolphin Surf", "pan_modell_id": "seagull",
                             "pan_lack": {"id": "aurora-white", "name": "Aurora White", "hex": "#E8E8EC"}})

    def test_nur_gepruefte_werte(self):
        z = {"geraet": {"modell": "<b>X</b>", "modellId": "../etc", "lack": {"hex": "rot"}}}
        o = ps.modell_aus_zustand(z)
        self.assertNotIn("pan_modell_id", o)
        self.assertNotIn("pan_lack", o)
        self.assertNotIn("<", o["pan_modell"])
        self.assertEqual(ps.modell_aus_zustand({}), {})
        self.assertEqual(ps.modell_aus_zustand({"geraet": None}), {})
        self.assertEqual(ps.modell_aus_zustand({"geraet": {"lack": None, "modell": ""}}), {})
