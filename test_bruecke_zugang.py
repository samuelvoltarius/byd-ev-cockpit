# -*- coding: utf-8 -*-
"""1.22: Zugang fuer unterwegs holen (Knopf "Unterwegs verbinden" bzw. automatisch) und Hinweis auf der Startseite - nur Attrappen."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import evcockpit as ev  # noqa: E402
import panoptes_source as ps  # noqa: E402


class Zugang(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(ev._CFG)
        self.weg, self.roh, self.save, self.wkey = ps.WEG, ps._roh_direkt, ev.save_cfg, dict(ev._WEG)
        ev._CFG.clear()
        ev._CFG.update(panoptes=True, panoptes_url="http://100.1.2.3:8180", panoptes_jwt="J", panoptes_handy_jwt="H")
        ev.save_cfg = lambda c: None
        ev._WEG["key"] = "x"

    def tearDown(self):
        ev._CFG.clear()
        ev._CFG.update(self.cfg)
        ps.WEG, ps._roh_direkt, ev.save_cfg = self.weg, self.roh, self.save
        ev._WEG.clear()
        ev._WEG.update(self.wkey)

    def test_ohne_kopplung_und_ohne_handy(self):
        ev._CFG["panoptes"] = False
        self.assertEqual(ev._bruecke_einrichten()["grund"], "nicht_gekoppelt")
        ev._CFG.update(panoptes=True, panoptes_handy_jwt="")
        r = ev._bruecke_einrichten()
        self.assertEqual(r["grund"], "handy_fehlt")
        self.assertIn("Steuern einrichten", r["text"])

    def test_erfolg_speichert_alles_und_baut_den_weg(self):
        gesehen = []

        def roh(url, daten=None, timeout=0, jwt=""):
            gesehen.append((url, daten, jwt))
            return 200, {"ok": True, "bruecke": {"p": "P" * 43, "a_pub": "A" * 43, "server": "https://byd.serveone.at/bruecke"}}
        ps._roh_direkt = roh
        r = ev._bruecke_einrichten()
        self.assertTrue(r["ok"], r)
        self.assertEqual(gesehen[0][0], "http://100.1.2.3:8180/api/handy/v1/bruecke")
        self.assertEqual(set(gesehen[0][1]), {"h_pub", "g_handy"})              # der private Schluessel verlaesst das Cockpit nie
        self.assertEqual(gesehen[0][2], "H")                                    # mit dem Zugang der Handy-Kopplung
        self.assertEqual(ev._CFG["bruecke_p"], "P" * 43)
        self.assertEqual(len(ev._CFG["bruecke_h_priv"]), 43)
        self.assertIsNotNone(ps.WEG)
        self.assertEqual(ps.WEG.jwt_bruecke(), "H")                             # unterwegs gilt nur der Handy-Zugang
        self.assertEqual(ev._bruecke_hinweis(), "")

    def test_brueckenzugang_ist_dpapi_feld(self):
        import geheim
        for k in ("bruecke_h_priv", "bruecke_g_handy", "bruecke_p"):
            self.assertIn(k, geheim.FELDER)

    def test_fehler_in_klartext(self):
        for code, d, erwartet in ((409, {"ok": False, "grund": "bruecke_aus"}, "Handy-App unterwegs nutzen"),
                                  (503, {"ok": False, "grund": "server_nicht_erreichbar"}, "später"),
                                  (404, {}, "0.1.21")):
            ps._roh_direkt = lambda *a, **k: (code, d)
            r = ev._bruecke_einrichten()
            self.assertFalse(r["ok"])
            self.assertIn(erwartet, r["text"], (code, r))
        def kein_weg(*a, **k):
            raise OSError("x")
        ps._roh_direkt = kein_weg
        self.assertEqual(ev._bruecke_einrichten()["grund"], "kein_weg")
        self.assertIsNone(ev._bruecke_zugang())

    def test_hinweis_zustaende(self):
        self.assertEqual(ev._bruecke_hinweis(), "einrichten")
        ev._CFG.update(bruecke_p="P" * 43, bruecke_a_pub="A" * 43, bruecke_h_priv="h" * 43, bruecke_h_pub="b" * 43,
                       bruecke_g_handy="g" * 43, bruecke_server="https://byd.serveone.at/bruecke")
        ev._weg_einrichten()
        self.assertEqual(ev._bruecke_hinweis(), "")
        for g in ("geloescht", "entkoppelt", "jwt"):
            ps.WEG.letzter_fehler = g
            self.assertEqual(ev._bruecke_hinweis(), "neu", g)
        ev._CFG["panoptes_handy_jwt"] = ""
        self.assertEqual(ev._bruecke_hinweis(), "")

    def _jwt(self, rest_s):
        import base64
        import time
        kopf = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
        nutz = base64.urlsafe_b64encode(json_dumps({"exp": time.time() + rest_s}).encode()).decode().rstrip("=")
        return kopf + "." + nutz + ".x"

    def test_handy_zugang_wird_still_verlaengert_wenn_direkt_erreichbar(self):
        ev._CFG["panoptes_handy_jwt"] = self._jwt(3 * 86400)
        ev._BR.pop("erneuert", None)
        gesehen = []
        alt = ps._http_direkt
        ps._http_direkt = lambda url, daten=None, jwt="", timeout=0, methode=None: (gesehen.append((url, jwt)) or {"jwt": "NEU"})
        try:
            self.assertTrue(ev._handy_zugang_verlaengern())
            self.assertEqual(ev._CFG["panoptes_handy_jwt"], "NEU")
            self.assertTrue(gesehen[0][0].endswith("/api/sitzung/erneuern"))
            self.assertFalse(ev._handy_zugang_verlaengern())            # hoechstens alle 6 Stunden
        finally:
            ps._http_direkt = alt

    def test_lang_gueltiger_zugang_bleibt_unberuehrt_und_fehler_bleiben_still(self):
        ev._CFG["panoptes_handy_jwt"] = self._jwt(25 * 86400)
        ev._BR.pop("erneuert", None)
        self.assertFalse(ev._handy_zugang_verlaengern())
        ev._CFG["panoptes_handy_jwt"] = self._jwt(2 * 86400)

        def kaputt(*a, **k):
            raise OSError("kein Tailnet")
        alt = ps._http_direkt
        ps._http_direkt = kaputt
        try:
            self.assertFalse(ev._handy_zugang_verlaengern())
        finally:
            ps._http_direkt = alt

    def test_abgelaufen_beim_einrichten_in_klartext(self):
        ps._roh_direkt = lambda *a, **k: (401, {})
        r = ev._bruecke_einrichten()
        self.assertEqual(r["grund"], "handy_abgelaufen")
        self.assertIn("Steuern einrichten", r["text"])


def json_dumps(o):
    import json
    return json.dumps(o)


if __name__ == "__main__":
    unittest.main()
