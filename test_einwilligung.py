"""Regel 2 (Alfred, 21.10.2026): Daten an unsere oder fremde Server nur mit ausdruecklicher Einwilligung, Standard AUS.
Prueft am Quelltext, dass jedes Einwilligungs-Haekchen im Assistenten ohne `checked` ausgeliefert wird, dass ohne Wahl
keine Kartenkacheln geladen werden (auch nicht von OpenStreetMap) und dass ein Widerruf der Zaehlung beim Server loescht."""
import os
import re
import unittest

QUELLE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()

# Haekchen, hinter denen Daten das Geraet verlassen
EINWILLIGUNGEN = ("count", "upd", "price", "chargers", "planer", "planerfahrten", "modell3d", "lan")


def _ohne_werte(tag):
    return re.sub(r'"[^"]*"', '""', tag)          # onchange="...this.checked..." zaehlt nicht


class TestEinwilligung(unittest.TestCase):
    def test_haekchen_standard_aus(self):
        for i in EINWILLIGUNGEN:
            tags = re.findall(r"<input type=checkbox id=%s\b[^>]*>" % i, QUELLE)
            self.assertEqual(len(tags), 1, i)
            self.assertNotRegex(_ohne_werte(tags[0]), r"\schecked(?=[\s>=])", "%s ist vorausgewaehlt" % i)

    def test_kartenquelle_standard_keine(self):
        radios = {m.group(1): m.group(0) for m in re.finditer(r"<input type=radio name=kartenquelle id=kq_(\w+)[^>]*>", QUELLE)}
        self.assertEqual(set(radios), {"keine", "osm", "community"})
        self.assertRegex(_ohne_werte(radios["keine"]), r"\schecked(?=[\s>=])")
        for q in ("osm", "community"):
            self.assertNotRegex(_ohne_werte(radios[q]), r"\schecked(?=[\s>=])", q)
        # nur eine ausdrueckliche Wahl zaehlt; alter Wert "karte" (frueher vorausgewaehlt) zaehlt nicht
        self.assertIn('q = _CFG.get("kartenquelle")\n    return q if q in ("community", "osm") else "keine"', QUELLE.replace("\r\n", "\n"))
        self.assertIn('stil = KARTE_STIL if _kartenquelle() == "community" else ""', QUELLE)
        self.assertIn('_kartenquelle() != "community"', QUELLE)                     # Live-Belegung nur mit Community
        self.assertIn("if(EINW.kartenquelle==='keine')", QUELLE)                    # dann gar keine Kacheln
        self.assertNotIn('_CFG.get("karte") == "community"', QUELLE)

    def test_3d_nur_mit_zustimmung(self):
        self.assertEqual(QUELLE.count('_CFG.get("modell3d") is not True'), 2)
        self.assertNotIn('_CFG.get("modell3d") is False', QUELLE)
        self.assertIn("document.getElementById('modell3d').checked=VOR.modell3d===true", QUELLE)

    def test_ping_nur_mit_haekchen_und_widerruf_loescht(self):
        q = QUELLE.replace("\r\n", "\n")
        self.assertRegex(q, r'def ping_optin\(\):[\s\S]{0,1500}if not _CFG\.get\("count_optin"\):\s+return')
        self.assertIn('{"id": _CFG["_ping_loeschen"], "loeschen": True}', q)
        self.assertIn('c["_ping_loeschen"] = _CFG["install_id"]', q)
        self.assertRegex(q, r'if _CFG\.get\("update_check"\):\s+req = urllib\.request\.Request\(VERSION_URL')


class TestWiderrufLoescht(unittest.TestCase):
    def test_ping_loescht_und_vergisst_auftrag(self):
        import importlib
        import json
        import tempfile
        import urllib.request
        from unittest import mock
        os.environ["EVCOCKPIT_CFGDIR"] = tempfile.mkdtemp()
        import evcockpit
        evcockpit = importlib.reload(evcockpit)
        evcockpit._CFG.clear()
        evcockpit._CFG.update({"count_optin": False, "_ping_loeschen": "abc123"})
        gesendet = []

        class Antwort:
            def read(self):
                return b"{}"
        with mock.patch.object(urllib.request, "urlopen", side_effect=lambda req, timeout=0: gesendet.append(req) or Antwort()):
            evcockpit.ping_optin()
        self.assertEqual(len(gesendet), 1)                                   # nur die Loeschung, kein Zaehl-Ping
        self.assertEqual(json.loads(gesendet[0].data), {"id": "abc123", "loeschen": True})
        self.assertNotIn("_ping_loeschen", evcockpit._CFG)
        # ohne Netz bleibt der Auftrag stehen
        evcockpit._CFG["_ping_loeschen"] = "abc123"
        with mock.patch.object(urllib.request, "urlopen", side_effect=OSError("offline")):
            evcockpit.ping_optin()
        self.assertEqual(evcockpit._CFG.get("_ping_loeschen"), "abc123")


if __name__ == "__main__":
    unittest.main()
