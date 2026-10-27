"""Alle <script>-Bloecke der Seiten muessen als JavaScript parsen (1.18-Fehler: ein fehlendes Anfuehrungszeichen machte die ganze Seite leblos).
Prueft mit Node, falls vorhanden; sonst wird uebersprungen."""
import os
import re
import shutil
import subprocess
import tempfile
import unittest

_D = tempfile.mkdtemp()
_ALT = os.environ.get("EVCOCKPIT_CFGDIR")
os.environ["EVCOCKPIT_CFGDIR"] = _D
try:
    import evcockpit as ev
finally:
    if _ALT is None:
        os.environ.pop("EVCOCKPIT_CFGDIR", None)
    else:
        os.environ["EVCOCKPIT_CFGDIR"] = _ALT


class TestJsSyntax(unittest.TestCase):
    def test_skripte_parsen(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node nicht installiert (nur Entwicklungsrechner)")
        seiten = {"COCKPIT": ev.COCKPIT.replace("<!--ENERGIE-PANEL-->", ev.ENERGY_PANEL), "WIZARD": ev.WIZARD, "PANOPTES": ev.PANOPTES_SEITE, "ABOUT": ev.ABOUT, "MEIN_AUTO": __import__("mein_auto_seite").seite("https://x/s.json", "http://100.1.2.3:8180")}
        for name, h in seiten.items():
            h = ev._i18n(h)
            for i, m in enumerate(re.finditer(r"<script(?![^>]*\bsrc=)(?![^>]*type=[\"']?(?:importmap|application/json))[^>]*>(.*?)</script>", h, re.S)):
                f = os.path.join(_D, "%s_%d.js" % (name, i))
                open(f, "w", encoding="utf-8").write(m.group(1))
                r = subprocess.run([node, "--check", f], capture_output=True, text=True, stdin=subprocess.DEVNULL)
                self.assertEqual(r.returncode, 0, "%s Skript %d: %s" % (name, i, r.stderr[:300]))


if __name__ == "__main__":
    unittest.main()
