"""1.20: Startseite "Mein Auto" - Aufbau wie im freigegebenen Mockup; kein Aufsperren, kein Finden/Blinken (Regel A+)."""
import os
import re
import tempfile
import unittest

_D = tempfile.mkdtemp()
os.environ["EVCOCKPIT_CFGDIR"] = _D
import evcockpit as ev  # noqa: E402
import mein_auto_seite  # noqa: E402

H = mein_auto_seite.seite("https://x/stil.json", "http://100.1.2.3:8180")


class MeinAuto(unittest.TestCase):
    def test_kacheln_in_der_reihenfolge_des_mockups(self):
        folge = ["t_laden", "t_klima", "t_tuer", "t_reifen", "t_waech", "id=map", "t_warn", 'id="alle"' if 'id="alle"' in H else "id=alle"]
        pos = [H.index(x) for x in folge]
        self.assertEqual(pos, sorted(pos))

    def test_schnellknoepfe_genau_drei(self):
        self.assertEqual(re.findall(r"id=(a_[a-z]+) onclick", H), ["a_heat", "a_lock", "a_off", "a_setup"])   # a_setup = einmal koppeln
        self.assertIn("cmd('heat')", H)
        self.assertIn("cmd('off')", H)
        self.assertIn("zusperren()", H)

    def test_a_plus_kein_aufsperren_kein_finden(self):
        for verboten in ("unlock", "Aufsperren", "cmd('find')", "Auto finden", "Blinken", "Hupe"):
            self.assertNotIn(verboten, H)

    def test_panoptes_logo_und_alle_funktionen(self):
        self.assertIn("/static/panoptes-logo.svg", H)
        self.assertIn('href="http://100.1.2.3:8180/"', H)
        self.assertTrue((ev.STATIC_DIR / "panoptes-logo.svg").exists())
        self.assertIn("panoptes-logo.svg", ev.ICONS)

    def test_mehr_menue_hat_das_cockpit_eigene(self):
        for ziel in ('href="/setup"', 'href="/klassisch#d_energie"', 'href="/klassisch"', 'href="/about"'):
            self.assertIn(ziel, H)

    def test_karte_nur_mit_stil(self):
        self.assertIn("const KARTEN_STIL='https://x/stil.json'", H)
        self.assertIn("const KARTEN_STIL=''", mein_auto_seite.seite("", ""))

    def test_alte_seite_bleibt_unter_klassisch(self):
        self.assertIn("kt_wb", ev.COCKPIT)           # alte Ansicht ist unveraendert vorhanden


if __name__ == "__main__":
    unittest.main()


class Nachbesserung120(unittest.TestCase):
    def test_modellname_nur_dolphin_surf(self):
        self.assertIn("nm='BYD Dolphin Surf'", H)
        self.assertIn("modell(S&&S.model).nm", H)             # Bildunterschrift nimmt den bereinigten Namen
        self.assertNotIn("el('sub').textContent=[s.model", H)

    def test_laden_kachel_zeigt_leistung_restzeit_ziel(self):
        for t in ("charge_power", "charge_remaining", "lp.zielSoc", "Restzeit meldet Panoptes gerade nicht"):
            self.assertIn(t, H)
        self.assertNotIn("kWh/100 km", H)                      # kein Verbrauch in der Laden-Kachel

    def test_klima_nie_nur_strich(self):
        self.assertIn("__T('unbekannt')", H)

    def test_kein_sprachfeld_unten_rechts(self):
        self.assertIn("evc-ohne-sprachfeld", H)
        self.assertIn("meta[name=evc-ohne-sprachfeld]", ev.I18N_BODY)
        self.assertNotIn("evc-ohne-sprachfeld", ev.COCKPIT)    # alte Seite behaelt es
