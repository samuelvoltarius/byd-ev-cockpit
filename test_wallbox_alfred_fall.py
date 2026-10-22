"""1.17.1: Fall Alfred 23.10. (nachgebaut, keine echten Daten) - tuya_local-Ladestation in HA, daneben Fahrzeug-Entitaeten.
1.15 hatte switch.*_unearthed als Modus und das Ladelimit des Autos als Ziel vorgeschlagen. Das darf nie wieder passieren."""
import unittest

import wallbox_quellen as wq


def st(eid, state, **a):
    return {"entity_id": eid, "state": state, "attributes": a}


def haus(zustand="idle"):
    v = "unavailable" if zustand == "weg" else None
    return [
        st("sensor.ev_charger_status", v or zustand, device_class="enum", options=["sleep", "idle", "plugged_in", "charging", "waiting", "fault"], friendly_name="EV charger Status"),
        st("number.ev_charger_charge_current", v or "10", unit_of_measurement="A", device_class="current", min=6, max=32, friendly_name="EV charger Charge current"),
        st("number.ev_charger_maximum_current", v or "32", unit_of_measurement="A", device_class="current", friendly_name="EV charger Maximum current"),
        st("switch.ev_charger_unearthed", v or "off", friendly_name="EV charger Unearthed"),
        st("button.ev_charger_charge", v or "unknown", friendly_name="EV charger Charge"),
        st("button.ev_charger_stop", v or "unknown", friendly_name="EV charger Stop"),
        st("button.ev_charger_reset", v or "unknown", friendly_name="EV charger Reset"),
        st("select.ev_charger_plug_in_action", v or "Prompt", options=["Prompt", "Charge", "Idle"], friendly_name="EV charger Plug in action"),
        st("sensor.ev_charger_total_power", v or "0", unit_of_measurement="kW", device_class="power", friendly_name="EV Charger Total Power"),
        st("number.overdrive_a19399_charge_limit", "80", unit_of_measurement="%", friendly_name="Overdrive Charge limit"),
        st("binary_sensor.byd_charging", "off", device_class="battery_charging", friendly_name="BYD Charging"),
        st("sensor.surfmate_138222_charge_power", "0.0", unit_of_measurement="kW", device_class="power", friendly_name="Panoptes Vehicle Charge Power"),
        st("switch.surfmate_138222_smart_charging", "off", friendly_name="Panoptes Vehicle Smart Charging"),
    ]


class TestFallAlfred(unittest.TestCase):
    def test_vorschlag_sicher(self):
        g = wq.ha_geraete(haus())
        self.assertEqual(len(g), 1)
        z = g[0]["zuordnung"]
        self.assertEqual((z["modus"], z["start"], z["stop"], z["strom"], z["laedt"], z["ziel"]),
                         (None, "button.ev_charger_charge", "button.ev_charger_stop", "number.ev_charger_charge_current",
                          "sensor.ev_charger_status", None))
        alle = " ".join(str(v) for v in z.values())
        for verboten in ("unearthed", "maximum_current", "reset", "overdrive", "byd_", "surfmate"):
            self.assertNotIn(verboten, alle)

    def test_alte_gefaehrliche_zuordnung_wird_entschaerft(self):
        alt = {"schluessel": "wallbox", "titel": "Wallbox", "laedt": "binary_sensor.byd_charging", "leistung": "sensor.ev_charger_l1_power",
               "modus": "switch.ev_charger_unearthed", "ziel": "number.overdrive_a19399_charge_limit",
               "strom": "number.ev_charger_charge_current", "startzeit": None, "modusOptionen": {}}
        b = wq.ha_bereinigen(alt)
        self.assertEqual((b["modus"], b["ziel"], b["laedt"], b["strom"]), (None, None, None, "number.ev_charger_charge_current"))
        self.assertEqual(sorted(b["entfernt"]), ["binary_sensor.byd_charging", "number.overdrive_a19399_charge_limit", "switch.ev_charger_unearthed"])

    def test_knoepfe_starten_und_stoppen(self):
        zust = {"s": "idle"}
        druecke = []

        def http(m, url, tok, daten=None, timeout=4.0):
            pfad = url.split(":8123", 1)[1]
            if m == "POST":
                druecke.append((pfad, daten))
                zust["s"] = "charging" if daten["entity_id"].endswith("_charge") else "idle"
                return []
            eid = pfad[len("/api/states/"):]
            return next(x for x in haus(zust["s"]) if x["entity_id"] == eid)
        z = wq.ha_geraete(haus())[0]["zuordnung"]
        q = wq.HaQuelle("http://192.168.0.30:8123", "t", [z], http=http, schlaf=lambda s: None)
        lp = q.ladepunkte()[0]
        self.assertEqual((lp["faehigkeiten"]["modus"], lp["modus"], lp["erreichbar"]), (["aus", "sofort"], "aus", True))
        self.assertTrue(q.steuern("ha:wallbox", "modus", "sofort")["uebernommen"])
        self.assertTrue(q.steuern("ha:wallbox", "modus", "aus")["uebernommen"])
        self.assertEqual([d[1]["entity_id"] for d in druecke], ["button.ev_charger_charge", "button.ev_charger_stop"])

    def test_nicht_erreichbar_wird_nicht_gesteuert(self):
        z = wq.ha_geraete(haus())[0]["zuordnung"]
        lp = wq.ha_ladepunkt(z, {r: next(x for x in haus("weg") if x["entity_id"] == e) for r, e in z.items()
                                 if isinstance(e, str) and "." in e})
        self.assertFalse(lp["erreichbar"])
        with self.assertRaises(wq.WallboxFehler) as f:
            wq.pruefe_wert(lp, "strom", 10)
        self.assertEqual(f.exception.code, "ha_nicht_erreichbar")


if __name__ == "__main__":
    unittest.main()
