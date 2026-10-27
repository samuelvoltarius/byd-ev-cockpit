"""Sperre fuer Fernbefehle ueber die BYD-Cloud: nur bei sicher AUSGESCHALTETEM Auto.

Hintergrund (Vorfall 13.10.2026): "Klima aus" ueber die BYD-Cloud hat ein eingeschaltetes Auto mit
Fahrer darin komplett abgeschaltet (stand in P und lud). Die Cloud beendet dabei die ganze
Fernsitzung. Deshalb gilt fuer JEDEN Cloud-Befehl (Klima, Batterieheizung, Sitze, Zusperren, Hupe):

  - Der Zustand muss frisch sein (direkt vor dem Befehl abgefragt).
  - Gang D/R/N oder Geschwindigkeit > 0  -> gesperrt.
  - Panoptes im Auto meldet power_level: nur 0 (aus) ist erlaubt (2 = an, am Dolphin Surf gemessen).
  - Sonst BYD-Cloud vehicle_state: nur 0 (aus) ist erlaubt.
  - Unbekannt -> gesperrt. Lieber ein Befehl zu wenig als ein Auto aus, in dem jemand sitzt.
"""

FRISCH_S = 180

# Gleiche Regeln wie Alfreds Bridge (befehl_gate.py, 21.10.2026): nur bei LIVE bestaetigtem "aus", hoechstens
# 180 s alt, gilt fuer ALLE Befehle (auch Batterie, Hupe/Licht), Aufsperren NIE. Der power_level von Panoptes kommt
# per HTTP direkt aus dem Fahrzeug-SDK (collectTelemetry, ~2 s Cache), nicht aus einem gespeicherten MQTT-Wert.
ERLAUBTE_BEFEHLE = ("heat", "cool", "off", "batt_on", "batt_off", "lock",
                    "seat_off", "seat_lo", "seat_hi", "vent_off", "vent_lo", "vent_hi")
NIE = ("unlock", "find")      # Aufsperren nie; Hupe/Licht nie (Regel A+, Koordination 27.10.): "find" gibt es im Cockpit nicht
assert not set(ERLAUBTE_BEFEHLE) & set(NIE)

GRUND_AN = "das Auto ist eingeschaltet"
GRUND_FAEHRT = "das Auto fährt oder ist nicht in P"
GRUND_UNBEKANNT = "ob das Auto aus ist, lässt sich gerade nicht sicher feststellen"
GRUND_ALT = "der Fahrzeugzustand ist nicht aktuell"


def _zahl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def befehl_erlaubt(z, jetzt):
    """z: {"t": Zeitstempel der Abfrage, "power_level", "vehicle_state", "gear", "speed"}.
    Liefert (True, "") oder (False, Grund in Alltagssprache)."""
    if not z or _zahl(z.get("t")) is None or jetzt - float(z["t"]) > FRISCH_S:
        return False, GRUND_ALT
    gang = str(z.get("gear") or "").upper()[:1]
    if gang in ("D", "R", "N") or (_zahl(z.get("speed")) or 0) > 0:
        return False, GRUND_FAEHRT
    pl = _zahl(z.get("power_level"))
    if pl is not None:
        return (True, "") if pl == 0 else (False, GRUND_AN)
    vs = _zahl(z.get("vehicle_state"))
    if vs is not None and vs >= 0:
        return (True, "") if vs == 0 else (False, GRUND_AN)
    return False, GRUND_UNBEKANNT


def aus_letzter_abfrage(state, jetzt):
    """Stiller Beweis aus der letzten REGULAEREN Cloud-Abfrage (kein Zusatzauftrag ans Auto):
    nur wenn sie von der BYD-Cloud kam, einen gueltigen vehicle_state hat und frisch ist. Sonst None."""
    vs, t = state.get("vehicle_state"), _zahl(state.get("_zustand_t"))
    if state.get("quelle") != "BYD-Cloud" or not isinstance(vs, int) or vs < 0 or t is None or jetzt - t > FRISCH_S:
        return None
    return {"t": t, "vehicle_state": vs, "gear": state.get("gear"), "speed": state.get("speed")}
