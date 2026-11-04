# -*- coding: utf-8 -*-
"""1.23 Apps & Display (Tacho, Launcher einrichten), Lese-Zugang ueber die Handy-Kopplung, "Mehr" in 7 Bereichen."""
import io
import json
import os
import re
import unittest
import urllib.error

import apps_display as ad
import evcockpit as ev
import neu_look
import panoptes_source as ps


class FakePv:
    """Wie panoptes_source.Panoptes + _http_direkt: 403/409 kommen als dict mit _status, andere Fehler als HTTPError, 401 als NichtAngemeldet."""

    def __init__(self, antworten):
        self.url, self.jwt = "http://auto:8080", "jwt-h"
        self.antworten, self.aufrufe = antworten, []
        self.anmeldungen = 0

    def _anmelden(self):
        self.anmeldungen += 1
        raise ps.KopplungAbgelaufen()

    def http(self, url, daten=None, jwt="", methode=None):
        pfad = url[len(self.url):]
        m = methode or ("POST" if daten is not None else "GET")
        self.aufrufe.append((m, pfad, daten))
        st, d = self.antworten.get((m, pfad), (404, {}))
        if st == 401:
            raise ps.NichtAngemeldet()
        if st in (403, 409):
            return dict(d, _status=st)
        if st >= 400:
            raise urllib.error.HTTPError(url, st, "x", {}, io.BytesIO(json.dumps(d).encode()))
        return dict(d)


LISTE = {"ok": True, "angeboten": True, "hinweisVerstanden": True, "jetzt": {"id": "design:horizont"},
         "eintraege": [{"id": "design:klar", "art": "design", "design": "klar", "name": "Klar", "waehlbar": True, "gewaehlt": False, "fahrt": True},
                       {"id": "design:horizont", "art": "design", "design": "horizont", "waehlbar": True, "gewaehlt": True, "fahrt": True},
                       {"id": "app:com.google.android.apps.maps", "art": "app", "name": "Google Maps", "navi": True, "waehlbar": True, "fahrt": True},
                       {"id": "app:com.waze", "art": "app", "name": "Waze", "waehlbar": False, "grund": "nicht_freigegeben"},
                       {"id": "app:x;rm", "art": "app", "name": "Boese", "waehlbar": True},
                       {"id": "app:com.yt", "art": "app", "name": "YT", "waehlbar": False, "grund": "warnleuchten_unbekannt", "video": True}]}

LAYOUT = {"format": "panoptes-launcher-layout", "version": 1, "seiten": [[{"id": "w1", "typ": "widget", "kachel": "fahrzeug", "x": 0, "y": 0, "b": 4, "h": 3}]],
          "dock": ["at.greenchili.surfmate"], "hintergrund": "panoptes", "zaehler": 10}


