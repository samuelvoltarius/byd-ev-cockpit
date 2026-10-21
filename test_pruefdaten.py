"""Gleiche Zahlen wie das gemeinsame Kartenmodul panoptes-karte (eine Wahrheit fuer Cockpit, Planer, Panoptes).

Die Pruefdaten stammen aus https://byd.serveone.at/tiles/lib/ (Version im Dateinamen, sha256 wird geprueft).
"""
import hashlib
import json
import os
import unittest

import planer_bridge as pb

HIER = os.path.dirname(os.path.abspath(__file__))
PRUEF = os.path.join(HIER, "pruefdaten", "panoptes-karte-1.1.0.pruefdaten.json")
MODUL = os.path.join(HIER, "static", "panoptes-karte-1.1.0.js")
SHA = {PRUEF: "b515406370d56d1db71028fef0ff69b39bb2b317ff8854b7be8f764c5a0adcca",
       MODUL: "0801623fec901132cbeb725872b72e799a14ec4b6b49f45c5600ee6f6a80e2eb"}


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
