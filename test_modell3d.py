"""Tests 3D-Modelle (kein Netz)."""
import hashlib
import os
import tempfile
import unittest

import modell3d as m3

GLB = b"glTF" + b"\x00" * 100
SHA = hashlib.sha256(GLB).hexdigest()
MANI = {"models": [
    {"id": "seagull", "name": "BYD Seagull", "file": "seagull.glb", "sha256": SHA, "verfuegbar": True,
     "license": "CC-BY-4.0", "author": "Nazh Design", "attribution": "„2023 BYD Seagull“ von Nazh Design, CC BY 4.0"},
    {"id": "han", "name": "BYD Han", "file": None, "verfuegbar": False},
    {"id": "boese", "file": "../../etc/passwd", "sha256": SHA, "verfuegbar": True},
]}


class TestZuordnung(unittest.TestCase):
    def test_modelle(self):
        self.assertEqual(m3.modell_id("BYD Dolphin Surf / Seagull (Comfort/Design)"), "seagull")
        self.assertEqual(m3.modell_id("BYD Dolphin (Comfort/Design)"), "dolphin")
        self.assertEqual(m3.modell_id("BYD Seal U EV (Design)"), "seal-u")
        self.assertEqual(m3.modell_id("BYD Seal (Excellence/AWD)"), "seal")
        self.assertEqual(m3.modell_id("BYD Atto 3"), "atto3")
        self.assertEqual(m3.modell_id("Anderes / unbekannt"), "")

    def test_nur_ladbare(self):
        self.assertEqual(m3.eintrag(MANI, "seagull")["file"], "seagull.glb")
        self.assertIsNone(m3.eintrag(MANI, "han"))          # verfuegbar false
        self.assertIsNone(m3.eintrag(MANI, "boese"))        # Pfad aus dem Manifest nie ungeprueft
        self.assertIsNone(m3.eintrag(MANI, "gibtsnicht"))

    def test_namensnennung(self):
        i = m3.info(m3.eintrag(MANI, "seagull"))
        self.assertIn("Nazh Design", i["attribution"])
        self.assertEqual(i["paint"], "bodypaint")


class TestDatei(unittest.TestCase):
    def test_laden_pruefen_zwischenspeichern(self):
        calls = []
        with tempfile.TemporaryDirectory() as d:
            p = m3.datei(m3.eintrag(MANI, "seagull"), d, hole=lambda u: calls.append(u) or GLB)
            self.assertEqual(open(p, "rb").read(), GLB)
            m3.datei(m3.eintrag(MANI, "seagull"), d, hole=lambda u: calls.append(u) or GLB)
            self.assertEqual(calls, ["https://byd.serveone.at/tiles/models/seagull.glb"])   # nur einmal geladen

    def test_falsche_pruefsumme_wird_nicht_gespeichert(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                m3.datei(m3.eintrag(MANI, "seagull"), d, hole=lambda u: b"kaputt")
            self.assertEqual(os.listdir(d), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