class TestTacho(unittest.TestCase):
    def test_liste_mit_saetzen_und_nur_gueltigen_ids(self):
        r = ad.tacho_lesen(FakePv({("GET", "/api/tacho/auswahl"): (200, LISTE)}))
        self.assertTrue(r["ok"])
        ids = [e["id"] for e in r["eintraege"]]
        self.assertNotIn("app:x;rm", ids)
        self.assertEqual(ids[:2], ["design:klar", "design:horizont"])
        waze = [e for e in r["eintraege"] if e["id"] == "app:com.waze"][0]
        self.assertEqual(waze["satz"], "Erst am Auto freigeben.")
        yt = [e for e in r["eintraege"] if e["id"] == "app:com.yt"][0]
        self.assertEqual(yt["satz"], "Auf diesem Auto nicht möglich.")
        self.assertTrue(yt["video"])
        self.assertEqual(r["jetzt"], "design:horizont")

    def test_ohne_recht_kommt_der_satz_von_panoptes(self):
        t = "Tacho-Recht fehlt – in Panoptes unter Gekoppelte Geräte einschalten."
        r = ad.tacho_lesen(FakePv({("GET", "/api/tacho/auswahl"): (403, {"ok": False, "grund": "nicht_erlaubt", "recht": "tacho", "text": t})}))
        self.assertEqual(r, {"ok": False, "recht": "tacho", "text": t})

    def test_alte_kopplung_ohne_art_und_altes_panoptes(self):
        r = ad.tacho_lesen(FakePv({("GET", "/api/tacho/auswahl"): (403, {"ok": False, "grund": "nur_mit_login"})}))
        self.assertIn("Steuern einrichten", r["text"])
        r = ad.tacho_lesen(FakePv({}))
        self.assertTrue(r.get("alt"))
        self.assertFalse(r["ok"])

    def test_nicht_angeboten(self):
        r = ad.tacho_lesen(FakePv({("GET", "/api/tacho/auswahl"): (200, {"ok": True, "angeboten": False, "grund": "dilink5_x", "eintraege": []})}))
        self.assertFalse(r["angeboten"])
        self.assertEqual(r["satz"], "Auf diesem Auto nicht möglich.")

    def test_waehlen_prueft_die_id_vor_dem_senden(self):
        pv = FakePv({("POST", "/api/tacho/auswahl"): (200, {"ok": True})})
        self.assertFalse(ad.tacho_waehlen(pv, "app:../x")["ok"])
        self.assertFalse(ad.tacho_waehlen(pv, None)["ok"])
        self.assertEqual(pv.aufrufe, [])
        self.assertTrue(ad.tacho_waehlen(pv, "design:sport")["ok"])
        self.assertEqual(pv.aufrufe, [("POST", "/api/tacho/auswahl", {"id": "design:sport"})])

    def test_waehlen_409_als_satz(self):
        pv = FakePv({("POST", "/api/tacho/auswahl"): (409, {"ok": False, "grund": "nur_im_stand"})})
        self.assertEqual(ad.tacho_waehlen(pv, "app:com.google.android.apps.maps"), {"ok": False, "text": "Nur in P möglich."})

    def test_normal(self):
        pv = FakePv({("POST", "/api/tacho/normal"): (200, {"ok": True})})
        self.assertTrue(ad.tacho_normal(pv)["ok"])
        self.assertEqual(pv.aufrufe[0][:2], ("POST", "/api/tacho/normal"))

    def test_ohne_kopplung_und_abgelaufen(self):
        self.assertIn("Erst mit Panoptes verbinden", ad.tacho_lesen(None)["text"])
        r = ad.tacho_lesen(FakePv({("GET", "/api/tacho/auswahl"): (401, {})}))
        self.assertEqual(r["text"], ad.TEXT_ABGELAUFEN)


