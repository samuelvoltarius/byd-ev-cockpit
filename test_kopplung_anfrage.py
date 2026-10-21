"""1.9: Kopplung per Anfrage (KOPPLUNG_ANFRAGE.md v1.1) und Planer-Geraete-Fluss (API §6) - ohne Netz."""
import io
import json
import unittest
import urllib.request
from unittest import mock

import panoptes_source as ps
import planer_bridge as pb

AID = "0123456789abcdef0123456789abcdef"


class TestPanoptesAnfrage(unittest.TestCase):
    def test_anfrage_ok_und_gruende(self):
        gesendet = []

        def roh(url, daten=None):
            gesendet.append((url, daten))
            return 200, {"ok": True, "id": AID, "gueltigBis": 1, "abfrageAlleMs": 2000}
        r = ps.kopplung_anfrage("http://auto:8180/", "EV-Cockpit PC", "4711", roh=roh)
        self.assertEqual(r, {"ok": True, "id": AID, "gueltigBis": 1})
        self.assertEqual(gesendet, [("http://auto:8180/auth/kopplung/anfrage", {"geraet": "EV-Cockpit PC", "pruefzahl": "4711"})])
        for code, body, grund in ((429, {"ok": False, "grund": "zu_viele_offen"}, "zu_viele_offen"),
                                  (429, {"ok": False, "grund": "ratenlimit"}, "ratenlimit"),
                                  (400, {"ok": False, "grund": "pruefzahl"}, "pruefzahl"),
                                  (404, {}, "zu_alt"),                      # Panoptes vor 0.1.7
                                  (200, {"ok": True, "id": "kurz"}, "http_200")):   # kaputte id nie annehmen
            self.assertEqual(ps.kopplung_anfrage("http://a", "x", "1", roh=lambda u, d=None, c=code, b=body: (c, b)),
                             {"ok": False, "grund": grund})

    def test_status_alle_endzustaende(self):
        def mit(code, body):
            return lambda u, d=None: (code, body)
        self.assertEqual(ps.kopplung_status("http://a", AID, roh=mit(200, {"status": "wartet"}))["status"], "wartet")
        e = ps.kopplung_status("http://a", AID, roh=mit(200, {"status": "erlaubt", "jwt": "J", "kopplungId": "k-1", "expiresIn": 9}))
        self.assertEqual(e, {"status": "erlaubt", "jwt": "J", "kopplungId": "k-1", "expiresIn": 9})
        for st in ("abgeholt", "abgelehnt", "abgelaufen"):
            self.assertEqual(ps.kopplung_status("http://a", AID, roh=mit(200, {"status": st}))["status"], st)
        self.assertEqual(ps.kopplung_status("http://a", AID, roh=mit(404, {"status": "unbekannt"}))["status"], "unbekannt")
        self.assertEqual(ps.kopplung_status("http://a", AID, roh=mit(200, {"status": "erlaubt"}))["status"], "fehler")  # ohne jwt
        self.assertEqual(ps.kopplung_status("http://a", "../x", roh=mit(200, {}))["status"], "unbekannt")   # nie fremde Pfade

    def test_link_pruefzahl_name(self):
        self.assertEqual(ps.aus_kopplungslink("https://panoptes.tail1234.ts.net/system.html#koppeln=482913"),
                         ("https://panoptes.tail1234.ts.net", "482913"))
        self.assertEqual(ps.aus_kopplungslink(" http://100.1.2.3:8180/#koppeln=ab-12 "), ("http://100.1.2.3:8180", "ab-12"))
        self.assertIsNone(ps.aus_kopplungslink("482913"))
        self.assertIsNone(ps.aus_kopplungslink("javascript:alert(1)#koppeln=1234"))
        for _ in range(50):
            z = ps.neue_pruefzahl()
            self.assertTrue(len(z) == 4 and z.isdigit())
        with mock.patch("socket.gethostname", return_value="Büro<PC>\x07" + "x" * 60):
            n = ps.geraetename()
        self.assertTrue(n.startswith("EV-Cockpit Büro") and len(n) <= 40 and "<" not in n and "\x07" not in n)

    def test_sitzung_erneuern(self):
        gesichert = []
        p = ps.Panoptes("http://a", "", "ALT", http=lambda url, daten=None, jwt="", **k: {"success": True, "jwt": "NEU"},
                        jwt_gespeichert=lambda j, code_verbraucht=False: gesichert.append(j))
        self.assertEqual(ps.sitzung_erneuern(p), "NEU")
        self.assertEqual((p.jwt, gesichert), ("NEU", ["NEU"]))

    def test_code_weg_schickt_namen(self):
        gesendet = []

        def http(url, daten=None, jwt="", **k):
            gesendet.append((url, daten))
            return {"success": True, "jwt": "J"}
        p = ps.Panoptes("http://a", "482913", http=http)
        p._anmelden()
        self.assertEqual(gesendet[0][0], "http://a/auth/kopplung")
        self.assertEqual(gesendet[0][1]["code"], "482913")
        self.assertTrue(gesendet[0][1]["name"].startswith("EV-Cockpit"))


