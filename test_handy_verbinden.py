# -*- coding: utf-8 -*-
"""1.22: "Handy verbinden" (QR fuer eine neue Handy-Kopplung) - Attrappe fuer den noch nicht gebauten Panoptes-Endpunkt."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handy_verbinden as hv  # noqa: E402

QR = hv.QR_START + "eyJ2IjoyLCJjIjoiMTIzNDU2IiwiYiI6eyJwIjoieHh4In19"
ID = "r-" + "a" * 16


class Pv:
    def __init__(self, post=None, get=None):
        self.post, self.get, self.gesehen = post, get, []

    def senden(self, pfad, daten):
        self.gesehen.append((pfad, daten))
        return self.post

    def _get(self, pfad):
        self.gesehen.append((pfad, None))
        return self.get


class HandyVerbinden(unittest.TestCase):
    def test_anfrage_erfolg_und_nie_ein_automatisches_erlauben(self):
        pv = Pv(post={"ok": True, "id": ID})
        r = hv.anfragen(pv, "Alfreds PC", "4821")
        self.assertEqual(r, {"ok": True, "id": ID})
        self.assertEqual(pv.gesehen[0], ("/api/kopplung/weiteres-geraet", {"art": "handy", "geraet": "Alfreds PC", "pruefzahl": "4821"}))

    def test_fehler_in_klartext(self):
        for post, teil in (({"_status": 404}, "aktualisieren"), ({"_status": 429}, "warten"),
                           ({"_status": 403, "ok": False}, "Recht"), ({"_status": 409, "ok": False, "grund": "bruecke_aus"}, "unterwegs"),
                           ({"ok": True, "id": "kaputt"}, "noch einmal")):
            r = hv.anfragen(Pv(post=post), "x", "1")
            self.assertFalse(r["ok"])
            self.assertIn(teil, r["text"], post)

    def test_status_wartet_abgelehnt_abgelaufen(self):
        for st in ("wartet", "abgelehnt", "abgelaufen", "abgeholt"):
            self.assertEqual(hv.status(Pv(get={"status": st}), ID), {"status": st})
        self.assertEqual(hv.status(Pv(get={"status": "komisch"}), ID), {"status": "fehler"})
        self.assertEqual(hv.status(Pv(get={}), "../x"), {"status": "fehler"})

    def test_erlaubt_liefert_nur_ein_bild_und_prueft_den_qr_text(self):
        r = hv.status(Pv(get={"status": "erlaubt", "qr": QR}), ID)
        self.assertEqual(r["status"], "erlaubt")
        self.assertTrue(r["svg"].startswith("<svg"))
        self.assertNotIn("eyJ2", r["svg"])                      # der QR-Text selbst wird nicht ausgeliefert
        for schlecht in ("https://boese.example/#k=abc", "", QR + "x" * 2000):
            self.assertEqual(hv.status(Pv(get={"status": "erlaubt", "qr": schlecht}), ID), {"status": "fehler"})

    def test_seite_einfach(self):
        self.assertIn("Am Auto oder in Telegram", hv.SEITE)
        for fachwort in ("Brücke", "Noise", "Tailnet", "JWT"):
            self.assertNotIn(fachwort, hv.SEITE)


if __name__ == "__main__":
    unittest.main()