class TestLauncher(unittest.TestCase):
    def antworten(self, **mehr):
        a = {("GET", "/api/launcher/v1/layout"): (200, {"layout": LAYOUT, "geaendert": 5, "quelle": "auto", "standard": False}),
             ("GET", "/api/launcher/v1/layout/apps"): (200, {"ok": True, "apps": [{"paket": "com.spotify.music", "name": "Spotify", "video": False},
                                                                                  {"paket": "kaputt", "name": "x"}]}),
             ("GET", "/api/appupdate/launcher"): (200, {"paket": "at.greenchili.panoptes.launcher", "installiert": 12})}
        a.update(mehr)
        return a

    def test_lesen(self):
        r = ad.launcher_lesen(FakePv(self.antworten()))
        self.assertTrue(r["ok"])
        self.assertEqual(r["geaendert"], 5)
        self.assertEqual([a["paket"] for a in r["apps"]], ["com.spotify.music"])
        self.assertEqual(r["stand"], {"installiert": True})

    def test_lesen_ohne_recht(self):
        t = "Launcher-Recht fehlt – in Panoptes unter Gekoppelte Geräte einschalten."
        pv = FakePv({("GET", "/api/launcher/v1/layout"): (403, {"ok": False, "grund": "nicht_erlaubt", "recht": "launcher", "text": t})})
        self.assertEqual(ad.launcher_lesen(pv)["text"], t)
        self.assertEqual(len(pv.aufrufe), 1)          # danach nichts weiter gefragt

    def test_speichern_mit_basis_und_409(self):
        pv = FakePv({("PUT", "/api/launcher/v1/layout"): (200, {"ok": True, "geaendert": 9, "bereinigt": 1, "layout": LAYOUT})})
        r = ad.launcher_speichern(pv, LAYOUT, 5)
        self.assertEqual((r["ok"], r["geaendert"], r["bereinigt"]), (True, 9, 1))
        self.assertEqual(pv.aufrufe[0], ("PUT", "/api/launcher/v1/layout", {"layout": LAYOUT, "basis": 5}))
        pv = FakePv({("PUT", "/api/launcher/v1/layout"): (409, {"ok": False, "grund": "neuer", "layout": LAYOUT, "geaendert": 11})})
        r = ad.launcher_speichern(pv, LAYOUT, 5)
        self.assertTrue(r["neuer"])
        self.assertEqual(r["geaendert"], 11)
        self.assertEqual(r["text"], ad.TEXT_NEUER)

    def test_falsches_format_geht_nicht_raus(self):
        pv = FakePv({})
        self.assertFalse(ad.launcher_speichern(pv, {"format": "x"}, 1)["ok"])
        self.assertFalse(ad.launcher_speichern(pv, dict(LAYOUT, seiten=[[{"n": "x" * 70000}]]), 1)["ok"])
        self.assertFalse(ad.launcher_speichern(pv, LAYOUT, "abc")["ok"])
        self.assertEqual(pv.aufrufe, [])

    def test_standard_und_oeffnen_senden_nur_das_feste(self):
        pv = FakePv({("POST", "/api/launcher/v1/layout/standard"): (200, {"ok": True, "geaendert": 3, "layout": LAYOUT, "standard": True}),
                     ("POST", "/api/appupdate/launcher"): (200, {"ok": True, "installiert": 12})})
        self.assertTrue(ad.launcher_standard(pv)["ok"])
        self.assertTrue(ad.launcher_oeffnen(pv)["ok"])
        self.assertEqual(pv.aufrufe[1], ("POST", "/api/appupdate/launcher", {"aktion": "oeffnen"}))

    def test_oeffnen_nicht_installiert(self):
        pv = FakePv({("POST", "/api/appupdate/launcher"): (200, {"ok": False, "grund": "nicht_installiert"})})
        self.assertIn("nicht installiert", ad.launcher_oeffnen(pv)["text"])


class TestSicherheit(unittest.TestCase):
    def test_nur_die_vertragspfade(self):
        src = open(os.path.join(os.path.dirname(__file__), "apps_display.py"), encoding="utf-8").read()
        src = src[:src.index("EN = {")]            # Code und Seiten, ohne die Uebersetzungstabelle
        pfade = set(re.findall(r'"(/api/[^"]*)"', src))
        self.assertEqual(pfade, {"/api/tacho/auswahl", "/api/tacho/normal", "/api/launcher/v1/layout", "/api/appupdate/launcher"})
        for wort in ("vehicle", "aufsperren", "unlock", "installieren", "entfernen\"", "hupe", "horn"):
            self.assertNotIn(wort, src.lower().replace("installiert", ""), wort)

    def test_alle_texte_haben_englisch(self):
        for t in list(ad.TACHO_GRUENDE.values()) + [ad.TACHO_SONST, ad.TEXT_ALT, ad.TEXT_KOPPLUNG, ad.TEXT_WEG, ad.TEXT_ABGELAUFEN, ad.TEXT_NEUER]:
            self.assertIn(t, ad.EN, t)
        for s in (ad.TACHO_SEITE, ad.LAUNCHER_SEITE):
            for t in re.findall(r"__T\('([^']+)'\)", s):
                self.assertIn(t, ev._I18N, t)
            for t in re.findall(r"msg\('([^']+)'\)", s):
                if re.search("[A-Za-z]", t):
                    self.assertIn(t, ev._I18N, t)


