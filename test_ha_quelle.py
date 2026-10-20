"""Tests Home Assistant als Datenquelle (kein Netz)."""
import unittest

import ha_quelle as hq


def e(eid, state, **attr):
    return {"entity_id": eid, "state": state, "attributes": attr}


STATES = [
    # Panoptes ueber MQTT-Discovery (Geraet "SurfMate (Dolphin Surf)")
    e("sensor.surfmate_dolphin_surf_state_of_charge", "64.5", unit_of_measurement="%", device_class="battery",
      friendly_name="SurfMate (Dolphin Surf) State of Charge"),
    e("sensor.surfmate_dolphin_surf_ev_range", "251", unit_of_measurement="km", friendly_name="SurfMate (Dolphin Surf) EV Range"),
    e("sensor.surfmate_dolphin_surf_odometer", "18342", unit_of_measurement="km", device_class="distance",
      friendly_name="SurfMate (Dolphin Surf) Odometer"),
    e("binary_sensor.surfmate_dolphin_surf_is_charging", "off", device_class="battery_charging",
      friendly_name="SurfMate (Dolphin Surf) Charging"),
    e("device_tracker.surfmate_dolphin_surf_location", "home", latitude=47.8, longitude=13.04,
      friendly_name="SurfMate (Dolphin Surf) Location"),
    # Stoerer, die nie gewaehlt werden duerfen
    e("sensor.pixel_8_battery_level", "88", unit_of_measurement="%", device_class="battery", friendly_name="Pixel 8 Battery"),
    e("sensor.wohnzimmer_luftfeuchte", "45", unit_of_measurement="%", device_class="humidity"),
    e("device_tracker.alfreds_iphone", "home", latitude=47.8, longitude=13.04, friendly_name="iPhone"),
    e("sensor.tankstelle_range", "5", unit_of_measurement="km"),
]


class TestVorschlag(unittest.TestCase):
    def test_panoptes_geraet_wird_erkannt(self):
        v = hq.vorschlag(STATES)
        self.assertEqual(v["soc"]["wahl"], "sensor.surfmate_dolphin_surf_state_of_charge")
        self.assertEqual(v["range_km"]["wahl"], "sensor.surfmate_dolphin_surf_ev_range")
        self.assertEqual(v["odometer"]["wahl"], "sensor.surfmate_dolphin_surf_odometer")
        self.assertEqual(v["charging"]["wahl"], "binary_sensor.surfmate_dolphin_surf_is_charging")
        self.assertEqual(v["location"]["wahl"], "device_tracker.surfmate_dolphin_surf_location")

    def test_handy_und_fremdes_nie(self):
        v = hq.vorschlag(STATES)
        alle = {k["id"] for f in v.values() for k in f["kandidaten"]}
        self.assertNotIn("sensor.pixel_8_battery_level", alle)
        self.assertNotIn("device_tracker.alfreds_iphone", alle)
        self.assertNotIn("sensor.wohnzimmer_luftfeuchte", alle)

    def test_ohne_autobezug_keine_vorauswahl(self):
        v = hq.vorschlag([e("sensor.akku_ladestand", "50", unit_of_measurement="%")])
        self.assertEqual(v["soc"]["wahl"], "")
        self.assertEqual(v["soc"]["kandidaten"][0]["id"], "sensor.akku_ladestand")   # aber waehlbar

    def test_auto_unterstrich_name(self):
        v = hq.vorschlag([e("sensor.auto_ladestand", "50", unit_of_measurement="%")])
        self.assertEqual(v["soc"]["wahl"], "sensor.auto_ladestand")


class TestWerte(unittest.TestCase):
    def test_lesen(self):
        z = {f: hq.vorschlag(STATES)[f]["wahl"] for f in hq.FELDER}
        st = hq.aus_states(STATES, z)
        self.assertEqual(st, {"soc": 64.5, "range_km": 251.0, "odometer": 18342.0, "charging": "OFF",
                              "latitude": 47.8, "longitude": 13.04})

    def test_unbekannt_wird_nicht_erfunden(self):
        st = hq.aus_states([e("sensor.byd_soc", "unavailable", unit_of_measurement="%")], {"soc": "sensor.byd_soc"})
        self.assertEqual(st, {})
        self.assertEqual(hq.aus_states(STATES, {}), {})

    def test_meilen(self):
        st = hq.aus_states([e("sensor.byd_range", "100", unit_of_measurement="mi")], {"range_km": "sensor.byd_range"})
        self.assertEqual(st["range_km"], 160.9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
