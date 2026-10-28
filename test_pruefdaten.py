"""Gleiche Zahlen wie das gemeinsame Kartenmodul panoptes-karte (eine Wahrheit fuer Cockpit, Planer, Panoptes).

Die Pruefdaten stammen aus https://byd.serveone.at/tiles/lib/ (Version im Dateinamen, sha256 wird geprueft).
"""
import hashlib
import json
import os
import unittest

import planer_bridge as pb

HIER = os.path.dirname(os.path.abspath(__file__))
PRUEF = os.path.join(HIER, "pruefdaten", "panoptes-karte-1.1.1.pruefdaten.json")
MODUL = os.path.join(HIER, "static", "panoptes-karte-1.1.1.js")
SHA = {PRUEF: "84421768f1378f934bfc41775d99e843b9995e8cc0a210b7a20045866b179e82",
       MODUL: "9956ae2f065758f3a7d6a7befd1a3bcf81ca0b351dd8313dacefad15a3e8aebf"}


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
