"""1.18.2: Wallbox-Bruecke (HA-Entitaeten wallbox_*): automatische Zuordnung, nie der Freigabe-Schalter, Ladestrom als select."""
import unittest

import wallbox_quellen as wq


def st(eid, state, **a):
    return {"entity_id": eid, "state": state, "attributes": a}


BRUECKE = [
    st("sensor.wallbox_status", "sleep", device_class="enum", options=["sleep", "idle", "plugged_in", "charging", "waiting", "fault", "paused", "charged"], friendly_name="Wallbox Status"),
    st("sensor.wallbox_leistung", "0.0", unit_of_measurement="kW", device_class="power", friendly_name="Wallbox Leistung"),
    st("sensor.wallbox_energie_sitzung", "0.0", unit_of_measurement="kWh", device_class="energy", friendly_name="Wallbox Energie Ladevorgang"),
    st("sensor.wallbox_ladestrom_soll", "6", unit_of_measurement="A", device_class="current", friendly_name="Wallbox Ladestrom eingestellt"),
    st("sensor.wallbox_strom_l1", "0.0", unit_of_measurement="A", device_class="current", friendly_name="Wallbox Strom L1"),
    st("binary_sensor.wallbox_laedt", "off", device_class="battery_charging", friendly_name="Wallbox Lädt"),
    st("binary_sensor.wallbox_angesteckt", "off", device_class="plug", friendly_name="Wallbox Auto angesteckt"),
    st("binary_sensor.wallbox_fehler", "off", device_class="problem", friendly_name="Wallbox Fehler"),
    st("binary_sensor.wallbox_erdung_aus", "off", device_class="problem", friendly_name="Wallbox Erdungsprüfung aus"),
    st("switch.wallbox_steuern_erlaubt", "off", friendly_name="Wallbox Steuern erlaubt"),
    st("button.wallbox_laden_starten", "unknown", friendly_name="Wallbox Laden starten"),
    st("button.wallbox_laden_stoppen", "unknown", friendly_name="Wallbox Laden stoppen"),
    st("select.wallbox_ladestrom", "6", options=["6", "8", "10", "13", "16"], friendly_name="Wallbox Ladestrom wählen"),
]


class Bruecke(unittest.TestCase):
    def setUp(self):
        g = wq.ha_geraete(BRUECKE)
        self.assertEqual(len(g), 1)
        self.z = g[0]["zuordnung"]

    def test_zuordnung(self):
        z = self.z
        self.assertEqual(z["titel"], "Wallbox")
        self.assertEqual((z["laedt"], z["leistung"], z["start"], z["stop"], z["strom"]),
                         ("sensor.wallbox_status", "sensor.wallbox_leistung", "button.wallbox_laden_starten",
                          "button.wallbox_laden_stoppen", "select.wallbox_ladestrom"))

    def test_freigabe_schalter_nie_steuerung(self):
        self.assertIsNone(self.z["modus"])
        self.assertEqual(self.z["freigabe"], "switch.wallbox_steuern_erlaubt")      # nur als Sperre-Anzeige, nie als Modus

    def test_melder_sind_nicht_laedt(self):
        for eid in ("binary_sensor.wallbox_fehler", "binary_sensor.wallbox_erdung_aus", "binary_sensor.wallbox_angesteckt"):
            self.assertNotEqual(self.z["laedt"], eid)

    def test_lesen_und_faehigkeiten(self):
        e = {r: dict(next(s for s in BRUECKE if s["entity_id"] == self.z[r])) for r in wq.DOMAENEN if self.z.get(r)}
        lp = wq.ha_ladepunkt(self.z, e)
        self.assertIs(lp["laedt"], False)
        self.assertEqual((lp["leistungW"], lp["stromA"]), (0, 6))
        self.assertEqual(lp["faehigkeiten"]["strom"], {"min": 6, "max": 16, "stufen": [6, 8, 10, 13, 16]})

    def test_nur_stufen(self):
        lp = {"art": "wallbox", "faehigkeiten": {"strom": {"min": 6, "max": 16, "stufen": [6, 8, 10, 13, 16]}}}
        self.assertEqual(wq.pruefe_wert(lp, "strom", 13), 13)
        for v in (7, 11, 17, 5):
            with self.assertRaises(wq.WallboxFehler):
                wq.pruefe_wert(lp, "strom", v)

    def test_schreiben_per_select_option(self):
        aufrufe = []

        def http(m, url, tok, daten=None, timeout=4.0):
            if m == "POST":
                aufrufe.append((url.rsplit("/api/services/", 1)[1], daten))
                return []
            eid = url.rsplit("/", 1)[1]
            s = next(x for x in BRUECKE if x["entity_id"] == eid)
            if eid == "switch.wallbox_steuern_erlaubt":
                return dict(s, state="on")
            return dict(s, state="10" if eid in ("select.wallbox_ladestrom", "sensor.wallbox_ladestrom_soll") and aufrufe else s["state"])
        q = wq.HaQuelle("http://192.168.1.10", "t", [self.z], http=http, schlaf=lambda s: None)
        r = q.steuern("ha:wallbox", "strom", 10)
        self.assertEqual(aufrufe, [("select/select_option", {"entity_id": "select.wallbox_ladestrom", "option": "10"})])
        self.assertTrue(r["uebernommen"])
        with self.assertRaises(wq.WallboxFehler):
            q.steuern("ha:wallbox", "strom", 11)
        self.assertEqual(len(aufrufe), 1)