class TestPlanerGeraet(unittest.TestCase):
    def test_start_und_abholen(self):
        aufrufe = []

        def anfrage(pfad, token, daten=None):
            aufrufe.append((pfad, token, daten))
            if pfad == "geraet/start":
                return 200, {"ok": True, "code": "ABCD1234", "code_anzeige": "ABCD-1234", "link": "/ev/verbinden?c=ABCD1234",
                             "ablauf_s": 600, "pollId": AID}
            return 202, {"status": "wartet"}
        r = pb.geraet_start("EV-Cockpit PC", anfrage=anfrage)
        self.assertEqual(r, {"code": "ABCD-1234", "pollId": AID, "link": "https://byd.serveone.at/ev/verbinden?c=ABCD1234",
                             "ablauf_s": 600})
        self.assertEqual(aufrufe[0], ("geraet/start", "", {"geraet": "EV-Cockpit PC", "typ": "cockpit"}))
        self.assertEqual(pb.geraet_abholen(AID, anfrage=anfrage), {"status": "wartet"})
        s64 = "ab" * 32
        ok = pb.geraet_abholen(AID, anfrage=lambda p, t, d=None: (200, {"status": "erlaubt", "schluessel": s64, "name": "PC"}))
        self.assertEqual(ok, {"status": "erlaubt", "token": "g:" + s64, "name": "PC"})
        for code, st in ((403, "abgelehnt"), (410, "abgelaufen"), (429, "fehler")):
            self.assertEqual(pb.geraet_abholen(AID, anfrage=lambda p, t, d=None, c=code: (c, {}))["status"], st)
        # fremder Link aus der Antwort wird nie uebernommen
        r2 = pb.geraet_start("x", anfrage=lambda p, t, d=None: (200, {"ok": True, "code": "C", "link": "https://boese.example/",
                                                                      "pollId": AID}))
        self.assertEqual(r2["link"], pb.BASIS)

    def test_header_je_schluesselart(self):
        gesehen = {}
        with mock.patch.object(urllib.request, "urlopen", side_effect=lambda req, timeout=0: _antwort(req, gesehen)):
            pb._anfrage("meine-karten", "g:" + "cd" * 32)
            self.assertEqual(gesehen.get("x-geraete-token"), "cd" * 32)
            self.assertNotIn("x-member-token", gesehen)
            gesehen.clear()
            pb._anfrage("meine-karten", "f" * 32)
            self.assertEqual(gesehen.get("x-member-token"), "f" * 32)
            self.assertNotIn("x-geraete-token", gesehen)
        self.assertEqual(pb.oeffnen_url("g:" + "cd" * 32), pb.BASIS)          # Geraete-Schluessel nie in eine URL
        self.assertEqual(pb.oeffnen_url("f" * 32), pb.BASIS + "#z=" + "f" * 32)

    def test_eine_quelle_pro_auto(self):
        # nach dem Koppeln ist der Code verbraucht, nur der JWT bleibt: Panoptes meldet trotzdem selbst
        self.assertTrue(pb.panoptes_meldet({"panoptes": True, "panoptes_url": "http://a", "panoptes_jwt": "J"}))
        self.assertTrue(pb.panoptes_meldet({"panoptes": True, "panoptes_url": "http://a", "panoptes_code": "c"}))
        self.assertFalse(pb.panoptes_meldet({"panoptes": True, "panoptes_url": "http://a"}))
        self.assertFalse(pb.panoptes_meldet({"panoptes": False, "panoptes_url": "http://a", "panoptes_jwt": "J"}))


class _Antwort(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _antwort(req, gesehen):
    gesehen.update({k.lower(): v for k, v in req.header_items()})
    return _Antwort(json.dumps({"ok": True}).encode())


if __name__ == "__main__":
    unittest.main()
