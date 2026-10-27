"""1.20: Startseite "Mein Auto" - Aufbau wie im freigegebenen Mockup; kein Aufsperren, kein Finden/Blinken (Regel A+)."""
import os
import re
import tempfile
import unittest

_D = tempfile.mkdtemp()
os.environ["EVCOCKPIT_CFGDIR"] = _D
import evcockpit as ev  # noqa: E402
import mein_auto_seite  # noqa: E402

H = mein_auto_seite.seite("https://x/stil.json", "http://100.1.2.3:8180", ev.COCKPIT)


class MeinAuto(unittest.TestCase):
    def test_kacheln_in_der_reihenfolge_des_mockups(self):
        folge = ['id="t_route"', 'id="t_laden"', 'id="t_klima"', 'id="t_camping"', "id=t_tuer", "id=t_reifen", "id=t_waech", "id=t_pos", "id=t_warn", "id=alle"]
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
        self.assertIn("const KARTEN_STIL=''", mein_auto_seite.seite("", "", ev.COCKPIT))

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


class Bedienkacheln121(unittest.TestCase):
    def test_route_und_camping_sind_uebernommen_nicht_neu(self):
        for t in ("function rPlanen", "function rZeigen", "async function rAnAuto", "id=rziel", "id=rbtn", "id=rstopps",
                  "function campingZeichnen", "async function cpPost", "id=cp_status", "id=cp_plan", "function cpPlan"):
            self.assertIn(t, H)
        self.assertNotIn("id=rmap", H)                         # keine Karte in der Kachel

    def test_ohne_alte_ansicht_kein_absturz(self):
        h = mein_auto_seite.seite("", "")
        self.assertIn("id=\"t_route\"", h)

    def test_klima_temperatur_17_bis_33(self):
        self.assertIn("min=17 max=33 value=25", H)
        self.assertIn("'&t='+TEMP", H)

    def test_laden_kachel_rueckfrage_und_freigabe(self):
        for t in ("bestaetigung_noetig", "/wallbox/freigabe", "/wallbox/steuern", "Steuern erlauben", "Ladeplan: aus", "braucht Panoptes 0.1.20"):
            self.assertIn(t, H)

    def test_sitzheizung_ehrlich(self):
        self.assertIn("gerade nicht möglich", H)
        self.assertIn("seatOk", H)

    def test_cmd_temperatur_durchgereicht(self):
        import panoptes_source as ps
        import time
        gesichert = dict(ev._CFG)
        ev._CFG.update(panoptes=True, panoptes_url="http://127.0.0.1:9", panoptes_jwt="x", panoptes_handy_jwt="H")
        gesehen = []
        alt = ps.handy_aktion
        ps.handy_aktion = lambda url, jwt, a, f=None, **k: (gesehen.append((a, f)) or {"ok": True, "weg": "lokal", "bestaetigt": True})
        try:
            ev._run_cmd("heat", 22.4)
            time.sleep(0.5)
            ev._run_cmd("heat", 40)
            time.sleep(0.5)
            ev._run_cmd("heat", None)
            time.sleep(0.5)
        finally:
            ps.handy_aktion = alt
            ev._CFG.clear()
            ev._CFG.update(gesichert)
            ev._HOLD_UNTIL = 0             # _run_cmd haelt den Poller 45 s an - hier nicht an andere Tests weitergeben
        self.assertEqual([g[1]["tempC"] for g in gesehen], [22, 33, 26])

class WaechterFenster1203(unittest.TestCase):
    def test_kachel_oeffnet_fenster_im_cockpit(self):
        h = mein_auto_seite.seite("", "http://100.1.2.3:8180", ev.COCKPIT)
        self.assertIn('id=t_waech onclick="wmAuf()"', h)
        self.assertIn("id=wm_strip", h)
        self.assertNotIn("waechter.html", h)                  # kein Sprung in die Panoptes-Weboberflaeche