if __name__ == "__main__":
    unittest.main()


class Sperre(unittest.TestCase):
    def test_gesperrt_und_echo(self):
        z = wq.ha_geraete(BRUECKE + [st("sensor.wallbox_ladestrom_soll", "6", unit_of_measurement="A", device_class="current", friendly_name="Wallbox Ladestrom eingestellt")])[0]["zuordnung"]
        self.assertEqual((z["freigabe"], z["echo"]), ("switch.wallbox_steuern_erlaubt", "sensor.wallbox_ladestrom_soll"))
        self.assertIsNone(z["modus"])
        aufrufe = []

        def http(m, url, tok, daten=None, timeout=4.0):
            if m == "POST":
                aufrufe.append(url)
                return []
            eid = url.rsplit("/", 1)[1]
            return dict(next(s for s in BRUECKE + [st("sensor.wallbox_ladestrom_soll", "6", unit_of_measurement="A", device_class="current")] if s["entity_id"] == eid))
        q = wq.HaQuelle("http://192.168.1.10", "t", [z], http=http, schlaf=lambda s: None)
        lp = q.ladepunkte()[0]
        self.assertTrue(lp["faehigkeiten"]["gesperrt"])
        with self.assertRaises(wq.WallboxFehler) as f:
            wq.pruefe_wert(lp, "strom", 10)
        self.assertEqual(f.exception.code, "bruecke_gesperrt")
        with self.assertRaises(wq.WallboxFehler):
            q.steuern("ha:wallbox", "strom", 10)
        self.assertEqual(aufrufe, [])               # nichts gesendet

    def test_wartet_bis_echo(self):
        aufrufe, zaehler = [], [0]
        z = wq.ha_geraete(BRUECKE + [st("sensor.wallbox_ladestrom_soll", "6", unit_of_measurement="A", device_class="current", friendly_name="Wallbox Ladestrom eingestellt")])[0]["zuordnung"]

        def http(m, url, tok, daten=None, timeout=4.0):
            if m == "POST":
                aufrufe.append(url)
                return []
            eid = url.rsplit("/", 1)[1]
            if eid == "switch.wallbox_steuern_erlaubt":
                return st(eid, "on")
            if eid == "sensor.wallbox_ladestrom_soll":
                zaehler[0] += 1
                return st(eid, "10" if zaehler[0] > 12 else "6", unit_of_measurement="A")
            return dict(next(s for s in BRUECKE if s["entity_id"] == eid))
        q = wq.HaQuelle("http://192.168.1.10", "t", [z], http=http, schlaf=lambda s: None)
        r = q.steuern("ha:wallbox", "strom", 10)
        self.assertTrue(r["uebernommen"])          # erst nach ~12 Rueckleseversuchen (~12 s) sichtbar -> nicht zu frueh "anderer Wert"
        self.assertEqual(len(aufrufe), 1)
