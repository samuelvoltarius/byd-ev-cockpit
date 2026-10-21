"""Regel S: Geheimnisse nie im Klartext in config.json, wo ein Schluesselbund da ist (Windows DPAPI, macOS Keychain,
Linux Secret Service); sonst Rueckfall 0600 mit Warnung. macOS/Linux werden mit einem nachgebauten Schluesselbund
geprueft (subprocess ersetzt) - echte Geraete stehen hier nicht zur Verfuegung."""
import importlib
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import geheim

GEHEIM = {"panoptes_jwt": "eyJhbGciOi.jwt-geheim", "planer_token": "g:" + "ab" * 32, "password": "pw-xyz"}


class Schluesselbund:
    """Nachbau von `security` (macOS) und `secret-tool` (Linux); merkt sich jeden Aufruf."""

    def __init__(self, kaputt_lesen=False):
        self.daten, self.aufrufe, self.kaputt_lesen = {}, [], kaputt_lesen

    def run(self, cmd, input=None, capture_output=True, text=True, timeout=0):
        self.aufrufe.append((list(cmd), input))
        r = mock.Mock(returncode=0, stdout="")
        if cmd[:2] == ["security", "-i"]:                       # add-generic-password ... -w "<geheim>" via stdin
            teile = input.split('"')
            self.daten[teile[1]] = teile[5].replace('\\"', '"').replace("\\\\", "\\")
        elif cmd[:2] == ["security", "find-generic-password"]:
            k = cmd[cmd.index("-a") + 1]
            if k in self.daten and not self.kaputt_lesen:
                r.stdout = self.daten[k] + "\n"
            else:
                r.returncode = 44
        elif cmd[:2] == ["security", "delete-generic-password"]:
            self.daten.pop(cmd[cmd.index("-a") + 1], None)
        elif cmd[:2] == ["secret-tool", "store"]:
            self.daten[tuple(cmd[4:])] = input
        elif cmd[:2] == ["secret-tool", "lookup"]:
            k = tuple(cmd[2:])
            if k in self.daten and not self.kaputt_lesen:
                r.stdout = self.daten[k]
            else:
                r.returncode = 1
        elif cmd[:2] == ["secret-tool", "clear"]:
            self.daten.pop(tuple(cmd[2:]), None)
        return r


def _mit(plattform, werkzeug, sb):
    return [mock.patch.object(sys, "platform", plattform),
            mock.patch("shutil.which", side_effect=lambda n: "/usr/bin/" + n if n == werkzeug else None),
            mock.patch("subprocess.run", side_effect=sb.run)]


class TestSchluesselbund(unittest.TestCase):
    def setUp(self):
        geheim._GESPEICHERT.clear()

    def _rundlauf(self, plattform, werkzeug):
        sb = Schluesselbund()
        ps = _mit(plattform, werkzeug, sb)
        for p in ps:
            p.start()
        try:
            cfg = dict(GEHEIM, vin="LDEMO", model="Seagull")
            platte = geheim.fuer_platte(cfg, "prof1")
            text = json.dumps(platte)
            for v in GEHEIM.values():
                self.assertNotIn(v, text)                                   # kein Geheimnis in der Datei
            self.assertEqual(platte["panoptes_jwt"], "keychain:panoptes_jwt")
            self.assertEqual(geheim.WARNUNG, "")
            for cmd, _ in sb.aufrufe:                                       # nie auf der Kommandozeile
                for v in GEHEIM.values():
                    self.assertNotIn(v, " ".join(cmd))
            geheim._GESPEICHERT.clear()
            self.assertEqual({k: geheim.aus_platte(platte, "prof1")[k] for k in GEHEIM}, GEHEIM)
            self.assertEqual(geheim.aus_platte(platte, "anderes")["panoptes_jwt"], "")   # Profile getrennt
            cfg2 = dict(cfg, planer_token="")                                # Wert entfernt -> auch im Schluesselbund
            geheim.fuer_platte(cfg2, "prof1")
            self.assertEqual(geheim.aus_platte(platte, "prof1")["planer_token"], "")
        finally:
            for p in ps:
                p.stop()

    def test_macos_keychain(self):
        self._rundlauf("darwin", "security")

    def test_linux_secret_service(self):
        self._rundlauf("linux", "secret-tool")

    def test_zuruecklesen_gescheitert_bleibt_mit_warnung(self):
        sb = Schluesselbund(kaputt_lesen=True)
        ps = _mit("linux", "secret-tool", sb)
        for p in ps:
            p.start()
        try:
            platte = geheim.fuer_platte(dict(GEHEIM), "p")
            self.assertEqual(platte["panoptes_jwt"], GEHEIM["panoptes_jwt"])     # nicht verloren
            self.assertTrue(geheim.WARNUNG)
        finally:
            for p in ps:
                p.stop()

    def test_rueckfall_ohne_schluesselbund(self):
        with mock.patch.object(sys, "platform", "linux"), mock.patch("shutil.which", return_value=None):
            platte = geheim.fuer_platte(dict(GEHEIM), "p")
            self.assertEqual(platte["password"], "pw-xyz")
            self.assertTrue(geheim.WARNUNG)
            self.assertFalse(geheim.noch_klartext(platte))                  # kein Schluesselbund -> nichts zu migrieren
        geheim.fuer_platte({"vin": "x"}, "p")
        self.assertEqual(geheim.WARNUNG, "")                                 # ohne Geheimnisse keine Warnung


@unittest.skipUnless(sys.platform == "win32", "DPAPI nur unter Windows")
class TestDpapi(unittest.TestCase):
    def test_rundlauf_und_fremddaten(self):
        g = geheim.schuetzen("jwt-abc.def")
        self.assertTrue(g.startswith("dpapi:") and "jwt-abc" not in g)
        self.assertEqual(geheim.entschuetzen(g), "jwt-abc.def")
        self.assertEqual(geheim.schuetzen(g), g)
        self.assertEqual(geheim.entschuetzen("dpapi:AAAA"), "")
        self.assertEqual(geheim.schuetzen(""), "")

    def test_cockpit_schreibt_nie_klartext_und_migriert(self):
        d = tempfile.mkdtemp()
        roh = dict(GEHEIM, vin="LDEMO", model="BYD Dolphin Surf / Seagull (Active)")
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
            json.dump(roh, f)                                               # alte Version: Klartext
        os.environ["EVCOCKPIT_CFGDIR"] = d
        import evcockpit
        evcockpit = importlib.reload(evcockpit)
        cfg = evcockpit.load_cfg()
        self.assertEqual({k: cfg[k] for k in GEHEIM}, GEHEIM)               # im Speicher Klartext
        datei = open(os.path.join(d, "config.json"), encoding="utf-8").read()
        for v in GEHEIM.values():
            self.assertNotIn(v, datei)                                      # beim Laden migriert
        self.assertIn("LDEMO", datei)
        evcockpit._CFG["planer_token"] = "g:" + "cd" * 32
        evcockpit.save_cfg(evcockpit._CFG)
        self.assertNotIn("cd" * 32, open(os.path.join(d, "config.json"), encoding="utf-8").read())
        self.assertEqual(evcockpit.load_cfg()["planer_token"], "g:" + "cd" * 32)


class TestFelder(unittest.TestCase):
    def test_alle_geheimen_felder(self):
        for f in ("password", "control_pin", "panoptes_jwt", "panoptes_code", "planer_token", "ha_src_token",
                  "ha_pass", "pv_token", "charger_token"):
            self.assertIn(f, geheim.FELDER)


if __name__ == "__main__":
    unittest.main()
