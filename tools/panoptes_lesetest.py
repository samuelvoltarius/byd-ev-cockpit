"""Stufe 3: Kopplungstest gegen Panoptes im Auto. Sendet KEINE Befehle (weder ans Auto noch an die Cloud).

Aufruf:  python tools/panoptes_lesetest.py <datei> [--put KEY=WERT]
<datei>: zwei Zeilen - Adresse (z. B. http://100.x.y.z:8180) und Kopplungs-Code aus "Geraet koppeln"
(einmal verwendbar, 10 min gueltig). Wird nur gelesen.
--put: (nur mit Freigabe der Koordination) GENAU EIN harmloser Einstellungswert wird gesetzt, sofort
zurueckgesetzt und jeweils zurueckgelesen. Waechter, Abschreckung, Zugang/Fernzugang, adb, Ports und die
Planer-Kennung sind hier fest gesperrt - auch wenn das Schema sie erlauben wuerde.
Ausgabe: nur Befunde. Nie Kopplungs-Code, Token oder genaue Position (nur "vorhanden").
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import einstellungen as es             # noqa: E402
import panoptes_source as ps           # noqa: E402
from sicherheit import befehl_erlaubt  # noqa: E402

GESPERRT = re.compile(r"^(surveillance|guardStop|guardLegal|deterrent|remote|auth|adb|wireguard|tailscale|debug|"
                      r"backup|port|ports|planner|vehicle|cloud|telegram\.botToken)\b", re.I)


def _wert_aus(text):
    t = text.strip()
    if t.lower() in ("true", "false"):
        return t.lower() == "true"
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if re.fullmatch(r"-?\d+\.\d+", t):
        return float(t)
    return t


def put_test(p, key, neu):
    """Ein Wert setzen -> zuruecklesen -> alten Wert zuruecksetzen -> zuruecklesen."""
    if GESPERRT.search(key):
        return {"put": "VERWEIGERT (gesperrter Bereich: %s)" % key}
    stand = ps.einstellungen_lesen(p, "de")
    feld = {f["key"]: f for f in es.felder(stand["schema"])}.get(key)
    if not feld or not es.bearbeitbar(feld) or feld.get("typ") == "geheim" or feld.get("gefahr") or feld.get("bestaetigung"):
        return {"put": "VERWEIGERT (unbekannt, nicht bearbeitbar, geheim, gefahr oder Pflichttext)"}
    alt = es.wert(stand["werte"], key)
    erg = {"put_key": key, "alt": alt, "neu": neu}
    body, fehler = es.vorbereiten(stand["schema"], stand["werte"], {key: neu})
    if fehler or not body["werte"]:
        erg["put"] = "nicht gesendet: %s" % (fehler or "unveraendert")
        return erg
    r = ps.einstellungen_schreiben(p, body)
    erg["put_antwort"] = {k: r.get(k) for k in ("ok", "gespeichert", "fehler", "_status")}
    nach = ps.einstellungen_lesen(p, "de")
    erg["zurueckgelesen"] = es.wert(nach["werte"], key)
    body2, _ = es.vorbereiten(nach["schema"], nach["werte"], {key: alt})
    if body2["werte"]:
        r2 = ps.einstellungen_schreiben(p, body2)
        erg["zuruecksetzen"] = {k: r2.get(k) for k in ("ok", "fehler", "_status")}
    erg["am_ende"] = es.wert(ps.einstellungen_lesen(p, "de")["werte"], key)
    erg["wieder_wie_vorher"] = erg["am_ende"] == alt
    return erg


def main(pfad, put=None):
    zeilen = [z.strip() for z in open(pfad, encoding="utf-8").read().splitlines() if z.strip()]
    url, code = zeilen[0], zeilen[1]
    p = ps.Panoptes(url, code)
    erg = {}
    t0 = time.time()
    try:
        p._anmelden()
        erg["kopplung"] = "ok (Token erhalten, %s)" % ("Einmal-Code verbraucht, /auth/kopplung" if p.code_verbraucht
                                                       else "altes Panoptes, /auth/token")
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
    try:
        stand = ps.einstellungen_lesen(p, "de")
        ff = list(es.felder(stand["schema"]))
        erg["einstellungen"] = {"gruppen": len(stand["schema"].get("gruppen") or []), "felder": len(ff),
                                "nurLesendExtern": sum(1 for f in ff if f.get("nurLesendExtern")),
                                "geheim_im_klartext": sum(1 for f in ff if f.get("typ") == "geheim"
                                                          and "wert" in ((stand["werte"].get("werte") or {}).get(f["key"]) or {}))}
    except Exception as e:
        erg["einstellungen"] = "FEHLER %s" % type(e).__name__
    if put:
        k, v = put.split("=", 1)
        erg.update(put_test(p, k.strip(), _wert_aus(v)))
    erg["dauer_s"] = round(time.time() - t0, 1)
    return erg


if __name__ == "__main__":
    put = sys.argv[sys.argv.index("--put") + 1] if "--put" in sys.argv else None
    print(json.dumps(main(sys.argv[1], put), ensure_ascii=False, indent=1))
