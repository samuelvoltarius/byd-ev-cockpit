"""Tests Panoptes-Einstellungen aus dem Schema (Vertrag EINSTELLUNGEN_SCHEMA.md v1, kein Netz)."""
import unittest

import einstellungen as es

SCHEMA = {"version": 1, "etag": "s-1", "gruppen": [
    {"id": "waechter", "titel": "Wächter", "felder": [
        {"key": "surveillance.triggerMode", "typ": "auswahl", "titel": "Auslöser", "standard": None,
         "bestaetigung": "guardLegal.trigger", "nurLesendExtern": False, "neustartNoetig": False,
         "optionen": [{"wert": "shock"}, {"wert": "ai_everywhere", "gesperrt": True, "gesperrtGrund": "CH"},
                      {"wert": "ai_private"}]},
        {"key": "surveillance.privateZones", "typ": "geozone", "nurWenn": {"key": "surveillance.triggerMode", "gleich": "ai_private"},
         "nurLesendExtern": False},
        {"key": "guardStop.socBelow", "typ": "int", "min": 0, "max": 80, "nurLesendExtern": False},
        {"key": "deterrent.light", "typ": "bool", "gefahr": True, "nurLesendExtern": False},
        {"key": "cluster.x", "typ": "bool", "nurWenn": {"faehigkeit": "cluster"}, "nurLesendExtern": False},
    ]},
    {"id": "system", "titel": "System", "felder": [
        {"key": "remote.tailscale.enabled", "typ": "bool", "nurLesendExtern": True},
        {"key": "telegram.botToken", "typ": "geheim", "nurLesendExtern": False},
        {"key": "planner.autoId", "typ": "text", "nurLesendExtern": True},
    ]}]}
WERTE = {"etag": "w-1", "werte": {"surveillance.triggerMode": {"wert": "shock", "gesetzt": True},
                                  "guardStop.socBelow": {"wert": 20, "gesetzt": False},
                                  "deterrent.light": {"wert": False}, "telegram.botToken": {"gesetzt": True}}}


class TestSichtbar(unittest.TestCase):
    def test_nurwenn(self):
        f = {x["key"]: x for x in es.felder(SCHEMA)}
        self.assertFalse(es.sichtbar(f["surveillance.privateZones"], WERTE))
        w2 = {"werte": {"surveillance.triggerMode": {"wert": "ai_private"}}}
        self.assertTrue(es.sichtbar(f["surveillance.privateZones"], w2))
        self.assertFalse(es.sichtbar(f["cluster.x"], WERTE, {}))
        self.assertTrue(es.sichtbar(f["cluster.x"], WERTE, {"cluster": True}))
        self.assertFalse(es.bearbeitbar(f["remote.tailscale.enabled"]))     # Regel B
        self.assertFalse(es.bearbeitbar(f["surveillance.privateZones"]))    # geozone: erst nur anzeigen


class TestVorbereiten(unittest.TestCase):
    def test_nur_geaendertes_und_erlaubtes(self):
        body, fehler = es.vorbereiten(SCHEMA, WERTE, {"guardStop.socBelow": 25, "deterrent.light": False,
                                                      "remote.tailscale.enabled": False, "planner.autoId": "x",
                                                      "gibtsnicht": 1})
        self.assertEqual(body, {"etag": "w-1", "werte": {"guardStop.socBelow": 25}})
        self.assertEqual(fehler, {"remote.tailscale.enabled": "nurLesendExtern", "planner.autoId": "nurLesendExtern",
                                  "gibtsnicht": "unbekannt"})

    def test_grenzen_und_typen(self):
        _, f = es.vorbereiten(SCHEMA, WERTE, {"guardStop.socBelow": 81})
        self.assertEqual(f, {"guardStop.socBelow": "max 80"})
        _, f = es.vorbereiten(SCHEMA, WERTE, {"guardStop.socBelow": 2.5})
        self.assertEqual(f, {"guardStop.socBelow": "typ"})
        _, f = es.vorbereiten(SCHEMA, WERTE, {"deterrent.light": "ja"})
        self.assertEqual(f, {"deterrent.light": "typ"})

    def test_bestaetigung_und_gesperrte_option(self):
        _, f = es.vorbereiten(SCHEMA, WERTE, {"surveillance.triggerMode": "ai_private"})
        self.assertEqual(f, {"surveillance.triggerMode": "bestaetigungFehlt"})
        body, f = es.vorbereiten(SCHEMA, WERTE, {"surveillance.triggerMode": "ai_private"}, bestaetigt=["surveillance.triggerMode"])
        self.assertEqual((body["werte"], body["bestaetigt"], f), ({"surveillance.triggerMode": "ai_private"},
                                                                  ["surveillance.triggerMode"], {}))
        _, f = es.vorbereiten(SCHEMA, WERTE, {"surveillance.triggerMode": "ai_everywhere"}, bestaetigt=["surveillance.triggerMode"])
        self.assertEqual(f, {"surveillance.triggerMode": "option"})     # in CH gesperrt

    def test_geheim(self):
        body, _ = es.vorbereiten(SCHEMA, WERTE, {"telegram.botToken": "neu-123"})
        self.assertEqual(body["werte"], {"telegram.botToken": "neu-123"})
        body, _ = es.vorbereiten(SCHEMA, WERTE, {"telegram.botToken": None})         # null loescht
        self.assertEqual(body["werte"], {"telegram.botToken": None})


if __name__ == "__main__":
    unittest.main(verbosity=2)
