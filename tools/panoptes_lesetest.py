"""Stufe 3: rein lesender Kopplungstest gegen Panoptes im Auto. Sendet KEINE Befehle (weder ans Auto noch an die Cloud).

Aufruf:  python tools/panoptes_lesetest.py <datei>
<datei>: zwei Zeilen - Adresse (z. B. http://100.x.y.z:8180) und Kopplungs-Code. Wird nur gelesen.
Ausgabe: nur Befunde. Nie Kopplungs-Code, Token oder genaue Position (nur "vorhanden").
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import panoptes_source as ps          # noqa: E402
from sicherheit import befehl_erlaubt  # noqa: E402


def main(pfad):
    zeilen = [z.strip() for z in open(pfad, encoding="utf-8").read().splitlines() if z.strip()]
    url, code = zeilen[0], zeilen[1]
    p = ps.Panoptes(url, code)
    erg = {}
    t0 = time.time()
    try:
        p._anmelden()
        erg["kopplung"] = "ok (Token erhalten)"
    except Exception as e:
        erg["kopplung"] = "FEHLER %s" % type(e).__name__
        return erg
    for name, pfad_api in (("telemetry", "/api/mqtt/telemetry"), ("summary", "/api/launcher/v1/summary"),
                           ("gps", "/api/gps")):
        try:
            d = p._get(pfad_api)
            erg[name] = "ok (%d Felder)" % len(d.get("telemetry", d) if isinstance(d, dict) else 0)
        except Exception as e:
            erg[name] = "FEHLER %s" % type(e).__name__
    st = p.lies() or {}
    erg["cockpit_felder"] = {k: st.get(k) for k in ("soc", "range_km", "odometer", "gear", "charging", "power_level", "speed")}
    erg["position_vorhanden"] = bool(st.get("latitude") and st.get("longitude"))
    z = {"t": time.time(), "power_level": st.get("power_level"), "gear": st.get("gear"), "speed": st.get("speed")}
    ok, grund = befehl_erlaubt(z, time.time())
    erg["sperre"] = "Befehl WÄRE erlaubt (Auto aus erkannt)" if ok else "Befehl wäre gesperrt: " + grund
    erg["identitaet"] = ps.identitaet(p) or "(noch nicht verfügbar)"
    erg["dauer_s"] = round(time.time() - t0, 1)
    return erg


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), ensure_ascii=False, indent=1))
