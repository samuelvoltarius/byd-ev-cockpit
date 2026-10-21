"""WALLBOX_VERTRAG §5 im Cockpit: Freigabe je Ladepunkt, Bestaetigung serverseitig (409, einmal, 30 s, genau diese Aktion),
Hostwechsel loescht Freigaben, Heizung nie, Protokoll ohne URL."""
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import wallbox_steuern as ws

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


class TestBestaetigung(unittest.TestCase):
    def test_einmal_genau_diese_aktion_30s(self):
        t = [1000.0]
        uhr = lambda: t[0]
        k = ws.schluessel(1, "Carport", "modus", "now")
        b = ws.frage(k, uhr)
        self.assertEqual(len(b), 32)
        self.assertFalse(ws.einloesen(b, ws.schluessel(1, "Carport", "modus", "pv"), uhr))   # andere Aktion: verbraucht
        b = ws.frage(k, uhr)
        self.assertTrue(ws.einloesen(b, k, uhr))
        self.assertFalse(ws.einloesen(b, k, uhr))                                              # nur einmal
        b = ws.frage(k, uhr)
        t[0] += 31
        self.assertFalse(ws.einloesen(b, k, uhr))                                              # abgelaufen
        self.assertFalse(ws.einloesen(None, k, uhr))

    def test_protokoll_ohne_url_200_zeilen(self):
        from pathlib import Path
        p = Path(tempfile.mkdtemp()) / "p.jsonl"
        for i in range(205):
            ws.protokoll(p, "evcc", "evcc:1", "ziel", 80, "uebernommen")
        z = p.read_text("utf-8").splitlines()
        self.assertEqual(len(z), 200)
        self.assertNotIn("http", p.read_text("utf-8"))
        self.assertEqual(ws.protokoll_lesen(p, 3)[0]["herkunft"], "cockpit")


STATE = {"loadpoints": [{"title": "Carport", "mode": "smart", "alwaysCharge": "off", "limitSoc": 95, "art": "wallbox", "modus": "pv"},
                        {"title": "Garage", "mode": "now", "art": "wallbox", "modus": "now"},
                        {"title": "Heat pump", "mode": "smart", "art": "heizung", "modus": "pv"}]}


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
        ev._CFG.pop("evcc_steuern", None)
        ev._CFG.pop("evcc_steuern_ziel", None)
        self.gesendet = []
        self.p = [patch("evcc_backend.STEUERN_FREIGEGEBEN", True),
                  patch("evcc_backend.get_evcc_state", side_effect=lambda h, p=7070: STATE),
                  patch("evcc_backend.set_loadpoint", side_effect=self._setze)]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def _setze(self, host, port, lp, mode=None, limit_soc=None):
        self.gesendet.append((host, lp, mode, limit_soc))
        return {"ok": True, "mode": mode, "mode_roh": "smart", "limit_soc": limit_soc or 95}

    def post(self, pfad, b):
        r = urllib.request.Request(self.url + pfad, data=json.dumps(b).encode(), method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r) as a:
                return a.status, json.loads(a.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def bestaetigt(self, pfad, b):
        c, d = self.post(pfad, b)
        self.assertEqual((c, d["grund"]), (409, "bestaetigung_noetig"))
        return self.post(pfad, dict(b, bestaetigung=d["bestaetigung"]))

    B = {"host": "192.168.1.8", "port": 7070, "lp": 1, "titel": "Carport"}

    def test_ohne_freigabe_403_und_nichts_gesendet(self):
        c, d = self.post("/energy/steuern", dict(self.B, mode="now"))
        self.assertEqual((c, d["grund"]), (403, "nicht_freigegeben"))
        self.assertEqual(self.gesendet, [])

    def test_ablauf_freigeben_steuern(self):
        c, d = self.bestaetigt("/energy/steuern-erlauben", dict(self.B, an=True))
        self.assertEqual((c, d["steuern_erlaubt"]), (200, ["1:Carport"]))
        c, d = self.post("/energy/steuern", dict(self.B, mode="now"))
        self.assertEqual(c, 409)
        self.assertIn("Sofort", d["frage"]["text"])
        self.assertEqual(self.gesendet, [])                                        # ohne Ja nichts gesendet
        c2, d2 = self.post("/energy/steuern", dict(self.B, mode="pv", bestaetigung=d["bestaetigung"]))
        self.assertEqual(c2, 409)                                                  # Kennung galt fuer 'now'
        c, d = self.bestaetigt("/energy/steuern", dict(self.B, limit_soc=85))
        self.assertEqual((c, d["uebernommen"]), (200, True))
        self.assertEqual(self.gesendet, [("192.168.1.8", 1, None, 85)])
        prot = (ev.CFG_DIR / "wallbox_protokoll.jsonl").read_text("utf-8")
        self.assertNotIn("192.168", prot)

    def test_ungueltig_400_vor_rueckfrage(self):
        self.bestaetigt("/energy/steuern-erlauben", dict(self.B, an=True))
        for b in ({"limit_soc": 10}, {"mode": "fast"}, {}):
            c, d = self.post("/energy/steuern", dict(self.B, **b))
            self.assertEqual(c, 400)

    def test_heizung_nicht_freigebbar(self):
        c, d = self.post("/energy/steuern-erlauben", {"host": "192.168.1.8", "lp": 3, "titel": "Heat pump", "an": True})
        self.assertEqual((c, d["grund"]), (400, "keine_wallbox"))

    def test_hostwechsel_loescht_freigaben(self):
        self.bestaetigt("/energy/steuern-erlauben", dict(self.B, an=True))
        c, d = self.post("/energy/steuern", dict(self.B, host="192.168.1.9", mode="now"))
        self.assertEqual(c, 403)
        self.assertEqual(ev._CFG.get("evcc_steuern"), [])
        c, d = self.post("/energy/steuern", dict(self.B, mode="now"))           # auch zurueck: neu freigeben noetig
        self.assertEqual(c, 403)

    def test_oeffentliche_adresse_abgelehnt(self):
        c, d = self.post("/energy/steuern-erlauben", dict(self.B, host="8.8.8.8", an=True))
        self.assertEqual(c, 400)
        c, d = self.post("/energy/steuern-erlauben", dict(self.B, host="byd.serveone.at", an=True))
        self.assertEqual(c, 400)

    def test_code_schalter_aus(self):
        with patch("evcc_backend.STEUERN_FREIGEGEBEN", False):
            c, d = self.post("/energy/steuern-erlauben", dict(self.B, an=True))
        self.assertEqual(c, 403)


if __name__ == "__main__":
    unittest.main()
