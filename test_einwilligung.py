"""Regel 2 (Alfred, 21.10.2026): Daten an unsere oder fremde Server nur mit ausdruecklicher Einwilligung, Standard AUS.
Prueft am Quelltext, dass jedes Einwilligungs-Haekchen im Assistenten ohne `checked` ausgeliefert wird und dass
Community-Karte und 3D-Modell nur bei ausdruecklicher Zustimmung laufen (fehlender Schluessel = aus)."""
import os
import re
import unittest

QUELLE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()

# Haekchen, hinter denen Daten das Geraet verlassen
EINWILLIGUNGEN = ("count", "upd", "price", "chargers", "kartecommunity", "planer", "planerfahrten", "modell3d", "lan")


class TestEinwilligung(unittest.TestCase):
    def test_haekchen_standard_aus(self):
        for i in EINWILLIGUNGEN:
            tags = re.findall(r"<input type=checkbox id=%s\b[^>]*>" % i, QUELLE)
            self.assertEqual(len(tags), 1, i)
            ohne_werte = re.sub(r'"[^"]*"', '""', tags[0])          # onchange="...this.checked..." zaehlt nicht
            self.assertNotRegex(ohne_werte, r"\schecked(?=[\s>=])", "%s ist vorausgewaehlt" % i)

    def test_karte_und_3d_nur_mit_zustimmung(self):
        self.assertIn('stil = KARTE_STIL if _CFG.get("karte") == "community" else ""', QUELLE)
        self.assertIn('_CFG.get("karte") != "community"', QUELLE)
        self.assertEqual(QUELLE.count('_CFG.get("modell3d") is not True'), 2)
        self.assertNotIn('_CFG.get("modell3d") is False', QUELLE)
        self.assertIn("document.getElementById('kartecommunity').checked=VOR.karte==='community'", QUELLE)
        self.assertIn("document.getElementById('modell3d').checked=VOR.modell3d===true", QUELLE)

    def test_ping_nur_mit_haekchen(self):
        self.assertRegex(QUELLE, r'def ping_optin\(\):[\s\S]{0,400}if not _CFG\.get\("count_optin"\):\s+return')
        self.assertRegex(QUELLE, r'if _CFG\.get\("update_check"\):\s+req = urllib\.request\.Request\(VERSION_URL')


if __name__ == "__main__":
    unittest.main()