class TestBereiche(unittest.TestCase):
    def test_sieben_bereiche_in_fester_reihenfolge(self):
        h = neu_look.hub_html("1.23")
        ids = re.findall(r'class=bereich id="b_([a-z]+)"', h)
        self.assertEqual(ids, ["start", "car", "guard", "drive", "auto", "apps", "system"])
        namen = [n for _b, _i, n, _k in neu_look.BEREICHE]
        self.assertEqual(namen, ["Start", "Steuerung", "Kameras & Wächter", "Fahrten & Laden", "Regeln", "Apps & Display", "Einstellungen"])
        self.assertNotIn("Automationen", h)
        self.assertIn('href="/tacho"', h)
        self.assertIn('href="/launcher"', h)

    def test_ausgeblendet_statt_ausgegraut(self):
        h = neu_look.hub_html("1", {"panoptes": False, "steuern": False})
        for z in ('href="/tacho"', 'href="/launcher"', 'href="/#k-klima"', 'href="/handy"', 'id="b_apps"', 'id="b_car"'):
            self.assertNotIn(z, h)
        self.assertIn('href="/setup"', h)
        h = neu_look.hub_html("1", {"panoptes": True, "steuern": False})
        self.assertIn('href="/tacho"', h)
        self.assertNotIn('href="/#k-klima"', h)

    def test_englisch(self):
        for _b, _i, n, ks in neu_look.BEREICHE:
            self.assertIn(n, neu_look.EN)


class TestLeseZugang(unittest.TestCase):
    """1.23: Lesen geht ueber die Handy-Kopplung (wie ueber die Bruecke schon seit 1.22); "Handy verbinden" bleibt bei der Cockpit-Kopplung."""

    def setUp(self):
        import evcockpit as e
        self.e = e
        self.alt = dict(e._CFG)
        e._PANOPTES.update(key=None, obj=None, aktiv=None, handy_kaputt="")
        e._PANOPTES_K.update(key=None, obj=None)
        e._CFG.clear()
        e._CFG.update(panoptes=True, panoptes_url="http://auto:8080", panoptes_jwt="jwt-k")

    def tearDown(self):
        self.e._CFG.clear()
        self.e._CFG.update(self.alt)
        self.e._PANOPTES.update(key=None, obj=None, aktiv=None, handy_kaputt="")
        self.e._PANOPTES_K.update(key=None, obj=None)

    def test_ohne_handy_kopplung_die_cockpit_kopplung(self):
        self.assertEqual(self.e._panoptes_obj().jwt, "jwt-k")

    def test_mit_handy_kopplung_nur_sie(self):
        self.e._CFG["panoptes_handy_jwt"] = "jwt-h"
        pv = self.e._panoptes_obj()
        self.assertEqual(pv.jwt, "jwt-h")
        self.assertIs(self.e._PANOPTES["aktiv"], pv)
        self.assertEqual(self.e._panoptes_obj_kopplung().jwt, "jwt-k")
        self.assertIs(self.e._panoptes_obj(), pv)                   # gleiches Objekt, kein Neubau
        self.e._CFG["panoptes_handy_jwt"] = "jwt-h2"                # still verlaengert
        self.assertEqual(self.e._panoptes_obj().jwt, "jwt-h2")

    def test_rueckfall_wenn_handy_zugang_nicht_mehr_gilt(self):
        self.e._CFG["panoptes_handy_jwt"] = "jwt-h"
        self.e._PANOPTES["handy_kaputt"] = "jwt-h"
        self.assertEqual(self.e._panoptes_obj().jwt, "jwt-k")
        self.e._CFG["panoptes_handy_jwt"] = "jwt-neu"               # neu eingerichtet -> wieder Handy
        self.assertEqual(self.e._panoptes_obj().jwt, "jwt-neu")

    def test_handy_verbinden_nutzt_die_cockpit_kopplung(self):
        src = open(os.path.join(os.path.dirname(__file__), "evcockpit.py"), encoding="utf-8").read()
        a = src.index('if u.path == "/handy/qr/anfrage":')
        b = src.index('if u.path == "/bruecke/einrichten":', a)
        self.assertEqual(src[a:b].count("pv = _panoptes_obj_kopplung()"), 2)
        self.assertNotIn("_panoptes_obj()", src[a:b])

    def test_seiten_und_endpunkte_sind_verdrahtet(self):
        src = open(os.path.join(os.path.dirname(__file__), "evcockpit.py"), encoding="utf-8").read()
        for p in ('"/tacho"', '"/launcher"', '"/tacho/daten"', '"/launcher/daten"', '"/tacho/waehlen"', '"/launcher/speichern"', '"/launcher/oeffnen"'):
            self.assertIn(p, src)
        self.assertEqual(self.e._I18N["Launcher einrichten"], "Set up launcher")


if __name__ == "__main__":
    unittest.main()
