"""Tests 3D-Modelle (kein Netz)."""
import hashlib
import json
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
        self.assertEqual(m3.modell_id("BYD Seal 6 DM-i Touring (Boost)"), "seal6-dmi-touring")
        self.assertEqual(m3.modell_id("BYD Seal 6 DMI Touring (Comfort)"), "seal6-dmi-touring")
        self.assertNotEqual(m3.modell_id("BYD Seal 6 DM-i Touring"), "seal")
        self.assertNotEqual(m3.modell_id("BYD Seal 6 DM-i Touring"), "seal-u")
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

    def test_seal6_ohne_freigegebenes_asset_bleibt_beim_platzhalter(self):
        manifest = {"version": 17, "models": MANI["models"] + [{
            "id": "seal6-dmi-touring", "name": "BYD Seal 6 DM-i Touring",
            "file": None, "sha256": None, "verfuegbar": False,
        }]}
        self.assertIsNone(m3.eintrag(manifest, "seal6-dmi-touring"))


class TestManifest(unittest.TestCase):
    def test_kanonischer_katalog_v17_und_neuer(self):
        for version in (17, 18):
            manifest = {"version": version, "models": []}
            self.assertIs(m3.manifest_pruefen(manifest), manifest)

    def test_alter_oder_strukturell_falscher_katalog_wird_abgewiesen(self):
        for manifest in ({"version": 16, "models": []}, {"version": 17}, {"models": []}):
            with self.assertRaises(ValueError):
                m3.manifest_pruefen(manifest)

    def test_manifest_client_nutzt_gemeinsamen_kanal_und_akzeptiert_updates(self):
        calls = []
        raw = json.dumps({"version": 18, "models": []}).encode("utf-8")
        client = m3.Manifest(hole=lambda url: calls.append(url) or raw, uhr=lambda: 1.0)
        self.assertEqual(client.get()["version"], 18)
        self.assertEqual(calls, [m3.MANIFEST_URL])


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
