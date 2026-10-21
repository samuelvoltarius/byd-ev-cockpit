"""Gleiche Zahlen wie das gemeinsame Kartenmodul panoptes-karte (eine Wahrheit fuer Cockpit, Planer, Panoptes).

Die Pruefdaten stammen aus https://byd.serveone.at/tiles/lib/ (Version im Dateinamen, sha256 wird geprueft).
"""
import hashlib
import json
import os
import unittest

import planer_bridge as pb

HIER = os.path.dirname(os.path.abspath(__file__))
PRUEF = os.path.join(HIER, "pruefdaten", "panoptes-karte-1.0.0.pruefdaten.json")
MODUL = os.path.join(HIER, "static", "panoptes-karte-1.0.0.js")
SHA = {PRUEF: "f0c3d5f5a532a46f7e57e4ec8d9a6237a25072c52f391f6b49efdd72b6a529fb",
       MODUL: "64760f1332f6996742e0b0ea394327e9001a173cf40e80f2b791175c0763e618"}


class TestGemeinsam(unittest.TestCase):
    def test_dateien_unveraendert(self):
        for pfad, sha in SHA.items():
            with open(pfad, "rb") as f:
                self.assertEqual(hashlib.sha256(f.read()).hexdigest(), sha, pfad)

    def test_faktor_wie_modul(self):
        d = json.load(open(PRUEF, encoding="utf-8"))
        self.assertGreaterEqual(len(d["faktor"]), 10)
        for fall in d["faktor"]:
            f = pb.faktor_aus(fall["verhaeltnisse"])
            self.assertAlmostEqual(f, fall["faktor"], places=9, msg=fall["name"])
            self.assertEqual(round(f, 3), fall["faktor_gerundet"], fall["name"])

    def test_verhaeltnis_wie_modul(self):
        d = json.load(open(PRUEF, encoding="utf-8"))
        self.assertGreaterEqual(len(d["verhaeltnis"]), 6)
        for fall in d["verhaeltnis"]:
            self.assertEqual(pb.verhaeltnis_aus(fall["fahrt"]), fall["verhaeltnis"], fall["name"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
