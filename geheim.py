"""Geheimnisse in der Cockpit-Konfiguration schuetzen (Regel S: nie Klartext auf der Platte, wo es geht).

Windows: DPAPI (CurrentUser) ueber ctypes - nur derselbe Windows-Benutzer auf demselben Rechner kann entschluesseln.
Gespeichert wird "dpapi:<base64>". Linux/macOS: kein DPAPI in der Standardbibliothek; dort bleibt der Wert wie
bisher in config.json mit Dateirechten 0600 (nur der eigene Benutzer). Nur Standardbibliothek, kein Fremdpaket.
"""
import base64
import sys

# Felder, die nie im Klartext auf die Platte sollen
FELDER = ("password", "control_pin", "panoptes_jwt", "panoptes_code", "planer_token",
          "ha_src_token", "ha_pass", "pv_token", "charger_token")
PREFIX = "dpapi:"


def verfuegbar():
    return sys.platform == "win32"


def _blob(daten):
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
    puffer = ctypes.create_string_buffer(daten, len(daten))
    return DATA_BLOB(len(daten), ctypes.cast(puffer, ctypes.POINTER(ctypes.c_char))), puffer, DATA_BLOB


def _dpapi(daten, schuetzen):
    import ctypes
    ein, _puffer, DATA_BLOB = _blob(daten)
    aus = DATA_BLOB()
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    f = crypt32.CryptProtectData if schuetzen else crypt32.CryptUnprotectData
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


def fuer_platte(cfg):
    """Kopie der Konfiguration mit geschuetzten Geheimnissen (das Original im Speicher bleibt Klartext)."""
    return {k: (schuetzen(v) if k in FELDER else v) for k, v in cfg.items()}


def aus_platte(cfg):
    return {k: (entschuetzen(v) if k in FELDER else v) for k, v in cfg.items()}


def noch_klartext(cfg):
    """True, wenn auf Windows noch ein Geheimnis ungeschuetzt in der Datei steht (dann einmal neu schreiben)."""
    return verfuegbar() and any(isinstance(cfg.get(k), str) and cfg.get(k) and not cfg[k].startswith(PREFIX) for k in FELDER)
