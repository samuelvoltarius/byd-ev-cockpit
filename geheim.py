"""Geheimnisse des Cockpits im Schluesselbund des Betriebssystems (Regel S: nie Klartext auf der Platte, wo es geht).

- Windows: DPAPI (CurrentUser) ueber ctypes. In config.json steht "dpapi:<base64>"; nur derselbe Windows-Benutzer auf
  demselben Rechner kann entschluesseln.
- macOS: Schluesselbund ueber das eingebaute Werkzeug `security`. Das Geheimnis geht per stdin hinein (`security -i`),
  nie ueber die Kommandozeile (die sehen andere Prozesse). In config.json steht nur "keychain:<feld>".
- Linux: Secret Service (GNOME Schluesselbund, KWallet) ueber `secret-tool`, liest das Geheimnis von stdin.
  In config.json steht nur "keychain:<feld>".
- Rueckfall (kein Schluesselbund, z. B. Raspberry ohne Desktop): wie bisher in config.json mit Dateirechten 0600,
  dazu ein Warnhinweis im Cockpit (WARNUNG).
Uebernahme nur mit Zuruecklesen: erst wenn der Schluesselbund den Wert nachweislich zurueckgibt, verschwindet er aus
der Datei. Nur Standardbibliothek, kein Fremdpaket.
"""
import base64
import shutil
import subprocess
import sys

# Felder, die nie im Klartext auf die Platte sollen
FELDER = ("password", "control_pin", "panoptes_jwt", "panoptes_code", "planer_token",
          "ha_src_token", "ha_pass", "pv_token", "charger_token")
PREFIX = "dpapi:"
KC = "keychain:"
DIENST = "EV-Cockpit"
WARNUNG_TEXT = ("Deine Passwörter und Schlüssel liegen unverschlüsselt in der Einstellungsdatei (nur für deinen "
                "Benutzer lesbar), weil hier kein Schlüsselbund verfügbar ist. Unter Linux hilft das Paket "
                "„libsecret-tools“ (secret-tool) mit einem laufenden Schlüsselbund.")
WARNUNG = ""                 # gesetzt, solange ein Geheimnis nur im Rueckfall (Klartext 0600) liegt
_GESPEICHERT = {}            # (profil, feld) -> Wert, der zuletzt nachweislich im Schluesselbund lag


def verfuegbar():
    return sys.platform == "win32"


def backend():
    """"dpapi" | "keychain" (macOS) | "secretservice" (Linux) | "" (Rueckfall)."""
    if sys.platform == "win32":
        return "dpapi"
    if sys.platform == "darwin" and shutil.which("security"):
        return "keychain"
    if sys.platform.startswith("linux") and shutil.which("secret-tool"):
        return "secretservice"
    return ""


# ---------------------------------------------------------------- Windows: DPAPI
def _dpapi(daten, schuetzen_):
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
    puffer = ctypes.create_string_buffer(daten, len(daten))
    ein = DATA_BLOB(len(daten), ctypes.cast(puffer, ctypes.POINTER(ctypes.c_char)))
    aus = DATA_BLOB()
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    f = crypt32.CryptProtectData if schuetzen_ else crypt32.CryptUnprotectData
    # CRYPTPROTECT_UI_FORBIDDEN = 0x1: nie einen Dialog zeigen
    if not f(ctypes.byref(ein), None, None, None, None, 0x1, ctypes.byref(aus)):
        raise OSError("DPAPI fehlgeschlagen (%d)" % ctypes.GetLastError())
    try:
        return ctypes.string_at(aus.pbData, aus.cbData)
    finally:
        kernel32.LocalFree(aus.pbData)


def schuetzen(wert):
    """Klartext -> "dpapi:<base64>" (Windows) bzw. unveraendert (sonst, oder wenn leer/schon geschuetzt)."""
    if not isinstance(wert, str) or not wert or wert.startswith(PREFIX) or not verfuegbar():
        return wert
    return PREFIX + base64.b64encode(_dpapi(wert.encode("utf-8"), True)).decode("ascii")


def entschuetzen(wert):
    """"dpapi:<base64>" -> Klartext. Nicht entschluesselbar (anderer Benutzer/Rechner) -> "" (dann neu einrichten)."""
    if not isinstance(wert, str) or not wert.startswith(PREFIX):
        return wert
    if not verfuegbar():
        return ""
    try:
        return _dpapi(base64.b64decode(wert[len(PREFIX):]), False).decode("utf-8")
    except Exception:
        return ""


