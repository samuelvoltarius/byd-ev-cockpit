"""1.16: Panoptes-Logo - Favicon/Apple-Touch-Icon auf allen Seiten, Icons ueber die Whitelist, ICO mit allen Groessen."""
import os
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

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


class TestLogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ev.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.url = "http://127.0.0.1:%d" % cls.srv.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def hole(self, pfad):
        with urllib.request.urlopen(self.url + pfad) as r:
            return r.headers.get("Content-Type"), r.read()

    def test_icons_ausgeliefert(self):
        for pfad, typ in (("/static/logo-glyph.png", "image/png"), ("/static/favicon-32.png", "image/png"),
                          ("/static/apple-touch-icon.png", "image/png"), ("/favicon.ico", "image/x-icon"),
                          ("/static/ev-cockpit.ico", "image/x-icon")):
            t, b = self.hole(pfad)
            self.assertEqual(t, typ, pfad)
            self.assertGreater(len(b), 500, pfad)
        with self.assertRaises(urllib.error.HTTPError):
            self.hole("/static/evcockpit.py")                      # Whitelist bleibt

    def test_alle_seiten_mit_favicon(self):
        for vorlage in (ev.COCKPIT, ev.WIZARD, ev.ABOUT):
            h = ev._i18n(vorlage)
            self.assertIn('rel=icon href="/static/favicon.ico"', h)
            self.assertIn("apple-touch-icon", h)
        self.assertIn('class=brand-logo src="/static/logo-glyph.png"', ev.COCKPIT)

    def test_seiten_sind_gueltiges_utf8(self):
        """1.16-Fehler: ein als JSON-Escape eingefuegtes Emoji ergab einsame Surrogate -> leere Antwort."""
        for h in (ev.COCKPIT.replace("<!--ENERGIE-PANEL-->", ev.ENERGY_PANEL), ev.WIZARD, ev.ABOUT, ev.PANOPTES_SEITE):
            ev._i18n(h).encode("utf-8")

    def test_ico_alle_groessen(self):
        from PIL import Image
        ico = Image.open(ev.STATIC_DIR / "ev-cockpit.ico")
        self.assertEqual(sorted(ico.ico.sizes()), [(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])

    def test_verknuepfung_nur_im_paket(self):
        self.assertIsNone(ev._verknuepfung_ziel())                # Repo hat kein Start.bat
        ok, text = ev._verknuepfung_anlegen()
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
