"""1.11: Waechter-Aufnahmen - nur erlaubte Felder, ehrlich 'zu alt' vor Panoptes 0.1.9, keine fremden Pfade."""
import os
import unittest
import urllib.error

import waechter as w

A = {"id": "a" * 32, "type": "sentry", "dateFormatted": "21.10.2026", "timeFormatted": "19:40", "available": True,
     "personCount": 1, "path": "/storage/x.mp4", "startLat": 47.1, "startLng": 15.4, "deleteUrl": "/x", "videoUrl": "/video/id/" + "a" * 32}


class Pv:
    def __init__(self, antwort):
        self.antwort, self.pfade, self.url, self.jwt = antwort, [], "http://127.0.0.1:1", "j"

    def _get(self, pfad):
        self.pfade.append(pfad)
        if isinstance(self.antwort, Exception):
            raise self.antwort
        return self.antwort


class TestWaechter(unittest.TestCase):
    def test_nur_erlaubte_felder(self):
        pv = Pv({"success": True, "recordings": [A, {"id": "../etc"}], "totalCount": 1, "totalPages": 3, "page": 1})
        d = w.liste(pv, 1, "2026-10-21", "sentry")
        self.assertEqual(d["seiten"], 3)
        self.assertEqual(len(d["aufnahmen"]), 1)                           # ungueltige ID faellt raus
        a = d["aufnahmen"][0]
        for verboten in ("path", "startLat", "startLng", "deleteUrl", "videoUrl"):
            self.assertNotIn(verboten, a)
        self.assertIn("date=2026-10-21", pv.pfade[0])
        self.assertIn("type=sentry", pv.pfade[0])

    def test_filter_werden_geprueft(self):
        pv = Pv({"success": True, "recordings": []})
        w.liste(pv, 1, "21.10.; rm", "alles")
        self.assertNotIn("date=", pv.pfade[0])
        self.assertNotIn("type=", pv.pfade[0])

    def test_vor_019_ehrlich(self):
        self.assertEqual(w.liste(Pv({"_status": 403, "error": "forbidden"}))["grund"], "zu_alt")
        e = urllib.error.HTTPError("u", 404, "nf", {}, None)
        self.assertEqual(w.liste(Pv(e))["grund"], "zu_alt")

    def test_warming(self):
        d = w.liste(Pv({"success": True, "warming": True, "progress": 40, "recordings": []}))
        self.assertTrue(d["warming"])

    def test_oeffnen_nur_gueltige_id(self):
        with self.assertRaises(ValueError):
            w.oeffnen(Pv({}), "video", "../../api/recordings/delete")
        with self.assertRaises(ValueError):
            w.oeffnen(Pv({}), "stream", "a" * 32)

    def test_nur_freigegebene_pfade_im_quelltext(self):
        q = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "waechter.py"), encoding="utf-8").read()
        for verboten in ("delete", "keep", "behalten", "stream", "camview", "snapshot", "/ws"):
            self.assertNotIn('"/api/recordings/' + verboten, q)
        self.assertNotIn("method=\"DELETE\"", q)

    def test_vorschau_202_wird_abgewartet(self):
        class R:
            def __init__(self, st): self.status = st
            def close(self): pass
        antworten = [R(202), R(202), R(200)]
        import urllib.request as ur
        alt = ur.urlopen
        ur.urlopen = lambda req, timeout=20: antworten.pop(0)
        try:
            gewartet = []
            r = w.oeffnen(Pv({}), "thumb", "a" * 32, warte=gewartet.append)
            self.assertEqual((r.status, len(gewartet)), (200, 2))
            antworten[:] = [R(202)] * 5
            with self.assertRaises(urllib.error.HTTPError):
                w.oeffnen(Pv({}), "thumb", "a" * 32, warte=lambda s: None)
        finally:
            ur.urlopen = alt

    def test_letztes_ereignis(self):
        aufrufe = []

        def liste_(pv, seite, datum, art, groesse):
            aufrufe.append((art, groesse))
            return {"ok": True, "aufnahmen": [{"id": art, "timestamp": {"sentry": 100, "proximity": 200}[art]}]}
        self.assertEqual(w.letztes(None, liste_)["id"], "proximity")
        self.assertEqual(aufrufe, [("sentry", 1), ("proximity", 1)])          # je Art nur die neueste, keine Dashcam
        self.assertEqual(w.letztes(None, lambda *a: {"ok": False, "grund": "zu_alt"}), {"grund": "zu_alt"})
        self.assertIsNone(w.letztes(None, lambda *a: {"ok": True, "aufnahmen": []}))


if __name__ == "__main__":
    unittest.main()
