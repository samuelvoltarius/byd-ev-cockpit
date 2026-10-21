"""Wallbox steuern im Cockpit nach WALLBOX_VERTRAG §5: Freigabe je Ladepunkt, Bestaetigung serverseitig,
Schreib-Protokoll. Die Wirkung selbst macht evcc_backend.set_loadpoint (immer mit Zuruecklesen)."""
import json
import secrets
import time

GUELTIG_S = 30
PROTOKOLL_MAX = 200
_OFFEN = {}          # kennung -> (ablauf, schluessel); nur im Speicher


def schluessel(lp, titel, aktion, wert):
    """Genau diese Aktion + Wert + Ladepunkt (§5.2.3)."""
    return json.dumps([int(lp), str(titel or "")[:60], str(aktion), wert], sort_keys=True)


def frage(sch, uhr=time.time):
    """Neue Einmal-Kennung (128 bit, 30 s) fuer genau diese Aktion."""
    jetzt = uhr()
    for k in [k for k, (ab, _) in _OFFEN.items() if ab < jetzt]:
        _OFFEN.pop(k, None)
    k = secrets.token_hex(16)
    _OFFEN[k] = (jetzt + GUELTIG_S, sch)
    return k


def einloesen(kennung, sch, uhr=time.time):
    """True nur fuer eine gueltige, unbenutzte Kennung zu genau dieser Aktion. Gilt einmal."""
    if not isinstance(kennung, str) or kennung not in _OFFEN:
        return False
    ab, s = _OFFEN.pop(kennung)
    return ab >= uhr() and s == sch


def frage_text(titel, aktion, wert):
    t = str(titel or "Ladepunkt")[:60]
    if aktion == "freigeben":
        return t + ": Steuern erlauben? Das Cockpit darf dann über evcc den Lademodus und den Ziel-Ladestand ändern. Mehr nicht."
    if aktion == "modus":
        n = {"off": "Aus", "now": "Sofort", "minpv": "Min+PV", "pv": "PV"}.get(wert, str(wert))
        return t + ": Lademodus auf „" + n + "“ stellen?"
    return t + ": Ziel-Ladestand auf " + str(wert) + " % stellen?"


def ziel_kennung(host, port):
    """Woran die Freigaben haengen: Host und Port, wie eingegeben (Wechsel loescht alle Freigaben, §2)."""
    return "%s:%s" % (str(host or "").strip().lower(), int(port or 7070))


def protokoll(pfad, quelle, ladepunkt, aktion, wert, ergebnis, uhr=time.time):
    """Eine Zeile je Steuer- und Freigabe-Aktion, ohne URL, Token, Position (§5.4). Die letzten 200 bleiben."""
    z = {"zeit": int(uhr() * 1000), "quelle": quelle, "ladepunkt": str(ladepunkt)[:80], "aktion": aktion,
         "wert": wert, "ergebnis": str(ergebnis)[:60], "herkunft": "cockpit"}
    try:
        alt = pfad.read_text("utf-8").splitlines() if pfad.exists() else []
    except Exception:
        alt = []
    alt = (alt + [json.dumps(z, ensure_ascii=False)])[-PROTOKOLL_MAX:]
    tmp = pfad.with_name(pfad.name + ".neu")
    tmp.write_text("\n".join(alt) + "\n", "utf-8")
    tmp.replace(pfad)


def protokoll_lesen(pfad, n=50):
    try:
        zeilen = pfad.read_text("utf-8").splitlines()
    except Exception:
        return []
    aus = []
    for z in reversed(zeilen[-n:]):
        try:
            aus.append(json.loads(z))
        except Exception:
            pass
    return aus
