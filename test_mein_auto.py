"""1.20: Startseite "Mein Auto" - Aufbau wie im freigegebenen Mockup; kein Aufsperren, kein Finden/Blinken (Regel A+)."""
import os
import re
import tempfile
import unittest

_D = tempfile.mkdtemp()
os.environ["EVCOCKPIT_CFGDIR"] = _D
import evcockpit as ev  # noqa: E402
import mein_auto_seite  # noqa: E402
import neu_look  # noqa: E402
import anpassen  # noqa: E402

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

    def test_mehr_fuehrt_zur_neuen_seite_und_nichts_zur_alten_ansicht(self):
        self.assertIn("location.href='/mehr'", H)
        self.assertNotIn("/klassisch", H)
        hub = neu_look.hub_html("1.21")
        for ziel in ('href="/setup"', 'href="/panoptes"', 'href="/energie"', 'href="/laden"', 'href="/fahrten"', 'href="/aufnahmen"',
                     'href="/karte"', 'href="/takt"', 'href="/about"'):
            self.assertIn(ziel, hub)

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
        # 1.21: auf keiner Seite mehr die schwebende DE-Pille; Sprache wechselt man unter Mehr -> Deutsch/English
        self.assertNotIn("position:fixed;right:12px;bottom:12px", ev.I18N_BODY.split("return;   // 1.21")[0])
        self.assertIn("return;   // 1.21", ev.I18N_BODY)
        self.assertIn("Deutsch / English", neu_look.hub_html("1"))


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
        for t in ("bestaetigung_noetig", "/wallbox/freigabe", "/wallbox/steuern", "Steuern erlauben", "lp_box", "/panoptes/ladeplan"):
            self.assertIn(t, H)
        self.assertNotIn("braucht Panoptes 0.1.20", H)

    def test_sitzheizung_ueber_panoptes_mit_rueckfrage(self):
        self.assertIn("id=seatP", H)
        self.assertIn("function sitz(w,n)", H)
        self.assertIn("confirm(", H.split("function sitz(w,n)")[1].split("}")[0])
        import panoptes_source as ps
        import time
        gesichert = dict(ev._CFG)
        ev._CFG.update(panoptes=True, panoptes_url="http://127.0.0.1:9", panoptes_jwt="x", panoptes_handy_jwt="H")
        gesehen = []
        alt = ps.handy_aktion
        ps.handy_aktion = lambda url, jwt, a, f=None, **k: (gesehen.append((a, f)) or {"ok": True, "weg": "lokal", "bestaetigt": True})
        try:
            ev._run_cmd("sitz_f_2")
            time.sleep(0.5)
            ev._run_cmd("sitz_b_0")
            time.sleep(0.5)
        finally:
            ps.handy_aktion = alt
            ev._CFG.clear()
            ev._CFG.update(gesichert)
            ev._HOLD_UNTIL = 0
        self.assertEqual(gesehen, [("sitzheizung", {"sitz": "fahrer", "stufe": 2}), ("sitzheizung", {"sitz": "beifahrer", "stufe": 0})])

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

    def test_ladeplan_zu_alt_nur_bei_404(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()
        self.assertIn('"zu_alt" if e.code == 404 else "zugriff" if e.code in (401, 403)', src)

    def test_dropdowns_lesbar(self):
        h = ev._i18n("<html><head><meta charset=utf-8></head><body></body></html>")
        self.assertIn("color-scheme:dark", h)
        self.assertIn("option:checked", h)


class Boersenpreis1204(unittest.TestCase):
    def test_nur_mit_schalter_und_ohne_festen_tarif(self):
        alt_cfg, alt_t = dict(ev._CFG), dict(ev._TARIF)
        try:
            ev._TARIF.update(ts=9e18, art=None)
            ev._CFG["show_price"] = False
            self.assertFalse(ev._preis_erlaubt(False))
            ev._CFG["show_price"] = True
            self.assertTrue(ev._preis_erlaubt(False))
            for art in ("fest", "zeit", "zeittarif"):
                ev._TARIF["art"] = art
                self.assertFalse(ev._preis_erlaubt(False), art)
            for art in ("boerse_aus", "dynamisch", "irgendwas"):     # ab 1.21: NUR genau "boerse" erlaubt Boersenpreise
                ev._TARIF["art"] = art
                self.assertFalse(ev._preis_erlaubt(False), art)
            ev._TARIF["art"] = "boerse"
            self.assertTrue(ev._preis_erlaubt(False))
            ev._CFG["show_price"] = False
            self.assertFalse(ev._preis_erlaubt(False))
        finally:
            ev._CFG.clear()
            ev._CFG.update(alt_cfg)
            ev._TARIF.clear()
            ev._TARIF.update(alt_t)


class Unterseiten121(unittest.TestCase):
    """1.21: jede frueher nur in /klassisch erreichbare Funktion hat eine Seite im neuen Look; die alte Ansicht wird nicht mehr ausgeliefert."""
    def test_jede_seite_zeigt_nur_ihren_bereich(self):
        for pfad, (titel, sicht, auf) in neu_look.SEITEN.items():
            h = neu_look.sektion_html(ev.COCKPIT, pfad)
            self.assertIn("name=evc-neu", h, pfad)
            for i in neu_look.ALLE_BEREICHE:
                if i not in sicht and i != "taktseite":
                    self.assertIn("#%s{display:none!important}" % i, h, (pfad, i))
                else:
                    self.assertNotIn("#%s{display:none!important}" % i, h, (pfad, i))

    def test_klassisch_wird_nicht_mehr_im_alten_design_ausgeliefert(self):
        src = open(os.path.join(os.path.dirname(__file__), "evcockpit.py"), encoding="utf-8").read()
        self.assertIn('p in ("/mehr", "/klassisch")', src)
        self.assertNotIn('elif p != "/klassisch"', src)

    def test_alle_unterseiten_tragen_das_neue_stylesheet(self):
        for h in (ev._i18n(ev.ABOUT.replace("__VERSION__", "1")), ev._i18n(ev.PANOPTES_SEITE), ev._i18n(ev.WIZARD)):
            self.assertIn("id=uni", h)
            self.assertNotIn("font:16px/1.55 system-ui", h)


class Anpassen121(unittest.TestCase):
    def test_standard_und_bereinigen(self):
        std = anpassen.standard()
        self.assertEqual(std["reihe"], list(anpassen.KACHELN))
        self.assertEqual(std["kacheln"]["pos"]["gr"], "M")
        self.assertEqual(anpassen.bereinigen(None), std)
        self.assertEqual(anpassen.bereinigen("x"), std)

    def test_ungueltiges_faellt_weg_fehlendes_kommt_dazu(self):
        r = anpassen.bereinigen({"reihe": ["warn", "route", "warn", "unsinn", 5], "kacheln": {"route": {"gr": "XL", "aus": "ja"}, "warn": {"gr": "L", "aus": True}, "boese": {"gr": "S"}}})
        self.assertEqual(r["reihe"][:2], ["warn", "route"])
        self.assertEqual(sorted(r["reihe"]), sorted(anpassen.KACHELN))
        self.assertEqual(r["kacheln"]["route"], {"gr": "S", "aus": False})
        self.assertEqual(r["kacheln"]["warn"], {"gr": "L", "aus": True})
        self.assertNotIn("boese", r["kacheln"])

    def test_nur_im_anpassen_modus_aenderbar(self):
        self.assertIn('onclick="anpEin()"', H)
        self.assertIn(".anpbar{display:none}", H)
        self.assertIn("ANPAN&&", H)                    # Klicks auf Kacheln sind im Modus gesperrt, nicht davor
        self.assertIn("/layout", H)
        for g in ("anpReset", "anpGr", "anpSicht", "anpBew", "anpZiehen"):
            self.assertIn("function " + g, H)
