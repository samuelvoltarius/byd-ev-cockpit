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
