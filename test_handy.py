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
    def test_funktion_statt_version(self):
        # 0.1.17: kein JSON ("Nicht fuer gekoppelte Geraete" kommt als Text -> _roh liefert {}) bei 401/403/404 -> alt
        for c in (401, 403, 404):
            self.assertIs(ps.handy_vorhanden("http://h", "J", roh=lambda u, d=None, timeout=0, jwt="", c=c: (c, {})), False)
        # neu: JSON mit Grund (z. B. nur_handy) -> Schnittstelle da
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=lambda u, d=None, timeout=0, jwt="": (403, {"ok": False, "grund": "nur_handy"})), True)
        self.assertIs(ps.handy_vorhanden("http://h", "J", roh=lambda u, d=None, timeout=0, jwt="": (405, {})), True)

        def weg(*a, **k):
            raise OSError("x")
        self.assertIsNone(ps.handy_vorhanden("http://h", "J", roh=weg))