# ---------------------------------------------------------------- macOS / Linux: Schluesselbund
def _lauf(cmd, eingabe=None):
    try:
        r = subprocess.run(cmd, input=eingabe, capture_output=True, text=True, timeout=20)
        return r.returncode, r.stdout
    except Exception:
        return 1, ""


def _kc_setzen(profil, feld, wert):
    konto = "%s:%s" % (profil, feld)
    if backend() == "keychain":
        esc = lambda x: x.replace("\\", "\\\\").replace('"', '\\"')
        befehl = 'add-generic-password -U -a "%s" -s "%s" -w "%s"\n' % (esc(konto), DIENST, esc(wert))
        return _lauf(["security", "-i"], befehl)[0] == 0           # Geheimnis nur ueber stdin
    if backend() == "secretservice":
        return _lauf(["secret-tool", "store", "--label", "%s %s" % (DIENST, feld),
                      "anwendung", "ev-cockpit", "profil", profil, "feld", feld], wert)[0] == 0
    return False


def _kc_lesen(profil, feld):
    konto = "%s:%s" % (profil, feld)
    if backend() == "keychain":
        rc, aus = _lauf(["security", "find-generic-password", "-a", konto, "-s", DIENST, "-w"])
        return aus.rstrip("\n") if rc == 0 else None
    if backend() == "secretservice":
        rc, aus = _lauf(["secret-tool", "lookup", "anwendung", "ev-cockpit", "profil", profil, "feld", feld])
        return aus.rstrip("\n") if rc == 0 else None
    return None


def _kc_loeschen(profil, feld):
    konto = "%s:%s" % (profil, feld)
    if backend() == "keychain":
        _lauf(["security", "delete-generic-password", "-a", konto, "-s", DIENST])
    elif backend() == "secretservice":
        _lauf(["secret-tool", "clear", "anwendung", "ev-cockpit", "profil", profil, "feld", feld])
    _GESPEICHERT.pop((profil, feld), None)


# ---------------------------------------------------------------- Konfiguration
def fuer_platte(cfg, profil=""):
    """Kopie der Konfiguration fuer die Datei: Geheimnisse verschluesselt bzw. im Schluesselbund (mit Zuruecklesen).
    Das Original im Speicher bleibt Klartext. Setzt WARNUNG, wenn etwas im Rueckfall bleibt."""
    global WARNUNG
    aus, rueckfall = dict(cfg), False
    b = backend()
    for k in FELDER:
        v = cfg.get(k)
        if not isinstance(v, str) or not v:
            if b in ("keychain", "secretservice") and (profil, k) in _GESPEICHERT:
                _kc_loeschen(profil, k)                         # Wert entfernt -> auch im Schluesselbund weg
            continue
        if b == "dpapi":
            aus[k] = schuetzen(v)
        elif b in ("keychain", "secretservice"):
            if _GESPEICHERT.get((profil, k)) == v or (_kc_setzen(profil, k, v) and _kc_lesen(profil, k) == v):
                _GESPEICHERT[(profil, k)] = v
                aus[k] = KC + k
            else:
                rueckfall = True                                # Zuruecklesen gescheitert: Wert bleibt in der Datei
        else:
            rueckfall = True
    WARNUNG = WARNUNG_TEXT if rueckfall else ""
    return aus


def aus_platte(cfg, profil=""):
    aus = dict(cfg)
    for k in FELDER:
        v = cfg.get(k)
        if not isinstance(v, str):
            continue
        if v.startswith(PREFIX):
            aus[k] = entschuetzen(v)
        elif v == KC + k:
            w = _kc_lesen(profil, k)
            aus[k] = w or ""                                    # nicht mehr im Schluesselbund -> neu einrichten
            if w:
                _GESPEICHERT[(profil, k)] = w
    return aus


def noch_klartext(cfg):
    """True, wenn ein Geheimnis noch ungeschuetzt in der Datei steht und ein Schluesselbund da ist (einmal neu schreiben)."""
    return bool(backend()) and any(isinstance(cfg.get(k), str) and cfg.get(k) and not cfg[k].startswith(PREFIX)
                                   and cfg[k] != KC + k for k in FELDER)
