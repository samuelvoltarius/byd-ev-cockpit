#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EV-Cockpit (Community) — eigenstaendiges, LOKALES Cockpit fuer BYD-Fahrzeuge.

Kein Home Assistant. Kein MQTT. Kein Docker. Kein fremder Server.
Ein Programm: Setup-Assistent im Browser -> fragt die BYD-Cloud DIREKT ab -> Cockpit.

DATENSCHUTZ: Alle Zugangsdaten und Fahrzeugdaten bleiben auf DIESEM Rechner
(~/.evcockpit/config.json). Dieses Programm sendet NICHTS an den Autor oder
irgendeinen Dritt-Server. Einzige Gegenstelle ist die BYD-Cloud selbst.

WICHTIG — ZWEITER BYD-ACCOUNT:
Die BYD-Cloud erlaubt pro Account nur ~eine aktive Sitzung. Wenn dieses Tool
denselben Account nutzt wie deine BYD-App am Handy, stoeren sich beide
(Fehler 6024 "letzter Vorgang nicht abgeschlossen").
=> Lege einen ZWEITEN BYD-Account an und gib ihn im Auto als "Zusatznutzer"
   frei. Dann laufen App und Cockpit konfliktfrei nebeneinander.
"""
import asyncio, json, os, re, threading, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.10.1"
KARTE_STIL = "https://byd.serveone.at/tiles/style/surfmate-dark.json"   # Community-Karte (wie Panoptes/SurfMate)
PING_URL = "https://byd.serveone.at/ev-cockpit/ping"   # NUR bei ausdruecklicher Einwilligung


def ping_optin():
    """Anonyme Nutzungszaehlung — AUSSCHLIESSLICH wenn der Nutzer sie im Assistenten
    aktiv angehakt hat. Standard ist AUS. Sendet genau drei Felder, sonst nichts:
    zufaellige Installations-ID (kein Personenbezug), Version, Automodell.
    Faellt still aus, wenn kein Netz — blockiert das Cockpit nie."""
    if _CFG.get("_ping_loeschen"):
        # Haekchen wurde weggenommen: alle Eintraege dieser Zufalls-ID beim Server loeschen (Regel 2);
        # ohne Netz bleibt der Auftrag stehen und wird beim naechsten Start nachgeholt.
        try:
            import urllib.request
            req = urllib.request.Request(PING_URL, data=json.dumps({"id": _CFG["_ping_loeschen"], "loeschen": True}).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=6).read()
            _CFG.pop("_ping_loeschen", None)
            save_cfg(_CFG)
        except Exception:
            pass
    if not _CFG.get("count_optin"):
        return
    try:
        import urllib.request
        last = _CFG.get("_last_ping", 0)
        if time.time() - last < 86400:        # hoechstens 1x pro Tag
            return
        data = json.dumps({"id": _CFG.get("install_id", ""), "version": VERSION,
                           "model": _CFG.get("model", "")}).encode()
        req = urllib.request.Request(PING_URL, data=data,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=6).read()
        _CFG["_last_ping"] = time.time()
        save_cfg(_CFG)
    except Exception:
        pass                                   # Zaehlung ist nie wichtig genug fuer eine Fehlermeldung

# Standard: nur auf diesem Rechner erreichbar (127.0.0.1) — das ist Absicht.
# Wer es bewusst im eigenen Netz braucht (NAS/Raspberry/Tablet):
#   EVCOCKPIT_BIND=0.0.0.0 EVCOCKPIT_PORT=8100 python3 evcockpit.py
WEBPORT = int(os.environ.get("EVCOCKPIT_PORT", "8099"))
BIND = os.environ.get("EVCOCKPIT_BIND", "127.0.0.1")
CFG_DIR = Path(os.environ.get("EVCOCKPIT_CFGDIR") or (Path.home() / ".evcockpit"))
CFG_FILE = CFG_DIR / "config.json"
CACHE_FILE = CFG_DIR / "cache.json"
PHOTO_FILE = CFG_DIR / "car_photo.jpg"
# Nur Verhaeltnisse gemessen/Modell je Planer-Profil (keine Fahrten, keine Orte) - bleibt hier.
PLANER_FAKTOR_FILE = CFG_DIR / "planer_faktor.json"
STATIC_DIR = Path(__file__).resolve().parent / "static"
THREE_DATEIEN = {
    "/static/three/three.module.min.js": "application/javascript",
    "/static/three/examples/jsm/loaders/GLTFLoader.js": "application/javascript",
    "/static/three/examples/jsm/loaders/DRACOLoader.js": "application/javascript",
    "/static/three/examples/jsm/utils/BufferGeometryUtils.js": "application/javascript",
    "/static/three/examples/jsm/libs/draco/gltf/draco_wasm_wrapper.js": "application/javascript",
    "/static/three/examples/jsm/libs/draco/gltf/draco_decoder.wasm": "application/wasm",
}
MODELL_DIR = CFG_DIR / "modelle"   # Leaflet liegt hier (kein CDN!)


def lan_ip():
    """Eigene LAN-Adresse ermitteln — fuer den Tablet-Hinweis."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))          # verbindet nicht wirklich, ermittelt nur das Interface
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

# Modell -> nutzbare Akku-kWh (Startwert, im Assistenten aenderbar!).
# Diese Zahl braucht NUR die realistische Reichweiten-Rechnung.
MODELS = {
    "BYD Dolphin Surf / Seagull (Active)":      30.1,
    "BYD Dolphin Surf / Seagull (Comfort/Design)": 43.2,
    "BYD Dolphin (Active/Boost)":               44.9,
    "BYD Dolphin (Comfort/Design)":             60.4,
    "BYD Atto 3":                               60.4,
    "BYD Seal (Design/RWD)":                    61.4,
    "BYD Seal (Excellence/AWD)":                82.5,
    "BYD Seal U EV (Comfort)":                  71.8,
    "BYD Seal U EV (Design)":                   87.0,
    "BYD Sealion 7 (Comfort)":                  82.5,
    "BYD Sealion 7 (Design AWD)":               91.3,
    "BYD Han":                                  85.4,
    "BYD Tang":                                 108.8,
    "Anderes / unbekannt":                      60.0,
}

# Modell -> Karosserieform fuer die Platzhalter-Silhouette.
# (Eine Silhouette zeigt bewusst NICHT das exakte Modell — Seal und Han sehen als
#  Limousine gleich aus. Wer sein Auto genau sehen will, laedt ein Foto hoch.)
BODY_TYPE = {
    "BYD Dolphin Surf / Seagull (Active)": "klein",
    "BYD Dolphin Surf / Seagull (Comfort/Design)": "klein",
    "BYD Dolphin (Active/Boost)": "klein",
    "BYD Dolphin (Comfort/Design)": "klein",
    "BYD Atto 3": "suv",
    "BYD Seal (Design/RWD)": "limo",
    "BYD Seal (Excellence/AWD)": "limo",
    "BYD Seal U EV (Comfort)": "suv",
    "BYD Seal U EV (Design)": "suv",
    "BYD Sealion 7 (Comfort)": "suv",
    "BYD Sealion 7 (Design AWD)": "suv",
    "BYD Han": "limo",
    "BYD Tang": "gross",
    "Anderes / unbekannt": "klein",
}

COUNTRIES = ["AT", "DE", "CH", "NL", "BE", "FR", "IT", "ES", "PT", "DK", "SE", "NO", "FI", "PL", "CZ", "HU", "GB", "IE"]
TIMEZONES = ["Europe/Vienna", "Europe/Berlin", "Europe/Zurich", "Europe/Amsterdam", "Europe/Brussels",
             "Europe/Paris", "Europe/Rome", "Europe/Madrid", "Europe/Lisbon", "Europe/Copenhagen",
             "Europe/Stockholm", "Europe/Oslo", "Europe/Helsinki", "Europe/Warsaw", "Europe/Prague",
             "Europe/Budapest", "Europe/London", "Europe/Dublin"]

# Strompreis-Quellen je Land. aWATTar (AT/DE) ist die erprobte Quelle, sonst energy-charts.info
# (Fraunhofer ISE, gratis, deckt die EU-Gebotszonen ab). Beide ohne Konto, ohne Schluessel.
# Laender mit mehreren Zonen: sinnvolle Standardzone (im Assistenten aenderbar).
PRICE_ZONES = {
    "AT": ("awattar", "https://api.awattar.at/v1/marketdata"),
    "DE": ("awattar", "https://api.awattar.de/v1/marketdata"),
    "CH": ("energycharts", "CH"),
    "NL": ("energycharts", "NL"),
    "BE": ("energycharts", "BE"),
    "FR": ("energycharts", "FR"),
    "IT": ("energycharts", "IT-North"),
    "ES": ("energycharts", "ES"),
    "PT": ("energycharts", "PT"),
    "DK": ("energycharts", "DK1"),
    "SE": ("energycharts", "SE3"),
    "NO": ("energycharts", "NO1"),
    "FI": ("energycharts", "FI"),
    "PL": ("energycharts", "PL"),
    "CZ": ("energycharts", "CZ"),
    "HU": ("energycharts", "HU"),
}

_STATE = {}
_CFG = {}
_LOCK = threading.Lock()
_HOLD_UNTIL = 0.0        # waehrend eines Befehls NICHT pollen (BYD erlaubt nur 1 Vorgang)
_MSG = {"text": "", "ts": 0}

POLL_AWAKE = 300         # 5 min wenn wach/geparkt
POLL_DRIVE = 90          # 1,5 min waehrend der Fahrt
POLL_IDLE = 900          # 15 min wenn das Auto schlaeft
POLL_PANOPTES = 60       # 1 min, solange Panoptes im Auto antwortet (kein Cloud-Kontingent)
POLL_HA = 60             # 1 min, Home Assistant als Quelle (lokal, kein Cloud-Kontingent)
# Panoptes-Takt (1.9.8): jede Abfrage weckt die App im Auto -> der Nutzer waehlt, wie oft.
ABFRAGE_WAHL = (1, 2, 5, 10, 15, 30, 0)   # Minuten; 0 = nur manuell (Knopf ↻)
ABFRAGE_STD = {"abfrage_geparkt": 5, "abfrage_fahrt": 1}
ABFRAGE_SCHNELL_S = 5        # nach einer Nutzeraktion kurz alle 5 s ...
ABFRAGE_SCHNELL_DAUER = 60   # ... hoechstens 60 s lang, dann wieder der gewaehlte Takt
SICHTBAR_FRIST = 30          # so lange nach dem letzten Abruf eines SICHTBAREN Tabs gilt "jemand schaut hin"


# ---------------------------------------------------------------- Konfig
def _profil_id():
    """Kurze Kennung des Profilordners, damit zwei Profile im Schluesselbund getrennt bleiben."""
    import hashlib
    return hashlib.sha256(str(CFG_DIR.resolve()).encode("utf-8")).hexdigest()[:12]


def load_cfg():
    """Im Speicher Klartext; auf der Platte sind Geheimnisse unter Windows per DPAPI geschuetzt (geheim.py)."""
    global _CFG
    import geheim
    try:
        roh = json.loads(CFG_FILE.read_text("utf-8-sig"))   # utf-8-sig: auch von Hand mit BOM gespeichert
    except Exception:
        roh = {}
    _CFG = geheim.aus_platte(roh, _profil_id())
    if geheim.noch_klartext(roh):
        try:
            save_cfg(_CFG)                 # aeltere Version: Klartext-Geheimnisse einmal geschuetzt neu schreiben
        except Exception:
            pass
    return _CFG


def save_cfg(c):
    import geheim
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CFG_FILE.with_name(CFG_FILE.name + ".neu")
    tmp.write_text(json.dumps(geheim.fuer_platte(c, _profil_id()), indent=1, ensure_ascii=False), "utf-8")
    try:
        os.chmod(tmp, 0o600)           # nur der eigene Benutzer darf lesen
    except Exception:
        pass
    os.replace(tmp, CFG_FILE)


def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text("utf-8-sig"))
    except Exception:
        return {}


def save_cache(c):
    try:
        CFG_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(c, ensure_ascii=False), "utf-8")
    except Exception:
        pass


def byd_cfg():
    from pybyd import BydConfig
    return BydConfig(username=_CFG["username"], password=_CFG["password"],
                     control_pin=_CFG["control_pin"], country_code=_CFG.get("country_code", "AT"),
                     language=_CFG.get("language", "de"), time_zone=_CFG.get("time_zone", "Europe/Vienna"))


def ev(x):
    try:
        return x.value if hasattr(x, "value") else x
    except Exception:
        return x


# ---------------------------------------------------------------- BYD abfragen
async def _fetch_vehicles(cfg_dict):
    """Fuer den Assistenten: einloggen und die Fahrzeuge des Accounts holen."""
    from pybyd import BydClient, BydConfig
    conf = BydConfig(username=cfg_dict["username"], password=cfg_dict["password"],
                     control_pin=cfg_dict.get("control_pin", "000000"),
                     country_code=cfg_dict.get("country_code", "AT"),
                     language=cfg_dict.get("language", "de"),
                     time_zone=cfg_dict.get("time_zone", "Europe/Vienna"))
    async with BydClient(conf) as c:
        await c.login()
        out = []
        try:
            vs = await c.get_vehicles()
        except Exception:
            vs = None
        if vs:
            for v in (vs if isinstance(vs, list) else [vs]):
                vin = getattr(v, "vin", None) or (v.get("vin") if isinstance(v, dict) else None)
                nm = getattr(v, "series_name", None) or getattr(v, "model", None) or ""
                if vin:
                    out.append({"vin": vin, "name": str(nm)})
        return out


async def _poll_once(byd, cache):
    vin = _CFG["vin"]
    await byd.login()
    rt = await byd.get_vehicle_realtime(vin)
    try:
        gps = await byd.get_gps_info(vin)
    except Exception:
        gps = None
    try:
        chg = await byd.get_charging_status(vin)
    except Exception:
        chg = None
    try:
        hv = await byd.get_hvac_status(vin)
    except Exception:
        hv = None

    online = ev(getattr(rt, "online_state", -1)) not in (-1, 0) or ev(getattr(rt, "vehicle_state", 0)) == 1

    def g(attr, default=None):
        return ev(getattr(rt, attr, default))

    st = {}
    st["odometer"] = g("total_mileage") or cache.get("odometer")
    st["soc"] = g("elec_percent") or cache.get("soc")
    st["range_km"] = g("endurance_mileage") or cache.get("range_km")      # BYDs eigene Anzeige
    for k, a in [("tyre_fl", "left_front_tire_pressure"), ("tyre_fr", "right_front_tire_pressure"),
                 ("tyre_rl", "left_rear_tire_pressure"), ("tyre_rr", "right_rear_tire_pressure")]:
        v = g(a)
        st[k] = v if v else cache.get(k)
    try:
        st["consumption_avg"] = float(getattr(rt, "total_energy_ev", None) or cache.get("consumption_avg") or 0) or cache.get("consumption_avg")
    except Exception:
        st["consumption_avg"] = cache.get("consumption_avg")
    # realistische Reichweite aus ECHTEM Verbrauch (BYDs Zahl ist meist optimistisch)
    _c, _s = st.get("consumption_avg"), st.get("soc")
    kwh = float(_CFG.get("battery_kwh") or 60.0)
    st["real_range_km"] = round(kwh * (_s / 100.0) / _c * 100) if (_c and _s) else cache.get("real_range_km")
    st["charge_power"] = g("power_battery")
    st["gear"] = {1: "P", 2: "R", 3: "N", 4: "D"}.get(ev(getattr(rt, "power_gear", None)), cache.get("gear"))
    # Fuer die Sperre der Fernbefehle (sicherheit.py): Zuendungszustand und Tempo aus DIESER ohnehin
    # laufenden Abfrage merken - nie aus dem Cache, damit kein alter Wert als Beweis dient.
    _vs = ev(getattr(rt, "vehicle_state", None))
    st["vehicle_state"] = _vs if isinstance(_vs, int) else None
    st["speed"] = g("speed")
    st["_zustand_t"] = time.time()

    _hvraw = hv.raw if hv is not None else {}
    tout = g("temp_out_car")
    if tout is None:
        _to = _hvraw.get("tempOutCar")
        if isinstance(_to, (int, float)) and _to > -50:
            tout = _to
    st["temp_out"] = tout if tout is not None else cache.get("temp_out")

    # Verriegelt: Rohfeld ist camelCase (leftFrontDoorLock), 2 = verriegelt
    _rr = getattr(rt, "raw", None) or {}
    lv = [_rr.get(k) for k in ("leftFrontDoorLock", "rightFrontDoorLock", "leftRearDoorLock", "rightRearDoorLock")]
    lv = [v for v in lv if isinstance(v, int)]
    st["locked"] = ("ON" if all(v == 2 for v in lv) else "OFF") if lv else cache.get("locked", "OFF")

    doors = [ev(getattr(rt, a, 0)) for a in ("left_front_door", "right_front_door", "left_rear_door", "right_rear_door")]
    st["doors_open"] = "ON" if any(x == 1 for x in doors) else "OFF"
    wp = [ev(getattr(rt, a, 0)) for a in ("left_front_window_pct", "right_front_window_pct",
                                          "left_rear_window_pct", "right_rear_window_pct")]
    st["windows_open"] = "ON" if any(isinstance(x, (int, float)) and x > 0 for x in wp) else "OFF"

    chs = ev(getattr(chg, "charging_state", -1)) if chg is not None else -1
    st["charging"] = "ON" if chs == 1 else "OFF"
    cn = ev(getattr(chg, "connect_state", -1)) if chg is not None else -1
    st["plugged"] = "ON" if cn in (1, 2) else "OFF"
    # Restzeit: BYD liefert Stunden+Minuten getrennt, -1 wenn unbekannt.
    fh = ev(getattr(chg, "full_hour", None)) if chg is not None else None
    fm = ev(getattr(chg, "full_minute", None)) if chg is not None else None
    if (fh is not None and fh >= 0) or (fm is not None and fm >= 0):
        st["charge_remaining"] = "%dh %02dmin" % (max(fh or 0, 0), max(fm or 0, 0))
    else:
        st["charge_remaining"] = cache.get("charge_remaining")
    st["online"] = "ON" if online else "OFF"
    bh = ev(getattr(rt, "battery_heat_state", 0))
    st["battery_heat"] = "ON" if bh == 1 else "OFF"

    # Klima laeuft? Luefter (windPosition/firstWind/secondWind) oder acSwitch==2. tempInCar=-129 ist Muell.
    def hf(k):
        v = _hvraw.get(k, 0)
        return v if isinstance(v, (int, float)) else 0
    st["klima_on"] = "ON" if (hf("acSwitch") == 2 or hf("windPosition") > 0 or
                              hf("firstWind") > 0 or hf("secondWind") > 0) else "OFF"

    if gps is not None:
        la, lo = ev(getattr(gps, "latitude", None)), ev(getattr(gps, "longitude", None))
        if la and lo:
            st["latitude"], st["longitude"] = la, lo
    if "latitude" not in st:
        st["latitude"], st["longitude"] = cache.get("latitude"), cache.get("longitude")

    return st, online


def _friendly(e):
    """BYD-Fehler in Klartext uebersetzen — der Nutzer soll wissen, was zu tun ist."""
    m = str(e)
    if "3002" in m:
        return ("BYD hat E-Mail oder Passwort abgelehnt (Fehler 3002). "
                "Automatische Versuche wurden gestoppt — bitte das separate Cockpit-Konto prüfen.")
    if "6024" in m or "1008" in m or "nicht abgeschlossen" in m:
        return ("BYD ist beschäftigt. Läuft deine BYD-App mit DEMSELBEN Account? "
                "Bitte einen zweiten Account als Zusatznutzer verwenden.")
    if any(x in m.lower() for x in ("password", "auth", "login", "credential")):
        return "Login abgelehnt — E-Mail, Passwort oder Land stimmen nicht (⚙︎ → neu einrichten)."
    if "not supported" in m or "1001" in m:
        return "BYD liefert für diese VIN gerade keine Daten (oft nur kurz — es versucht's weiter)."
    return m[:150]


def _auth_failure(error):
    message = str(error).lower()
    return "3002" in message or any(word in message for word in
                                    ("wrong password", "falsche e-mail", "falsches passwort",
                                     "invalid credential", "login failed"))


from sicherheit import befehl_erlaubt, aus_letzter_abfrage, ERLAUBTE_BEFEHLE, NIE
from live_saeulen import Live

_LIVE = Live()

_PANOPTES = {"key": None, "obj": None}
_PAN_TEST = {"url": "", "jwt": "", "verbraucht": False, "kopplung_id": ""}   # JWT aus Test bzw. erlaubter Anfrage
def _kartenquelle():
    """"community" | "osm" | "keine". Nur eine ausdrueckliche Wahl (ab 1.9.2) zaehlt; ohne Wahl werden gar keine
    Kartenkacheln geladen - auch OpenStreetMap sieht IP und Gegend (Regel 2)."""
    q = _CFG.get("kartenquelle")
    return q if q in ("community", "osm") else "keine"


EINWILLIGUNG_STAND = "1.9.2"     # einmaliger Hinweis "Karte und 3D sind freiwillig" bis zu dieser Version
_PAN_ANFRAGE = {"url": "", "id": "", "bis": 0.0}     # offene Kopplungs-Anfrage; id = Abholrecht, bleibt im Prozess
_PLANER_NEU = {"poll": "", "token": "", "bis": 0.0}  # Planer-Geraete-Fluss; pollId = Abholrecht, bleibt im Prozess
DISCLAIMER_VERSION = "2026-10-21"                    # Textversion der Hinweise im Assistenten (DISCLAIMER.md Fassung 1)
_KOPPLUNG_GRUND = {
    "zu_alt": "Dieses Panoptes kann Anfragen noch nicht (erst ab Version 0.1.7). Nimm unter „Erweitert“ den Kopplungs-Code.",
    "zu_viele_offen": "In Panoptes warten schon 3 Anfragen. Bitte dort ablehnen oder 2 Minuten warten.",
    "ratenlimit": "Zu viele Anfragen in kurzer Zeit. Bitte 10 Minuten warten.",
    "pruefzahl": "Fehler bei der Prüfzahl. Bitte nochmal versuchen."}
_KOPPLUNG_STATUS = {
    "abgelehnt": "In Panoptes abgelehnt.",
    "abgelaufen": "Nicht rechtzeitig erlaubt (2 Minuten). Bitte nochmal verbinden.",
    "abgeholt": "Diese Erlaubnis wurde schon abgeholt. Bitte nochmal verbinden.",
    "unbekannt": "Panoptes kennt die Anfrage nicht mehr (neu gestartet?). Bitte nochmal verbinden.",
    "fehler": "Unerwartete Antwort von Panoptes. Bitte nochmal verbinden."}


def _cloud_an():
    """BYD-Cloud eingerichtet? (Ohne Konto - Quelle HA oder Panoptes - gibt es nur eine lokale Kennung.)"""
    return bool(_CFG.get("username") and _CFG.get("password") and _CFG.get("vin")
                and not str(_CFG.get("vin")).startswith("lokal-"))


def _ha_quelle_runde(cache):
    """Eine Abfrage bei Home Assistant als Datenquelle. True = Werte kamen von dort."""
    import ha_quelle
    t0 = time.time()
    try:
        st = ha_quelle.aus_states(ha_quelle.hole_states(_CFG["ha_src_url"], _CFG["ha_src_token"]),
                                  _CFG.get("ha_src_map") or {})
    except Exception as e:
        _STATE["_err"] = "Home Assistant nicht erreichbar (%s) — Adresse und Token prüfen." % type(e).__name__
        return False
    if "soc" not in st:
        _STATE["_err"] = "Home Assistant liefert gerade keinen Ladestand (Sensor „unavailable“?)."
        return False
    _c = cache.get("consumption_avg")
    if _c and st.get("soc"):
        st["real_range_km"] = round(float(_CFG.get("battery_kwh") or 60.0) * st["soc"] / 100.0 / _c * 100)
    st["online"] = "ON"
    cache.update({k: v for k, v in st.items() if v is not None})
    save_cache(cache)
    _STATE.update(st)
    _STATE.update({"_err": "", "_poll_ts": time.time(), "quelle": "Home Assistant",
                   "_latency_ms": int((time.time() - t0) * 1000)})
    return True                       # bewusst KEIN _ha_publish: was aus HA kommt, nicht nach HA zurueck


def _panoptes_verbindung():
    """Gekoppeltes Panoptes oder None (JWT bleibt auf diesem Rechner)."""
    return _panoptes_obj()


def _panoptes_gekoppelt():
    return bool(_CFG.get("panoptes") and _CFG.get("panoptes_url") and (_CFG.get("panoptes_code") or _CFG.get("panoptes_jwt")))


def _panoptes_obj():
    """Kopplung (Vertrag v1.1): Der Kopplungs-Code ist einmal verwendbar - nach dem Tausch zaehlt nur der JWT,
    der Code wird aus der Konfiguration geloescht."""
    if not _panoptes_gekoppelt():
        return None
    from panoptes_source import Panoptes
    key = (_CFG.get("panoptes_url"), _CFG.get("panoptes_code") or "jwt")
    if _PANOPTES["key"] != key:
        def merken(jwt, code_verbraucht=False):
            _CFG["panoptes_jwt"] = jwt
            if code_verbraucht:
                _CFG["panoptes_code"] = ""
                _PANOPTES["key"] = (_CFG.get("panoptes_url"), "jwt")
            save_cfg(_CFG)
        _PANOPTES.update(key=key, obj=Panoptes(key[0], _CFG.get("panoptes_code", ""), _CFG.get("panoptes_jwt", ""),
                                               jwt_gespeichert=merken))
    return _PANOPTES["obj"]


def _panoptes_runde(cache):
    """Eine Abfrage bei Panoptes im Auto. True = Daten kamen von dort (dann keine BYD-Cloud-Abfrage)."""
    pv = _panoptes_obj()
    if pv is None:
        return False
    t0 = time.time()
    _abfrage_zaehlen()                   # jede Abfrage weckt die App im Auto -> ehrlich mitzaehlen
    st = pv.lies()
    if not st:
        _STATE["panoptes_erreichbar"] = False
        _STATE["panoptes_fehler"] = pv.letzter_fehler
        return False
    st.pop("_quelle", None)
    if not _CFG.get("panoptes_code") and time.time() - float(_CFG.get("panoptes_erneuert") or 0) > 86400:
        try:
            from panoptes_source import sitzung_erneuern
            sitzung_erneuern(pv)                       # neuer JWT wird ueber jwt_gespeichert gesichert
            _CFG["panoptes_erneuert"] = time.time()
        except Exception:
            _CFG["panoptes_erneuert"] = time.time() - 86400 + 6 * 3600   # aeltere Panoptes ohne Endpunkt: in 6 h wieder
        save_cfg(_CFG)
    _schaetz = st.pop("usable_kwh", None)
    if _schaetz and _CFG.get("battery_quelle") != "manuell":
        # Panoptes rechnet usableKwh = Nennkapazitaet x geschaetzte Akku-Gesundheit (SOH) - KEIN Messwert vom Auto,
        # kann ueber der Nennkapazitaet liegen. Darum: als Schaetzung kennzeichnen, hoechstens die Nennkapazitaet des Modells.
        nenn = MODELS.get(_CFG.get("model") or "") if (_CFG.get("model") or "") != "Anderes / unbekannt" else None
        wert = min(_schaetz, nenn) if nenn else _schaetz
        if (abs(float(_CFG.get("battery_kwh") or 0) - wert) >= 0.05 or _CFG.get("battery_quelle") != BATTERIE_SCHAETZUNG
                or _CFG.get("battery_schaetzung") != _schaetz):
            _CFG.update(battery_kwh=wert, battery_quelle=BATTERIE_SCHAETZUNG, battery_schaetzung=_schaetz,
                        battery_nenn=nenn)
            save_cfg(_CFG)
    _c, _s = st.get("consumption_avg") or cache.get("consumption_avg"), st.get("soc")   # Panoptes liefert ihn mit
    kwh = float(_CFG.get("battery_kwh") or 60.0)
    if _c and _s:
        st["real_range_km"] = round(kwh * (_s / 100.0) / _c * 100)
    cache.update({k: v for k, v in st.items() if v is not None})
    save_cache(cache)
    _STATE.update(st)
    _STATE.update({"_err": "", "_poll_ts": time.time(), "quelle": "Panoptes", "panoptes_erreichbar": True,
                   "_latency_ms": int((time.time() - t0) * 1000)})
    _ha_publish(st)
    return True


_WECKER = threading.Event()
_TAKT = {"sichtbar_ts": 0.0, "schnell_bis": 0.0, "tag": "", "heute": 0}


BATTERIE_SCHAETZUNG = "Panoptes (geschätzt)"


def _abfrage_min(key):
    try:
        v = int(_CFG.get(key, ABFRAGE_STD[key]))
    except (TypeError, ValueError):
        v = ABFRAGE_STD[key]
    return v if v in ABFRAGE_WAHL else ABFRAGE_STD[key]


def _unterwegs():
    return str(_STATE.get("gear") or "").upper() in ("D", "R") or _STATE.get("charging") == "ON"


def _panoptes_takt(jetzt=None):
    """Sekunden bis zur naechsten Panoptes-Abfrage, None = gerade keine (nur manuell oder kein Tab sichtbar)."""
    jetzt = time.time() if jetzt is None else jetzt
    if jetzt < _TAKT["schnell_bis"]:
        return ABFRAGE_SCHNELL_S
    if jetzt - _TAKT["sichtbar_ts"] > SICHTBAR_FRIST and not _CFG.get("ha"):
        return None                      # Tab verborgen/zu -> pausiert (ausser Werte gehen an Home Assistant)
    m = _abfrage_min("abfrage_fahrt" if _unterwegs() else "abfrage_geparkt")
    return m * 60 if m else None


def _abfrage_zaehlen():
    tag = time.strftime("%Y-%m-%d")
    if _TAKT["tag"] != tag:
        _TAKT.update(tag=tag, heute=0)
    _TAKT["heute"] += 1


def _warte_panoptes(seit):
    """Wartet bis zur naechsten faelligen Abfrage; der Takt wird jede Sekunde neu bewertet
    (Tab wieder sichtbar, Einstellung geaendert, Knopf gedrueckt)."""
    while True:
        if _WECKER.wait(1):
            _WECKER.clear()
            return
        t = _panoptes_takt()
        if t is not None and time.time() - seit >= t:
            return


def nutzer_aktion():
    """Nutzer hat etwas getan: sofort abfragen, dann kurz alle 5 s (hoechstens 60 s)."""
    _TAKT["schnell_bis"] = time.time() + ABFRAGE_SCHNELL_DAUER
    _WECKER.set()


def abfrage_status():
    t = _panoptes_takt()
    return {"geparkt": _abfrage_min("abfrage_geparkt"), "fahrt": _abfrage_min("abfrage_fahrt"),
            "heute": _TAKT["heute"] if _TAKT["tag"] == time.strftime("%Y-%m-%d") else 0,
            "schnell": time.time() < _TAKT["schnell_bis"], "unterwegs": _unterwegs(),
            "takt_s": t, "pausiert": t is None and time.time() - _TAKT["sichtbar_ts"] > SICHTBAR_FRIST
            and not _CFG.get("ha")}


def _poller():
    # Import defensiv: sonst stirbt der Thread lautlos und das Cockpit bleibt ewig leer.
    try:
        from pybyd import BydClient
    except Exception as e:
        _STATE["_err"] = ("pybyd fehlt — bitte einmal installieren:  pip install pybyd   (%s)"
                          % str(e)[:60])
        return
    cache = load_cache()
    _STATE.update({k: v for k, v in cache.items() if v is not None})   # sofort letzte bekannte Werte zeigen
    st = None
    while True:
        try:
            if not _CFG.get("vin"):
                time.sleep(3)
                continue
            _r0 = time.time()
            if _panoptes_runde(cache):
                _warte_panoptes(_r0)
                continue
            if _CFG.get("datenquelle") == "ha":
                # Nie zusaetzlich die BYD-Cloud abfragen: haengt an HA schon eine BYD-Anbindung mit
                # demselben Konto, gaebe es Fehler 6024. Die Cloud bleibt nur fuer Fernbefehle.
                _ha_quelle_runde(cache)
                time.sleep(POLL_HA)
                continue
            if not _cloud_an():
                _STATE["_err"] = ("Keine Daten: Panoptes im Auto antwortet gerade nicht und es ist kein "
                                  "BYD-Konto eingerichtet. Ist das Auto wach und im Netz?")
                _warte_panoptes(_r0) if _panoptes_gekoppelt() else time.sleep(POLL_PANOPTES)
                continue
            if _STATE.get("_auth_blocked") or _CFG.get("auth_blocked"):
                _STATE["_auth_blocked"] = True
                _STATE["_err"] = ("BYD-Anmeldung pausiert. Bitte in den Einstellungen das separate "
                                  "Cockpit-Konto korrigieren und einmal bewusst speichern.")
                time.sleep(30)
                continue
            if time.time() < _HOLD_UNTIL:    # Befehl laeuft -> nicht pollen (sonst 6024-Kollision)
                time.sleep(4)
                continue
            online = False
            try:
                async def _w():
                    async with BydClient(byd_cfg()) as b:
                        return await _poll_once(b, cache)
                with _LOCK:
                    st, online = asyncio.run(_w())
                cache.update({k: v for k, v in st.items() if v is not None})
                save_cache(cache)
                _STATE.update(st)
                _STATE["_err"] = ""
                _STATE["_poll_ts"] = time.time()
                _STATE["quelle"] = "BYD-Cloud"
                _ha_publish(st)          # tut nichts ohne Haekchen
            except Exception as e:
                _STATE["_err"] = _friendly(e)
                if _auth_failure(e):
                    _STATE["_auth_blocked"] = True
                    _CFG["auth_blocked"] = True
                    save_cfg(_CFG)
            drv = online and str((st or {}).get("gear", "")).upper() in ("D", "R")
            # Takt aus dem Assistenten (Minuten). Schlafendes Auto immer 15 min -> schont die 12V.
            wach = max(60, int(_CFG.get("poll_min") or 5) * 60)
            time.sleep(POLL_DRIVE if drv else (wach if online else POLL_IDLE))
        except Exception as e:               # nichts darf den Poller killen
            _STATE["_err"] = _friendly(e)
            time.sleep(30)


# ---------------------------------------------------------------- Ladesaeulen in der Naehe (optional)
def _dist_km(la1, lo1, la2, lo2):
    from math import radians, sin, cos, asin, sqrt
    dla, dlo = radians(la2 - la1), radians(lo2 - lo1)
    a = sin(dla / 2) ** 2 + cos(radians(la1)) * cos(radians(la2)) * sin(dlo / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(a))


def _charger_rows(data, lat, lon):
    """Normalise OpenGlance/Overpass and legacy Copilot charger responses."""
    elements = data.get("elements") if isinstance(data, dict) else None
    if isinstance(elements, list):
        rows = []
        for e in elements:
            t = e.get("tags", {}) or {}
            la, lo = e.get("lat"), e.get("lon")
            try:
                la, lo = float(la), float(lo)
            except (TypeError, ValueError):
                continue
            socks, powers = [], []
            for key, value in t.items():
                if key.startswith("socket:") and key.count(":") == 1 and str(value).lower() not in ("no", "0"):
                    socks.append(key.split(":", 1)[1].replace("_", " "))
                if key.endswith(":output") or key in ("charging_station:output", "maxpower"):
                    try:
                        powers.append(float(str(value).lower().replace("kw", "").strip()))
                    except ValueError:
                        pass
            try:
                price = float(t.get("x:price_eur_kwh")) if t.get("x:price_eur_kwh") else None
            except (TypeError, ValueError):
                price = None
            rows.append({
                "name": str(t.get("name") or t.get("operator") or "Ladestation")[:80],
                "operator": str(t.get("operator") or "")[:60],
                "km": round(_dist_km(lat, lon, la, lo), 1),
                "sockets": ", ".join(sorted(set(socks))[:4]),
                "kw": max(powers) if powers else None,
                "n": str(t.get("capacity") or "")[:12],
                "eur_kwh": price if price and 0.1 <= price <= 3 else None,
                "source": str(t.get("x:source") or "OpenStreetMap")[:40],
                "lat": la, "lon": lo,
            })
        return rows
    if isinstance(data, list):
        rows = []
        for item in data:
            try:
                la, lo = float(item.get("lat")), float(item.get("lon"))
            except (AttributeError, TypeError, ValueError):
                continue
            sockets = item.get("stecker") or item.get("sockets") or []
            if isinstance(sockets, list):
                sockets = ", ".join(str(x).replace("_", " ") for x in sockets[:4])
            ct = item.get("ct_kwh")
            rows.append({
                "name": str(item.get("name") or "Ladestation")[:80],
                "operator": str(item.get("operator") or "")[:60],
                "km": round(_dist_km(lat, lon, la, lo), 1),
                "sockets": str(sockets)[:100], "kw": item.get("kw"),
                "n": str(item.get("punkte") or item.get("n") or "")[:12],
                "eur_kwh": (float(ct) / 100) if isinstance(ct, (int, float)) and ct > 0 else None,
                "source": str(item.get("quelle") or "Eigener Server")[:40],
                "lat": la, "lon": lo,
            })
        return rows
    return None


def _fetch_chargers_server(lat, lon, radius_m, base_url, token=""):
    """Read the OpenGlance `/chargers` endpoint (or the older Copilot endpoint)."""
    import urllib.request
    base = str(base_url or "").strip().rstrip("/")
    if not base.startswith(("https://", "http://")) or len(base) > 300:
        return None
    endpoint = base if base.endswith(("/chargers", "/api/chargers")) else base + "/chargers"
    query = urllib.parse.urlencode({"lat": f"{lat:.6f}", "lon": f"{lon:.6f}",
                                    "radius": int(radius_m)})
    headers = {"Accept": "application/json", "User-Agent": "EV-Cockpit/%s" % VERSION}
    if token:
        headers["Authorization"] = "Bearer " + token
        headers["X-Copilot-Token"] = token
    try:
        req = urllib.request.Request(endpoint + "?" + query, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            return None
        return _charger_rows(json.loads(raw.decode("utf-8")), lat, lon)
    except Exception:
        return None


def _fetch_chargers(lat, lon, radius_m=10000):
    """Ladesaeulen aus OpenStreetMap (Overpass). Kein Schluessel, keine Anmeldung.
    BEWUSST OHNE PREISE: es gibt keine verlaessliche freie Preisquelle — falsche Preise
    waeren schlimmer als gar keine. Daten sind Community-gepflegt, also ohne Gewaehr."""
    import urllib.request
    own_url = _CFG.get("charger_url") or os.environ.get("EVCOCKPIT_CHARGERS_URL", "")
    if own_url:
        own = _fetch_chargers_server(lat, lon, radius_m, own_url,
                                     _CFG.get("charger_token") or os.environ.get("EVCOCKPIT_CHARGERS_TOKEN", ""))
        if own is not None:
            _STATE["charger_source"] = "Eigener OpenGlance-Server · E-Control / Bundesnetzagentur"
            own.sort(key=lambda x: x["km"])
            return own[:8]
    q = ('[out:json][timeout:25];node["amenity"="charging_station"](around:%d,%f,%f);out body 40;'
         % (radius_m, lat, lon))
    # Overpass ist ein freier Gemeinschaftsdienst und antwortet unter Last auch mal mit 504.
    # Darum zwei Server nacheinander probieren, bevor wir aufgeben.
    d = None
    for host in ("https://overpass-api.de/api/interpreter",
                 "https://overpass.kumi.systems/api/interpreter"):
        try:
            req = urllib.request.Request(host, data=("data=" + urllib.parse.quote(q)).encode(),
                                         headers={"User-Agent": "EV-Cockpit/%s (privates Werkzeug)" % VERSION})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read().decode())
            break
        except Exception:
            continue
    if not d:
        return []
    _STATE["charger_source"] = "OpenStreetMap · öffentliche Ausweichquelle"
    # OSM nutzt amenity=charging_station AUCH fuer E-Bike-Ladepunkte — in der Praxis ist das
    # fast die Haelfte der Treffer. Ohne Filter zeigen wir einem Autofahrer Fahrradsaeulen.
    AUTO_STECKER = ("type2", "type2_combo", "type2_cable", "ccs", "chademo", "type1",
                    "type1_combo", "type3", "type3c", "tesla_supercharger", "tesla_destination")

    def ist_auto(t):
        mc = (t.get("motorcar") or "").lower()
        if mc == "no":
            return False              # explizit kein Auto -> raus (kickt die Fahrrad-Punkte sauber)
        if mc == "yes":
            return True
        # kein motorcar-Tag: nur nehmen, wenn ein AUTO-Stecker getaggt ist (z.B. Salzburg AG: type2)
        return any(k.startswith("socket:") and k.split(":")[1] in AUTO_STECKER for k in t)

    out = []
    for e in d.get("elements", []):
        t = e.get("tags", {}) or {}
        la, lo = e.get("lat"), e.get("lon")
        if la is None or lo is None or not ist_auto(t):
            continue
        # Steckertypen und Leistung aus den OSM-Tags zusammensuchen (sehr uneinheitlich gepflegt)
        socks, kw = [], []
        for k, v in t.items():
            if k.startswith("socket:") and k.count(":") == 1 and v not in ("no", "0"):
                socks.append(k.split(":")[1].replace("_", " "))
            if k.endswith(":output") or k == "charging_station:output":
                try:
                    kw.append(float(str(v).lower().replace("kw", "").strip()))
                except Exception:
                    pass
        out.append({
            "name": (t.get("name") or t.get("operator") or "Ladestation")[:42],
            "operator": (t.get("operator") or "")[:30],
            "km": round(_dist_km(lat, lon, la, lo), 1),
            "sockets": ", ".join(sorted(set(socks))[:3]),
            "kw": max(kw) if kw else None,
            "n": t.get("capacity") or "",
            "lat": la, "lon": lo,
        })
    out.sort(key=lambda x: x["km"])
    return out[:8]


def _charger_loop():
    """Laeuft NUR mit Haekchen. Overpass ist ein freier Gemeinschaftsdienst — deshalb
    nur neu abfragen, wenn das Auto sich wirklich bewegt hat (>3 km), sonst alle 12 h."""
    letzte = None
    while True:
        try:
            if _CFG.get("show_chargers") and _STATE.get("latitude"):
                la, lo = _STATE["latitude"], _STATE["longitude"]
                weit = letzte is None or _dist_km(letzte[0], letzte[1], la, lo) > 3
                alt = time.time() - (_STATE.get("_chg_ts") or 0) > 43200
                if weit or alt:
                    c = _fetch_chargers(la, lo)
                    _STATE["chargers"] = c
                    _STATE["_chg_ts"] = time.time()
                    letzte = (la, lo)
        except Exception:
            pass                       # Ladesaeulen sind nie wichtig genug fuer eine Fehlermeldung
        # Noch nichts gefunden (z.B. Overpass ueberlastet)? Bald nochmal statt 10 min stumm.
        time.sleep(600 if _STATE.get("chargers") else 60)


# ---------------------------------------------------------------- Routenplaner der BYD-Community (optional)
_PLANER = None
_ROUTE = {"t": 0.0, "d": None, "fehler": ""}
_PAN_ID = {"t": 0.0, "auto": ""}


_RPLAN = {}                    # letzte berechnete Route, nur im Arbeitsspeicher (fuer "Ins Auto schicken")
_PROFIL = {"t": 0.0, "name": ""}


def _planer_profil(tok):
    """Fahrzeugprofil fuer den Planer: im Assistenten gewaehlt, sonst das zum Modell passende (stuendlich neu)."""
    if _CFG.get("planer_fahrzeug"):
        return _CFG["planer_fahrzeug"]
    if not _PROFIL["name"] or time.time() - _PROFIL["t"] > 3600:
        import planer_bridge as pb
        _PROFIL.update(t=time.time(), name=pb.passendes_profil(pb.fahrzeuge(tok), _CFG.get("model"),
                                                              float(_CFG.get("battery_kwh") or 0)))
    return _PROFIL["name"]


def _planer_kennung():
    """Welche auto-Kennung beim Planer gilt: mit Panoptes gekoppelt die von Panoptes (dieselbe Route und
    Rueckmeldung wie im Auto, stuendlich nachgefragt), sonst die eigene des Cockpits."""
    if _CFG.get("panoptes") and _PANOPTES.get("obj") is not None:
        if time.time() - _PAN_ID["t"] > 3600:
            from panoptes_source import identitaet
            _PAN_ID.update(t=time.time(), auto=identitaet(_PANOPTES["obj"]))
        if _PAN_ID["auto"]:
            return _PAN_ID["auto"]
    return _CFG.get("planer_auto") or ""


class _ManifestLazy:
    """Manifest der 3D-Modelle erst laden, wenn das Cockpit es braucht."""
    def __init__(self):
        self.m = None

    def get(self):
        if self.m is None:
            import modell3d
            self.m = modell3d.Manifest()
        return self.m.get()


_MANIFEST = _ManifestLazy()
_TARIFE = {"t": 0.0, "d": []}


def _planer_loop():
    """Nach jeder BYD-Abfrage: Ladestand (und erkannte Fahrten) an den persoenlichen Planer.
    Tut nichts ohne Haekchen und Planer-Link."""
    global _PLANER
    try:
        from planer_bridge import Bruecke, neue_auto_kennung
    except Exception:
        return

    def laden():
        try:
            return json.loads(PLANER_FAKTOR_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def speichern(d):
        CFG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = PLANER_FAKTOR_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(d), encoding="utf-8")
        os.replace(tmp, PLANER_FAKTOR_FILE)

    _PLANER = Bruecke(speicher=(laden, speichern))
    zuletzt = None
    while True:
        time.sleep(15)
        ts = _STATE.get("_poll_ts")
        if not ts or ts == zuletzt:
            continue
        zuletzt = ts
        if _CFG.get("planer") and not _CFG.get("planer_auto"):
            _CFG["planer_auto"] = neue_auto_kennung()     # einmal je Fahrzeug, nie die VIN
            save_cfg(_CFG)
        try:
            _PLANER.nach_abfrage(_CFG, dict(_STATE))
        except Exception as e:           # Planer ist Zugabe - nie das Cockpit stoeren
            _PLANER.status["fehler"] = "Planer nicht erreichbar (%s)" % type(e).__name__


# ---------------------------------------------------------------- Waechter-Kamera (optional, Bastler)
# Glob ueber alle Sticks -> Stick-Wechsel egal. Panoptes (vormals SurfMate) und Overdrive:
# ls -t sortiert die Treffer beider Ordner gemeinsam, die neueste Aufnahme gewinnt.
SENT_GLOB = " ".join(d + "/event_*.jpg" for d in (
    "/storage/*/Panoptes/surveillance", "/storage/*/SurfMate/surveillance",
    "/storage/*/Overdrive/surveillance"))


def _adb(args, timeout=30):
    import subprocess
    return subprocess.run(["adb", "-s", _CFG.get("car_adb", "")] + args,
                          capture_output=True, timeout=timeout)


def _local_capabilities():
    """Detect optional local helpers without changing or connecting anything."""
    import shutil
    import subprocess
    adb_path = shutil.which("adb")
    devices = []
    if adb_path:
        try:
            result = subprocess.run([adb_path, "devices"], capture_output=True, text=True,
                                    timeout=5, check=False)
            for line in result.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device" and ":" in parts[0]:
                    devices.append(parts[0][:80])
        except (OSError, subprocess.SubprocessError):
            pass
    return {"adb_installed": bool(adb_path), "adb_devices": devices[:4]}


def _sentry_loop():
    """Holt die neueste Auslöse-Aufnahme des SurfMate- bzw. Overdrive-Wächters per adb vom USB-Stick im Auto.
    NUR aktiv, wenn im Assistenten angehakt UND eine adb-Adresse hinterlegt ist.
    Braucht: adb im System, kabelloses adb am Auto, Overdrive + USB-Stick. Das haben wenige."""
    import shutil, subprocess
    last = None
    while True:
        try:
            if not (_CFG.get("sentry") and _CFG.get("car_adb")):
                time.sleep(10)
                continue
            if not shutil.which("adb"):
                _STATE["sentry_err"] = ("adb ist auf diesem Rechner nicht installiert — "
                                        "ohne adb kann die Wächter-Kamera nicht ausgelesen werden.")
                time.sleep(120)
                continue
            try:
                subprocess.run(["adb", "connect", _CFG["car_adb"]], capture_output=True, timeout=15)
            except Exception:
                pass
            r = _adb(["shell", "ls -t %s 2>/dev/null | head -1" % SENT_GLOB], timeout=20)
            ev = r.stdout.decode(errors="ignore").strip()
            if not ev.endswith(".jpg"):
                _STATE["sentry_err"] = ("Auto per adb nicht erreichbar oder keine Aufnahmen gefunden "
                                        "(Adresse richtig? Auto wach? Stick drin?)")
                time.sleep(90)
                continue
            _STATE["sentry_err"] = ""
            if ev != last:
                tmp = str(CFG_DIR / "sentry.jpg")
                _adb(["pull", ev, tmp], timeout=90)
                if os.path.exists(tmp) and os.path.getsize(tmp) > 1000:
                    _STATE["sentry_img"] = True
                    _STATE["sentry_file"] = os.path.basename(ev)
                    # Zeitstempel steckt im Dateinamen: event_YYYYMMDD_HHMMSS.jpg
                    try:
                        b = os.path.basename(ev)[6:21]
                        _STATE["sentry_time"] = "%s.%s.%s %s:%s" % (b[6:8], b[4:6], b[0:4], b[9:11], b[11:13])
                    except Exception:
                        pass
                    last = ev
        except Exception as e:
            _STATE["sentry_err"] = str(e)[:120]
        time.sleep(int(_CFG.get("sentry_sec") or 60))


# ---------------------------------------------------------------- Strompreis (optional)
def _fetch_prices():
    """Holt die Boersenpreise fuer das im Assistenten gewaehlte Land.
    Rueckgabe: Liste [(unix_start, ct_pro_kWh)] — beide Quellen liefern EUR/MWh, /10 = ct/kWh."""
    import urllib.request
    src = PRICE_ZONES.get((_CFG.get("country_code") or "").upper())
    if not src:
        return None
    kind, arg = src
    if kind == "awattar":
        with urllib.request.urlopen(arg, timeout=12) as r:
            d = json.loads(r.read().decode())
        _STATE["price_src"] = "aWATTar"
        return [(int(x["start_timestamp"] / 1000), x["marketprice"] / 10.0) for x in d.get("data", [])]
    # energy-charts: ohne Datum kommt NUR der heutige Tag (abends bleiben dann 2-3 Balken uebrig).
    # Mit start/end holen wir heute + morgen (Day-ahead wird ~13 Uhr veroeffentlicht).
    heute = time.strftime("%Y-%m-%d")
    morgen = time.strftime("%Y-%m-%d", time.localtime(time.time() + 86400))
    url = "https://api.energy-charts.info/price?bzn=%s&start=%s&end=%s" % (arg, heute, morgen)
    with urllib.request.urlopen(url, timeout=12) as r:
        d = json.loads(r.read().decode())
    # CC BY 4.0 verlangt Namensnennung -> Quelle mitfuehren und im Cockpit anzeigen
    _STATE["price_src"] = "energy-charts.info"
    _STATE["price_lic"] = (d.get("license_info") or "")[:120]
    secs, pr = d.get("unix_seconds") or [], d.get("price") or []
    return [(int(s), p / 10.0) for s, p in zip(secs, pr) if p is not None]


def _price_loop():
    """Aktualisiert die Preise. Laeuft NUR, wenn der Nutzer es angehakt hat."""
    while True:
        try:
            if _CFG.get("show_price"):
                pts = _fetch_prices()
                if pts:
                    now = time.time()
                    # ACHTUNG: manche Zonen (NL/FR/PL/BE...) liefern VIERTELSTUNDEN-Werte (96/Tag),
                    # aWATTar/CH volle Stunden (24/Tag). Darum immer auf volle Stunden mitteln —
                    # sonst sieht ein Niederlaender nur 6 Stunden mit 4 gleichen Balken.
                    buckets = {}
                    for t, p in pts:
                        buckets.setdefault(int(t) - (int(t) % 3600), []).append(p)
                    hourly = sorted((h, sum(v) / len(v)) for h, v in buckets.items())
                    fut = [(t, p) for t, p in hourly if t + 3600 > now]
                    cur = next((p for t, p in hourly if t <= now < t + 3600), None)
                    horizon = fut[:24]
                    if horizon:
                        cheap = min(horizon, key=lambda x: x[1])
                        _STATE["price_now"] = round(cur, 2) if cur is not None else None
                        _STATE["price_cheap_ct"] = round(cheap[1], 2)
                        _STATE["price_cheap_time"] = time.strftime("%H:%M", time.localtime(cheap[0]))
                        _STATE["price_max_ct"] = round(max(p for _, p in horizon), 2)
                        _STATE["price_bars"] = [
                            {"h": time.strftime("%H", time.localtime(t)), "ct": round(p, 2),
                             "now": bool(t <= now < t + 3600), "cheap": bool(t == cheap[0])}
                            for t, p in horizon]
                        _STATE["price_zone"] = PRICE_ZONES.get((_CFG.get("country_code") or "").upper(), ("", ""))[1]
        except Exception:
            pass                              # Preis ist nie wichtig genug fuer eine Fehlermeldung
        time.sleep(1800)                      # Boersenpreise sind stuendlich, halbstuendlich pruefen reicht


# ---------------------------------------------------------------- Steuerung
def _busy(e):
    s = str(e)
    return "6024" in s or "1008" in s or "nicht abgeschlossen" in s


async def _climate(temp=None, off=False):
    """Exakt der Aufruf, der sich in der Praxis bewaehrt hat:
    params ist KEYWORD-only, verify_command_access will die VIN, command_pwd ueberall mit."""
    from pybyd import BydClient
    from pybyd.models import ClimateStartParams
    vin, pin = _CFG["vin"], _CFG["control_pin"]
    async with BydClient(byd_cfg()) as c:
        await c.login()
        tt = max(15.0, min(31.0, float(temp or 22.0)))
        last = None
        for i in range(2):      # BYD drosselt (1008) -> genau EINMAL sanft nachfassen, nie hammern
            try:
                await c.verify_command_access(vin, command_pwd=pin)
                if off:
                    await c.stop_climate(vin, command_pwd=pin)
                else:
                    await c.start_climate(vin, params=ClimateStartParams(temperature=tt, time_span=2),
                                          command_pwd=pin)
                return
            except Exception as e:
                last = e
                if _busy(e) and i < 1:
                    await asyncio.sleep(8)
                    continue
                raise
        raise last


async def _battery(on):
    """Batterie vorheizen an/aus. Aufruf 1:1 wie in der erprobten Bridge."""
    from pybyd import BydClient
    from pybyd.models import BatteryHeatParams
    vin, pin = _CFG["vin"], _CFG["control_pin"]
    async with BydClient(byd_cfg()) as c:
        await c.login()
        last = None
        for i in range(2):          # BYD drosselt -> genau EINMAL sanft nachfassen
            try:
                await c.verify_command_access(vin, command_pwd=pin)
                await c.set_battery_heat(vin, params=BatteryHeatParams(on=bool(on)), command_pwd=pin)
                return
            except Exception as e:
                last = e
                if _busy(e) and i < 1:
                    await asyncio.sleep(8)
                    continue
                raise
        raise last


# ---------------------------------------------------------------- Faehigkeiten des Fahrzeugs
# unser Knopf  ->  (Feld in get_vehicle_capabilities, Beschriftung, Standard angehakt?)
FEATURES = [
    ("klima",     "climate",                   "🌡️ Vorklimatisieren — Heizen, Kühlen, Aus", True),
    ("batt",      "battery_heat",              "🔋 Batterie vorheizen — im Winter vor dem Schnellladen", True),
    ("find",      "find_car",                  "🔍 Auto finden — Hupe und Blinken (Parkhaus!)", True),
    ("seat",      "driver_seat_heat",          "💺 Sitzheizung — Fahrer und Beifahrer", True),
    ("seatvent",  "driver_seat_ventilation",   "💨 Sitzbelüftung — Fahrer und Beifahrer", False),
    ("lock",      "lock",                      "🔒 Zusperren — falls du es mal vergessen hast", False),
]

# Sitz-Stufen laut BYD. 1 ist AUS, nicht AN — die Bibliothek gibt als Vorgabe 3 (=HOCH) vor!
SEAT_AUS, SEAT_NIEDRIG, SEAT_HOCH = 1, 2, 3


async def _fetch_caps(cfg_dict, vin):
    """Fragt das Auto, was es kann. Nur lesend."""
    from pybyd import BydClient, BydConfig
    conf = BydConfig(username=cfg_dict["username"], password=cfg_dict["password"],
                     control_pin=cfg_dict.get("control_pin", "000000"),
                     country_code=cfg_dict.get("country_code", "AT"),
                     language=cfg_dict.get("language", "de"),
                     time_zone=cfg_dict.get("time_zone", "Europe/Vienna"))
    async with BydClient(conf) as c:
        await c.login()
        cap = await c.get_vehicle_capabilities(vin)
        out = []
        for key, feld, text, standard in FEATURES:
            kann = bool(getattr(cap, feld, False))
            out.append({"key": key, "text": text, "kann": kann, "an": bool(kann and standard)})
        return out


async def _find_car():
    from pybyd import BydClient
    async with BydClient(byd_cfg()) as c:
        await c.login()
        vin, pin = _CFG["vin"], _CFG["control_pin"]
        await c.verify_command_access(vin, command_pwd=pin)
        await c.find_car(vin, command_pwd=pin)


async def _lock_car():
    """NUR zusperren. Aufsperren wird bewusst nirgends angeboten."""
    from pybyd import BydClient
    async with BydClient(byd_cfg()) as c:
        await c.login()
        vin, pin = _CFG["vin"], _CFG["control_pin"]
        await c.verify_command_access(vin, command_pwd=pin)
        await c.lock(vin, command_pwd=pin)


async def _seat(stufe, vent=False):
    """Sitzheizung/-belüftung für Fahrer UND Beifahrer. ALLE Werte explizit setzen —
    die Vorgaben der Bibliothek wären main_heat=3 (=HOCH) und würden die Sitze braten."""
    from pybyd import BydClient
    from pybyd.models import SeatClimateParams
    vin, pin = _CFG["vin"], _CFG["control_pin"]
    p = SeatClimateParams(
        main_heat=SEAT_AUS if vent else stufe,
        copilot_heat=SEAT_AUS if vent else stufe,
        main_ventilation=stufe if vent else SEAT_AUS,
        copilot_ventilation=stufe if vent else SEAT_AUS,
    )
    async with BydClient(byd_cfg()) as c:
        await c.login()
        last = None
        for i in range(2):
            try:
                await c.verify_command_access(vin, command_pwd=pin)
                await c.set_seat_climate(vin, params=p, command_pwd=pin)
                return
            except Exception as e:
                last = e
                if _busy(e) and i < 1:
                    await asyncio.sleep(8)
                    continue
                raise
        raise last


HEAT_TEMP = 26.0    # Zieltemperatur "Heizen"  (bewaehrt)
COOL_TEMP = 19.0    # Zieltemperatur "Kuehlen" (bewaehrt)


def _frischer_zustand():
    """Zustand direkt vor einem Cloud-Befehl: zuerst Panoptes im Auto (power_level), sonst die
    BYD-Cloud frisch abfragen. Nie den Cache nehmen - der kann Minuten alt sein."""
    if _CFG.get("panoptes") and _PANOPTES.get("obj") is not None:
        try:
            st = _PANOPTES["obj"].lies()
            if st and st.get("power_level") is not None:
                return {"t": time.time(), "power_level": st.get("power_level"),
                        "gear": st.get("gear"), "speed": st.get("speed")}
        except Exception:
            pass
    # Stiller Beweis: die letzte REGULAERE Cloud-Abfrage, wenn sie frisch genug ist (kein Zusatzauftrag).
    z = aus_letzter_abfrage(_STATE, time.time())
    if z:
        return z
    if _CFG.get("auth_blocked") or not _cloud_an():
        return None                    # kein (gueltiger) Cloud-Zugang -> Zustand unbekannt -> gesperrt
    # Sonst einmal frisch fragen - nur direkt vor einem Befehl, der das Auto ohnehin anspricht.
    try:
        from pybyd import BydClient

        async def _rt():
            async with BydClient(byd_cfg()) as c:
                await c.login()
                return await c.get_vehicle_realtime(_CFG["vin"])
        rt = asyncio.run(_rt())
        return {"t": time.time(), "vehicle_state": ev(getattr(rt, "vehicle_state", None)),
                "gear": {1: "P", 2: "R", 3: "N", 4: "D"}.get(ev(getattr(rt, "power_gear", None))),
                "speed": ev(getattr(rt, "speed", None))}
    except Exception:
        return None


def _run_cmd(action):
    """action: heat | cool | off. Laeuft im eigenen Thread und pausiert solange den Poller,
    weil BYD nur EINEN Vorgang gleichzeitig erlaubt (sonst 6024)."""
    labels = {"heat": "🔥 Heizen", "cool": "❄️ Kühlen", "off": "⏹️ Klima aus",
              "batt_on": "🔋 Batterie vorheizen", "batt_off": "🔋 Batterie-Heizung aus",
              "find": "🔍 Auto finden", "lock": "🔒 Zusperren",
              "seat_off": "💺 Sitzheizung aus", "seat_lo": "💺 Sitzheizung Stufe 1",
              "seat_hi": "💺 Sitzheizung Stufe 2",
              "vent_off": "💨 Belüftung aus", "vent_lo": "💨 Belüftung Stufe 1",
              "vent_hi": "💨 Belüftung Stufe 2"}

    def job():
        global _HOLD_UNTIL
        _HOLD_UNTIL = time.time() + 45
        _MSG.update({"text": "⏳ " + labels.get(action, "Befehl") + " wird gesendet …", "ts": time.time()})
        try:
            with _LOCK:
                # Sicherheitsregel (Vorfall 13.10.): Cloud-Befehle NUR bei sicher ausgeschaltetem Auto.
                ok, grund = befehl_erlaubt(_frischer_zustand(), time.time())
                if not ok:
                    _MSG.update({"text": "⛔ " + labels.get(action, "Befehl") + " nicht gesendet: " + grund +
                                 ". Fernbefehle gehen nur, wenn das Auto ausgeschaltet ist.", "ts": time.time()})
                    return
                if action in ("batt_on", "batt_off"):
                    asyncio.run(_battery(action == "batt_on"))
                elif action == "find":
                    asyncio.run(_find_car())
                elif action == "lock":
                    asyncio.run(_lock_car())
                elif action.startswith("seat_") or action.startswith("vent_"):
                    stufe = {"off": SEAT_AUS, "lo": SEAT_NIEDRIG, "hi": SEAT_HOCH}[action.split("_")[1]]
                    asyncio.run(_seat(stufe, vent=action.startswith("vent_")))
                elif action == "off":
                    asyncio.run(_climate(off=True))
                else:
                    asyncio.run(_climate(temp=HEAT_TEMP if action == "heat" else COOL_TEMP))
            _MSG.update({"text": "✅ " + labels.get(action, "Befehl") +
                         " angekommen — das Auto braucht ein paar Sekunden", "ts": time.time()})
        except Exception as e:
            msg = str(e)
            if "not confirmed" in msg or "asleep" in msg:
                # NICHT "das Auto schläft" behaupten — das ist pyBYDs generischer Timeout-Text,
                # keine Diagnose. In der Praxis kam es von zu schnellen Wiederholungen.
                msg = ("BYD hat den Befehl nicht bestätigt. Kurz warten und nochmal — "
                       "wenn es öfter passiert, bitte melden (das ist nicht normal).")
            elif _busy(e):
                msg = "BYD ist beschäftigt — läuft deine BYD-App mit DEMSELBEN Account? Dafür der Zweit-Account."
            _MSG.update({"text": "⚠️ " + msg[:150], "ts": time.time()})
        finally:
            _HOLD_UNTIL = 0

    threading.Thread(target=job, daemon=True).start()


# ---------------------------------------------------------------- Impressum / Haftung
# ---- Sprachschicht (DE Master, EN additiv). Siehe project_byd_copilot memory. ----
_I18N = json.loads(r'''{"BYD ist beschäftigt. Läuft deine BYD-App mit DEMSELBEN Account? Bitte einen zweiten Account als Zusatznutzer verwenden.": "BYD is busy. Is your BYD app running with the SAME account? Please use a second account as an additional user.", "Login abgelehnt — E-Mail, Passwort oder Land stimmen nicht (⚙︎ → neu einrichten).": "Login rejected — email, password or country are wrong (⚙︎ → set up again).", "BYD liefert für diese VIN gerade keine Daten (oft nur kurz — es versucht's weiter).": "BYD isn't returning any data for this VIN right now (often only briefly — it keeps trying).", "pybyd fehlt — bitte einmal installieren: pip install pybyd (%s)": "pybyd is missing — please install it once: pip install pybyd (%s)", "adb ist auf diesem Rechner nicht installiert — ohne adb kann die Wächter-Kamera nicht ausgelesen werden.": "adb is not installed on this computer — without adb the guardian camera can't be read out.", "Auto per adb nicht erreichbar oder keine Aufnahmen gefunden (Adresse richtig? Auto wach? Stick drin?)": "Car not reachable via adb or no recordings found (address correct? car awake? stick plugged in?)", "🔥 Heizen": "🔥 Heat", "❄️ Kühlen": "❄️ Cool", "⏹️ Klima aus": "⏹️ Climate off", "🔋 Batterie vorheizen": "🔋 Preheat battery", "🔋 Batterie-Heizung aus": "🔋 Battery heating off", "🔍 Auto finden": "🔍 Find car", "🔒 Zusperren": "🔒 Lock", "💺 Sitzheizung aus": "💺 Seat heating off", "💺 Sitzheizung Stufe 1": "💺 Seat heating level 1", "💺 Sitzheizung Stufe 2": "💺 Seat heating level 2", "💨 Belüftung aus": "💨 Ventilation off", "💨 Belüftung Stufe 1": "💨 Ventilation level 1", "💨 Belüftung Stufe 2": "💨 Ventilation level 2", "Befehl": "Command", "wird gesendet …": "is being sent …", "angekommen — das Auto braucht ein paar Sekunden": "arrived — the car needs a few seconds", "BYD hat den Befehl nicht bestätigt. Kurz warten und nochmal — wenn es öfter passiert, bitte melden (das ist nicht normal).": "BYD didn't confirm the command. Wait a moment and try again — if it happens more often, please report it (that's not normal).", "BYD ist beschäftigt — läuft deine BYD-App mit DEMSELBEN Account? Dafür der Zweit-Account.": "BYD is busy — is your BYD app running with the SAME account? That's what the second account is for.", "Deutlich zu wenig Druck (%.0f kPa statt %.0f) — bitte bald prüfen.": "Significantly too little pressure (%.0f kPa instead of %.0f) — please check soon.", "Etwas wenig Druck (%.0f kPa statt %.0f) — beim nächsten Tanken nachfüllen.": "A little low on pressure (%.0f kPa instead of %.0f) — top it up at your next stop.", "Reichlich viel Druck (%.0f kPa statt %.0f).": "Quite a lot of pressure (%.0f kPa instead of %.0f).", "Druck passt (%.0f–%.0f kPa).": "Pressure is fine (%.0f–%.0f kPa).", "Sensor meldet '%s' — liefert dein HA gerade Werte?": "Sensor reports '%s' — is your HA delivering values right now?", "Token abgelehnt — in HA neu erzeugen (Profil → Sicherheit).": "Token rejected — regenerate it in HA (Profile → Security).", "Sensor nicht gefunden — im Assistenten neu auswählen.": "Sensor not found — select it again in the wizard.", "Kilometerstand": "Odometer", "Ladezustand": "Charge level", "Echte Reichweite": "Real range", "Reichweite (BYD)": "Range (BYD)", "Verbrauch Schnitt": "Average consumption", "Ladeleistung": "Charging power", "Außentemperatur": "Outside temperature", "Reifen VL": "Tyre FL", "Reifen VR": "Tyre FR", "Reifen HL": "Tyre RL", "Reifen HR": "Tyre RR", "Gang": "Gear", "Verriegelt": "Locked", "Lädt": "Charging", "Angesteckt": "Plugged in", "Türen offen": "Doors open", "Fenster offen": "Windows open", "Klima läuft": "Climate running", "Batterie heizt": "Battery heating", "Standort": "Location", "Broker weist ab (Code %s) — Benutzer/Passwort?": "Broker refuses (code %s) — username/password?", "Keine Fahrzeuge gefunden — stimmen Login/Land?": "No vehicles found — are login/country correct?", "Login abgelehnt — E-Mail/Passwort/Land prüfen": "Login rejected — check email/password/country", "Token abgelehnt — stimmt er? (HA: Profil → Sicherheit → Token erstellen)": "Token rejected — is it correct? (HA: Profile → Security → Create token)", "Kein Kontakt zu Home Assistant — Adresse richtig? (z.B. http://192.168.0.10:8123)": "No contact with Home Assistant — is the address correct? (e.g. http://192.168.0.10:8123)", "Keine Verbindung — Adresse/Port richtig? Läuft der Broker (Mosquitto-Add-on)?": "No connection — are address/port correct? Is the broker running (Mosquitto add-on)?", "Broker weist ab — Benutzer/Passwort prüfen.": "Broker refuses — check username/password.", "VIN fehlt": "VIN missing", "EV-Cockpit laeuft:": "EV-Cockpit is running:", "Tablet/Handy im WLAN:": "Tablet/phone on Wi-Fi:", "Alle Daten bleiben auf DIESEM Rechner.": "All data stays on THIS computer.", "-> Der Browser oeffnet sich, der Assistent fuehrt dich durch.": "-> The browser opens, the wizard guides you through it.", "Beenden: dieses Fenster schliessen (oder Strg+C)": "To quit: close this window (or Ctrl+C)", "EV-Cockpit — Über & Rechtliches": "EV-Cockpit — About & Legal", "← zurück zum Cockpit": "← back to the cockpit", "Was das ist": "What this is", "Ein": "A", "freies Werkzeug für die BYD-Community": "free tool for the BYD community", ". Es zeigt dir die Daten deines eigenen Autos auf deinem eigenen Rechner — ohne Umweg über fremde Server. Gebaut aus Freude an der Sache und im Sinne des Rechts auf Reparatur. Kostenlos, für niemanden ein Geschäft.": ". It shows you your own car's data on your own computer — without a detour via someone else's servers. Built out of love for the thing and in the spirit of the right to repair. Free, a business for no one.", "Impressum": "Legal notice", "Salzburg, Österreich": "Salzburg, Austria", "E-Mail:": "Email:", "Vollständiges Impressum:": "Full legal notice:", "⚠️ Haftungsausschluss — bitte lesen": "⚠️ Disclaimer — please read", "Keine Verbindung zu BYD.": "No connection to BYD.", "Dies ist": "This is", "kein offizielles Produkt": "not an official product", "der BYD Auto Co. Ltd. und steht in keinerlei Verbindung zu BYD. „BYD\" ist eine Marke ihrer jeweiligen Inhaber und wird hier nur genannt, um die Kompatibilität zu beschreiben.": "of BYD Auto Co. Ltd. and has no connection to BYD whatsoever. \"BYD\" is a trademark of its respective owners and is named here only to describe compatibility.", "Nutzung auf eigene Gefahr.": "Use at your own risk.", "Diese Software wird kostenlos und": "This software is provided free of charge and", "ohne jede Gewähr": "without any warranty", "bereitgestellt — ohne Zusicherung von Funktion, Richtigkeit oder Verfügbarkeit. Sie": "— with no assurance of function, accuracy or availability. It", "steuert ein echtes Fahrzeug": "controls a real vehicle", "(z.B. die Klimaanlage). Für Schäden jeder Art, Datenverlust oder Folgen aus der Nutzung wird": "(e.g. the air conditioning).", "keine Haftung": "No liability", "übernommen, soweit gesetzlich zulässig.": "is accepted for damage of any kind, data loss or consequences of use, as far as legally permissible.", "BYDs Nutzungsbedingungen.": "BYD's terms of use.", "Der Zugriff auf die BYD-Cloud über eine fremde Anwendung kann den Nutzungsbedingungen von BYD widersprechen. Im ungünstigsten Fall kann BYD einen Account einschränken oder sperren.": "Accessing the BYD cloud through a third-party application may conflict with BYD's terms of use. In the worst case, BYD can restrict or block an account.", "Das entscheidest du selbst und trägst es selbst.": "You decide that yourself and carry it yourself.", "Zweiter Account.": "Second account.", "Die BYD-Cloud erlaubt pro Account nur eine aktive Sitzung. Nutze einen zweiten Account als Zusatznutzer — sonst stört dieses Werkzeug deine eigene BYD-App.": "The BYD cloud allows only one active session per account. Use a second account as an additional user — otherwise this tool disturbs your own BYD app.", "🔒 Datenschutz": "🔒 Privacy", "Deine Daten bleiben auf diesem Rechner.": "Your data stays on this computer.", "Zugangsdaten und Fahrzeugdaten werden ausschließlich lokal gespeichert (": "Access credentials and vehicle data are stored exclusively locally (", "). Die einzige Gegenstelle im Normalbetrieb ist die": "). The only remote endpoint in normal operation is the", "BYD-Cloud selbst": "BYD cloud itself", "— also der Dienst, dessen Daten du abrufst.": "— that is, the service whose data you're retrieving.", "Zwei freiwillige Ausnahmen": "Two voluntary exceptions", ", beide": ", both", "standardmäßig aus": "off by default", "und im Assistenten anhakbar:": "and checkable in the wizard:", "Strompreis": "Electricity price", "— dein Rechner fragt aWATTar bzw. energy-charts.info nach den Börsenpreisen deines Landes. Übertragen wird dabei nur die Anfrage selbst (die Gegenstelle sieht deine IP, wie bei jedem Webseitenbesuch) —": "— your computer asks aWATTar or energy-charts.info for your country's exchange prices. Only the request itself is transmitted (the remote endpoint sees your IP, as with any website visit) —", "keine Fahrzeugdaten": "no vehicle data", "Nutzungszählung": "Usage counting", "Nur wenn du sie im Assistenten aktiv anhakst, sendet das Programm einmal am Tag genau das hier:": "Only if you actively check it in the wizard does the program send exactly this once a day:", "{ \"id\": \"zufällige Installations-ID\", \"version\": \"__VERSION__\", \"model\": \"dein Automodell\" }": "{ \"id\": \"random installation ID\", \"version\": \"__VERSION__\", \"model\": \"your car model\" }", "Kein Name, keine E-Mail, keine VIN, kein Standort, keine Fahrdaten. Die ID ist eine Zufallszahl ohne Personenbezug. Häkchen jederzeit im Assistenten abschaltbar.": "No name, no email, no VIN, no location, no driving data. The ID is a random number with no personal reference. The checkbox can be switched off in the wizard at any time.", "Quelloffen": "Open source", "Du sollst uns nicht glauben müssen —": "You shouldn't have to take our word for it —", "schau nach": "check for yourself", ". Der gesamte Quelltext liegt offen; die Datei, die du gestartet hast, ist lesbarer Python-Code.": ". The entire source code is open; the file you started is readable Python code.", "EV-Cockpit — Einrichtung": "EV-Cockpit — Setup", "EV-Cockpit einrichten": "Set up EV-Cockpit", "Dein Auto, dein Rechner, deine Daten.": "Your car, your computer, your data.", "Wichtig": "Important", "BYD-Zugang": "BYD access", "Dein Auto": "Your car", "Aussehen": "Appearance", "⚠️ Bitte lies das hier — es ist der wichtigste Punkt": "⚠️ Please read this — it's the most important point", "Die BYD-Cloud erlaubt pro Konto nur": "The BYD cloud allows only", "eine": "one", "aktive Verbindung. Wenn du hier": "active connection per account. If you enter", "dasselbe Konto": "the same account", "einträgst wie in deiner BYD-App am Handy,": "here as in your BYD app on your phone,", "stören sich beide gegenseitig": "the two interfere with each other", "— mal spinnt das Cockpit, mal die App (Fehler 6024).": "— sometimes the cockpit acts up, sometimes the app (error 6024).", "So machst du es richtig:": "Here's how to do it right:", "In der BYD-App ein": "In the BYD app, create a", "zweites Konto": "second account", "anlegen (andere E-Mail-Adresse)": "(a different email address)", "Dieses zweite Konto im Auto als": "Grant this second account access in the car as an", "„Zusatznutzer\"": "\"additional user\"", "freigeben": "", "Hier gleich das": "Enter the", "zweite": "second", "Konto eintragen — nicht dein Haupt-Konto": "account here — not your main account", "Dann laufen App und Cockpit friedlich nebeneinander.": "Then the app and cockpit run peacefully side by side.", "Zugangsdaten und Fahrzeugdaten werden nur lokal gespeichert. Dieses Programm sendet": "Access credentials and vehicle data are stored only locally. This program sends", "nichts": "nothing", "an den Entwickler — es spricht nur mit der BYD-Cloud selbst. Nachlesbar: die Datei": "to the developer — it talks only to the BYD cloud itself. You can check: the file", "ist normaler, lesbarer Text.": "is normal, readable text.", "Verstanden — ich verwende ein zweites BYD-Konto": "Understood — I'm using a second BYD account", "Oder: mir ist bewusst, dass es sonst mit meiner BYD-App kollidieren kann.": "Or: I'm aware that it can otherwise collide with my BYD app.", "Weiter →": "Next →", "E-Mail deines BYD-Kontos": "Email of your BYD account", "(das zweite!)": "(the second one!)", "Passwort": "Password", "Steuer-PIN (6-stellig — dieselbe wie in der BYD-App)": "Control PIN (6 digits — the same as in the BYD app)", "z.B. 123456": "e.g. 123456", "Land": "Country", "Zeitzone": "Time zone", "🔍 Meine Fahrzeuge abrufen": "🔍 Fetch my vehicles", "Beim Abrufen meldet sich dein Rechner einmal bei BYD an — so wie deine Handy-App auch. Klappt es nicht, stimmt meistens das": "When fetching, your computer logs in to BYD once — just like your phone app does. If it doesn't work, it's usually the", "nicht.": "that's wrong.", "← Zurück": "← Back", "Dein Fahrzeug": "Your vehicle", "— erst Fahrzeuge abrufen —": "— fetch vehicles first —", "Modell (setzt die Akkugröße)": "Model (sets the battery size)", "Akku nutzbar in kWh —": "Usable battery in kWh —", "bitte prüfen": "please check", "Reifendruck-Sollwert (kPa, optional)": "Tyre pressure target (kPa, optional)", "z.B. 250": "e.g. 250", "🔎 Was kann mein Auto?": "🔎 What can my car do?", "Dein Auto hat uns gesagt, was es kann.": "Your car told us what it can do.", "Hak an, was du im Cockpit haben willst": "Check what you want in the cockpit", "— den Rest siehst du gar nicht erst.": "— you won't even see the rest.", "Ausgegraute Zeilen kann dein Auto nicht — die liegen nicht an uns.": "Greyed-out rows are things your car can't do — that's not on us.", "Aufsperren bieten wir bewusst nicht an": "We deliberately don't offer unlocking", ", auch wenn dein Auto es könnte: Ein Knopf im Browser, der dein Auto öffnet, wäre ein Einbruchswerkzeug für jeden, der an deinen Rechner kommt. Zusperren ist dagegen harmlos.": ", even if your car could do it: a button in the browser that opens your car would be a burglary tool for anyone who gets to your computer. Locking, on the other hand, is harmless.", "Der": "The", "Reifendruck-Sollwert": "tyre pressure target", "steht bei dir im": "is in your", "Türrahmen der Fahrertür": "driver's door frame", "(oft in bar: 2,5 bar = 250 kPa). Trägst du ihn ein, warnt dich das Cockpit bei zu wenig Druck. Lässt du das Feld leer, zeigt es den Druck nur an —": "(often in bar: 2.5 bar = 250 kPa). If you enter it, the cockpit warns you when pressure is too low. If you leave the field empty, it only shows the pressure —", "ich rate den Wert bewusst nicht": "I deliberately don't guess the value", ", er hängt an deiner Reifengröße und Beladung.": ", it depends on your tyre size and load.", "Diese Zahl braucht nur die": "This number is only needed for the", "ehrliche Reichweiten-Rechnung": "honest range calculation", ". Steht in deinen Fahrzeugpapieren oder im Prospekt. Stimmt sie nicht genau, ist das halb so wild — die Reichweite wird dann nur etwas ungenauer.": ". It's in your vehicle documents or the brochure. If it's not exactly right, no big deal — the range just gets a bit less accurate.", "Foto deines Autos (optional)": "Photo of your car (optional)", "Am schönsten ist ein Foto von": "A photo of", "deinem eigenen": "your own", "Auto — freigestellt vor hellem Hintergrund wirkt es am besten. Bleibt natürlich auch nur auf diesem Rechner. Kannst du auch später noch nachreichen.": "car looks nicest — cut out against a light background works best. It stays on this computer too, of course. You can also add it later.", "Wie oft soll beim Auto nachgefragt werden?": "How often should the car be polled?", "alle 2 Minuten — sehr frisch, viele Abfragen": "every 2 minutes — very fresh, many requests", "alle 5 Minuten — empfohlen": "every 5 minutes — recommended", "alle 10 Minuten — sparsam": "every 10 minutes — economical", "alle 15 Minuten": "every 15 minutes", "alle 30 Minuten — sehr sparsam": "every 30 minutes — very economical", "🔔 Bescheid geben, wenn das Laden fertig ist": "🔔 Notify me when charging is finished", "Im Cockpit gibt es oben rechts eine": "In the cockpit there's a", "Glocke": "bell", "— einmal draufklicken, dann meldet dir dein Browser, wenn das Auto fertig geladen hat (und wenn es plötzlich offen ist).": "at the top right — click it once, then your browser notifies you when the car has finished charging (and when it's suddenly open).", "Nichts zu konfigurieren:": "Nothing to configure:", "Die Meldung entsteht": "The notification is created", "in deinem Browser": "in your browser", "— kein Telegram, kein Konto, es verlässt nichts deinen Rechner.": "— no Telegram, no account, nothing leaves your computer.", "Ehrliche Grenze:": "Honest limitation:", "Es meldet nur, solange die Cockpit-Seite offen ist (ein Hintergrund-Tab reicht). Browser zu = keine Meldung.": "It only notifies while the cockpit page is open (a background tab is enough). Browser closed = no notification.", "Gilt, solange das Auto": "Applies as long as the car is", "aktiv": "active", "ist. Steht es länger, fragt das Cockpit nur alle 15 Minuten — das schont die 12V-Batterie. Während der Fahrt fragt es automatisch öfter.": ". If it stands for longer, the cockpit only polls every 15 minutes — that spares the 12V battery. While driving it automatically polls more often.", "Fürs Vorklimatisieren spielt das keine Rolle": "For preconditioning this doesn't matter", "— das geht jederzeit, auch beim geparkten Auto.": "— that works anytime, even with the car parked.", "Alles hier ist freiwillig.": "Everything here is optional.", "Lass ruhig alles aus — das Cockpit funktioniert komplett ohne. Du kannst jederzeit zurückkommen und etwas dazuschalten.": "Feel free to leave everything off — the cockpit works completely without it. You can come back anytime and switch something on.", "💶 Strompreis anzeigen — „wann ist Laden am billigsten?\"": "💶 Show electricity price — \"when is charging cheapest?\"", "Zeigt den": "Shows your country's", "Börsen-Strompreis": "exchange electricity price", "deines Landes als Stundenbalken mit der günstigsten Stunde. Quelle: aWATTar (AT/DE) bzw. energy-charts.info (Fraunhofer ISE), kostenlos, ohne Konto.": "as hourly bars with the cheapest hour. Source: aWATTar (AT/DE) or energy-charts.info (Fraunhofer ISE), free, no account.", "Ehrlich:": "Honestly:", "Das ist der": "This is the", "Börsenpreis": "exchange price", "nicht": "not", "was auf deiner Rechnung steht (Netz, Steuern, Aufschläge fehlen). Nur mit einem": "what's on your bill (grid fees, taxes, surcharges are missing). Only with an", "Börsentarif": "exchange tariff", "(Tibber, aWATTar, smartENERGY) ist das dein echter Verlauf. Bei Fixtarif bloß interessant.": "(Tibber, aWATTar, smartENERGY) is this your real curve. With a fixed tariff it's just interesting.", "Dein Rechner fragt dann diese Preisseite ab (die sieht deine IP, wie bei jedem Webseitenbesuch) —": "Your computer then queries this price page (which sees your IP, as with any website visit) —", "🔌 Ladesäulen in der Nähe anzeigen": "🔌 Show charging stations nearby", "Öffentliche Ladestationen rund um den": "Public charging stations around your", "aktuellen Standort deines Autos": "car's current location", "— Betreiber, Entfernung, Steckertyp. Quelle:": "— operator, distance, connector type. Source:", ", kein Konto.": ", no account.", "Ehrlich: keine Preise.": "Honestly: no prices.", "Es gibt keine verlässliche freie Quelle für aktuelle Ladepreise — falsche Preise wären schlimmer als gar keine. Auch die Standorte pflegen Freiwillige: meist gut, aber ohne Gewähr. E-Bike-Ladepunkte filtern wir raus.": "There's no reliable free source for current charging prices — wrong prices would be worse than none. The locations are also maintained by volunteers: usually good, but without guarantee. We filter out e-bike charging points.", "📱 Auch auf Tablet/Handy im Heimnetz öffnen": "📱 Also open on tablet/phone in the home network", "Ohne Haken ist das Cockpit": "Without the checkmark, the cockpit is reachable", "nur auf diesem Rechner": "only on this computer", "erreichbar — die sicherste Einstellung. Mit Haken erreichst du es auch vom Küchen-Tablet im eigenen WLAN; die Adresse zeigt dir das Cockpit dann unten an. Nur im eigenen, vertrauenswürdigen Netz aktivieren: das Cockpit kann die Klimaanlage deines Autos steuern.": "— the safest setting. With the checkmark you can also reach it from the kitchen tablet on your own Wi-Fi; the cockpit then shows you the address below. Only enable it on your own, trusted network: the cockpit can control your car's air conditioning.", "🏠 Ans Home Assistant senden": "🏠 Send to Home Assistant", "Du nutzt": "Using", "? Dann schickt das Cockpit dein Auto dorthin — es taucht": "? Then the cockpit sends your car there — it", "von selbst auf": "shows up on its own", ", mit allen Werten und den Klima-Knöpfen. Kein YAML, nichts konfigurieren. Praktisch, wenn du dort schon deine PV-Anlage oder Wallbox hast: dann siehst du alles auf einem Bild.": ", with all values and the climate buttons. No YAML, nothing to configure. Handy if you already have your PV system or wallbox there: then you see everything in one picture.", "Voraussetzung:": "Requirement:", "ein MQTT-Broker (bei HA meist das": "an MQTT broker (with HA usually the", "-Add-on, einmal installieren).": "add-on, install it once).", "Tipp:": "Tip:", "Am besten läuft dieses Programm dann auf dem Gerät, auf dem auch HA läuft (Raspberry, NAS, Mini-PC) — dann hat HA rund um die Uhr Daten. Dafür gibt es das Linux-Paket und eine Autostart-Anleitung in der LIESMICH.": "It's best to run this program on the device that also runs HA (Raspberry, NAS, mini PC) — then HA has data around the clock. There's a Linux package and an autostart guide for that in the README.", "MQTT-Broker (Adresse)": "MQTT broker (address)", "z.B. 192.168.0.10": "e.g. 192.168.0.10", "Benutzer (falls nötig)": "User (if needed)", "leer lassen wenn keiner": "leave empty if none", "leer lassen wenn keins": "leave empty if none", "🔌 Verbindung testen": "🔌 Test connection", "☀️ PV-Leistung aus Home Assistant holen": "☀️ Get PV power from Home Assistant", "Du hast eine": "You have a", "PV-Anlage": "PV system", "und sie ist in Home Assistant eingebunden? Dann zeigt das Cockpit deine": "and it's integrated into Home Assistant? Then the cockpit shows your", "aktuelle Solar-Leistung": "current solar power", "direkt neben Ladestand und Strompreis — du siehst auf einen Blick, ob du gerade": "right next to the charge level and electricity price — you see at a glance whether you're charging", "mit eigener Sonne": "with your own sun", "lädst oder teuer aus dem Netz.": "right now or expensively from the grid.", "Warum das so gut geht:": "Why this works so well:", "Wir reden nicht mit deinem Wechselrichter —": "We don't talk to your inverter —", "Home Assistant hat das schon erledigt": "Home Assistant has already done that", ". Egal ob Fronius, SMA, Huawei, SolarEdge oder Kostal: in HA ist es einfach ein Sensor mit einem Wert in Watt. Den holen wir uns, sonst nichts.": ". Whether Fronius, SMA, Huawei, SolarEdge or Kostal: in HA it's simply a sensor with a value in watts. That's what we fetch, nothing else.", "Wir zeigen, was": "We show what", "dein HA": "your HA", "sagt. Stimmt der Wert dort nicht, stimmt er hier auch nicht. Es wird": "says. If the value is wrong there, it's wrong here too. It's", "nur gelesen": "read only", "— wir schreiben nie etwas in dein HA.": "— we never write anything to your HA.", "Adresse deines Home Assistant": "Address of your Home Assistant", "z.B. http://192.168.0.10:8123": "e.g. http://192.168.0.10:8123", "Zugriffs-Token": "Access token", "(in HA: unten links auf deinen Namen → Sicherheit → ganz unten „Long-Lived Access Token\" → Token erstellen)": "(in HA: bottom left on your name → Security → at the very bottom \"Long-Lived Access Token\" → create token)", "den langen Text hier einfügen": "paste the long text here", "🔍 Meine Sensoren laden": "🔍 Load my sensors", "Welcher Sensor ist deine PV-Leistung?": "Which sensor is your PV power?", "Meist heißt er „PV Leistung\", „Solar Power\" o.ä. Nimm den, der die": "It's usually called \"PV Leistung\", \"Solar Power\" or similar. Take the one that shows the", "aktuelle Erzeugung in Watt": "current generation in watts", "zeigt.": ".", "🎥 Wächter-Kamera einbinden": "🎥 Integrate guardian camera", "— nur für Bastler": "— for tinkerers only", "Zeigt die letzte": "Shows the latest", "Auslöse-Aufnahme": "triggered recording", "der 360°-Kameras.": "from the 360° cameras.", "Braucht alles davon:": "Needs all of this:", "auf diesem Rechner (ist": "on this computer (is", "im Paket dabei),": "included in the package),", "kabelloses adb am Auto": "wireless adb on the car", "freigeschaltet,": "enabled,", "Overdrive-App": "Overdrive app", "USB-Stick": "USB stick", "im Auto.": "in the car.", "Sagt dir das nichts?": "Doesn't ring a bell?", "Haken weglassen": "Leave the checkmark off", "— alles andere geht trotzdem.": "— everything else still works.", "adb-Adresse des Autos (z.B. 192.168.0.50:5555)": "adb address of the car (e.g. 192.168.0.50:5555)", "🔔 Auf neue Versionen hinweisen": "🔔 Notify about new versions", "Das Cockpit schaut dann": "The cockpit then checks", "einmal am Tag": "once a day", "nach, ob es eine neuere Version gibt, und zeigt dir oben einen kleinen Hinweis. Nützlich für Fehlerbehebungen — du musst sonst selbst mitbekommen, wenn etwas repariert wurde.": "whether there's a newer version and shows you a small note at the top. Useful for bug fixes — otherwise you'd have to notice yourself when something was repaired.", "Wie das ohne Datenabfluss geht:": "How this works without data leaving:", "Dein Rechner lädt nur eine kleine Textdatei mit der neuesten Versionsnummer und": "Your computer only downloads a small text file with the latest version number and", "vergleicht sie selbst": "compares it itself", ". Der Server erfährt dabei": ". The server doesn't even", "nicht einmal, welche Version du hast": "learn which version you have", "— es wird nichts über dich gesendet, kein Ident, kein Modell, keine Fahrzeugdaten.": "— nothing about you is sent, no ident, no model, no vehicle data.", "Beim Abholen sieht der Server – wie bei jedem Webseitenbesuch – deine IP. Wir schreiben sie nirgends auf. Ohne Haken passiert gar nichts.": "When fetching, the server sees – as with any website visit – your IP. We don't record it anywhere. Without the checkmark, nothing happens at all.", "📊 Anonym mitzählen, dass ich das Tool nutze": "📊 Anonymously count that I use the tool", "Damit der Entwickler sieht, ob sich die Arbeit lohnt.": "So the developer can see whether the work is worth it.", "Einmal am Tag wird genau das gesendet — und sonst nichts:": "Once a day exactly this is sent — and nothing else:", "{ \"id\": \"zufällige Nummer\", \"version\": \"1.0\", \"model\": \"dein Modell\" }": "{ \"id\": \"random number\", \"version\": \"1.0\", \"model\": \"your model\" }", "Kein Name, keine E-Mail, keine VIN, kein Standort, keine Fahrdaten. Ohne Haken sendet das Programm": "No name, no email, no VIN, no location, no driving data. Without the checkmark, the program sends", "gar nichts": "nothing at all", "an den Entwickler.": "to the developer.", "✅ Fertig — Cockpit starten": "✅ Done — start cockpit", "ABMELDEN": "LOG OUT", "Löscht deine BYD-Zugangsdaten, die gespeicherten Fahrzeugdaten und dein Foto": "Deletes your BYD access credentials, the stored vehicle data and your photo", "von diesem Rechner": "from this computer", ". Dein BYD-Konto selbst bleibt unangetastet.": ". Your BYD account itself remains untouched.", "🚪 Abmelden & Daten löschen": "🚪 Log out & delete data", "Impressum · Haftungsausschluss · Datenschutz": "Legal notice · Disclaimer · Privacy", "Bevor es losgeht": "Before we start", "Ein Punkt ist wirklich wichtig — bitte kurz lesen.": "One point is really important — please read it briefly.", "Dein BYD-Zugang": "Your BYD access", "Damit holt dein Rechner die Daten direkt von BYD.": "With this, your computer fetches the data directly from BYD.", "Welches Fahrzeug, und wie groß ist der Akku?": "Which vehicle, and how big is the battery?", "Dein Cockpit": "Your cockpit", "Ein Foto und wie oft nachgefragt wird.": "A photo and how often it's polled.", "Alles freiwillig — lass ruhig alles aus.": "All optional — feel free to leave everything off.", "⚠️ Bitte zuerst „Meine Fahrzeuge abrufen\" drücken.": "⚠️ Please press \"Fetch my vehicles\" first.", "ℹ️ Deine Auswahl ist gespeichert. Erneut abfragen, um sie zu ändern.": "ℹ️ Your selection is saved. Query again to change it.", "(gespeichert)": "(saved)", "••••••• (gespeichert — leer lassen zum Behalten)": "••••••• (saved — leave empty to keep)", "Aktuelles Foto — neues wählen zum Ersetzen": "Current photo — choose a new one to replace it", "ℹ️ Deine Einstellungen sind vorausgefüllt. Ändere, was du willst, und speichere.": "ℹ️ Your settings are pre-filled. Change what you want and save.", "Wirklich abmelden? Zugangsdaten, Fahrzeugdaten und Foto werden von diesem Rechner gelöscht.": "Really log out? Access credentials, vehicle data and photo will be deleted from this computer.", "⏳ Lösche …": "⏳ Deleting …", "✅ Abgemeldet. Alles gelöscht.": "✅ Logged out. Everything deleted.", "⚠️ Bitte zuerst in Schritt 2 die Fahrzeuge abrufen.": "⚠️ Please fetch the vehicles in step 2 first.", "⏳ Frage dein Auto …": "⏳ Asking your car …", "Dein Auto kann das nicht.": "Your car can't do that.", "✅ Dein Auto kann": "✅ Your car can", "von": "of", "Dingen.": "things.", "⚠️ Bitte Adresse und Token eintragen.": "⚠️ Please enter address and token.", "⏳ Frage dein Home Assistant …": "⏳ Asking your Home Assistant …", "Leistungs-Sensoren gefunden — wähl deinen PV-Sensor aus.": "power sensors found — choose your PV sensor.", "⚠️ Bitte zuerst die Broker-Adresse eintragen.": "⚠️ Please enter the broker address first.", "⏳ Verbinde …": "⏳ Connecting …", "✅ Broker erreicht — dein Auto erscheint gleich in Home Assistant.": "✅ Broker reached — your car will appear in Home Assistant shortly.", "⏳ Melde mich bei BYD an …": "⏳ Logging in to BYD …", "Fahrzeug(e) gefunden — weiter unten mit Weiter": "vehicle(s) found — continue below with Next", "⚠️ Fehler:": "⚠️ Error:", "⚠️ Bitte erst Fahrzeuge abrufen und eins auswählen": "⚠️ Please fetch vehicles first and select one", "⏳ Speichere …": "⏳ Saving …", "✅ Gespeichert — Cockpit startet …": "✅ Saved — cockpit is starting …", "Für den Tablet-Zugriff das Programm einmal neu starten.": "For tablet access, restart the program once.", "ist da.": "is here.", "Ansehen →": "View →", "Benachrichtigen, wenn das Laden fertig ist": "Notify when charging is finished", "AKKU": "BATTERY", "REICHWEITE (ECHT)": "RANGE (REAL)", "BYD sagt:": "BYD says:", "Kein Foto hinterlegt": "No photo set", "⚙︎ → Foto-URL": "⚙︎ → Photo URL", "KILOMETERSTAND": "ODOMETER", "AUSSEN": "OUTSIDE", "VERBRAUCH Ø": "CONSUMPTION Ø", "REIFEN": "TYRES", "DEINE PV-ANLAGE": "YOUR PV SYSTEM", "ERZEUGT GERADE": "GENERATING NOW", "Quelle: dein Home Assistant": "Source: your Home Assistant", "KLIMA": "CLIMATE", "🔥  Heizen": "🔥  Heat", "❄  Kühlen": "❄  Cool", "◼  Aus": "◼  Off", "🔋  Batterie vorheizen": "🔋  Preheat battery", "🔍  Auto finden": "🔍  Find car", "🔒  Zusperren": "🔒  Lock", "SITZE (FAHRER + BEIFAHRER)": "SEATS (DRIVER + PASSENGER)", "💺  Aus": "💺  Off", "💺  Stufe 1": "💺  Level 1", "💺  Stufe 2": "💺  Level 2", "💨  Belüftung aus": "💨  Ventilation off", "💨  Stufe 1": "💨  Level 1", "💨  Stufe 2": "💨  Level 2", "Heizen zielt auf 26 °C, Kühlen auf 19 °C.": "Heating targets 26 °C, cooling 19 °C.", "Batterie vorheizen": "Preheating the battery", "hilft im Winter vor dem Schnellladen — eine warme Batterie lädt deutlich schneller. Das geht auch bei geparktem Auto.": "helps in winter before fast charging — a warm battery charges much faster. This also works with the car parked.", "LADEN": "CHARGING", "LEISTUNG": "POWER", "FERTIG IN": "DONE IN", "laut Auto": "per the car", "STROM GERADE": "ELECTRICITY NOW", "Börse, ohne Netz & Steuern": "Exchange, without grid & taxes", "Türen": "Doors", "Fenster": "Windows", "STROMPREIS (BÖRSE)": "ELECTRICITY PRICE (EXCHANGE)", "JETZT": "NOW", "GÜNSTIGSTE STUNDE": "CHEAPEST HOUR", "um": "at", "Uhr": "", "TEUERSTE": "MOST EXPENSIVE", "Börsenpreis ohne Netz & Steuern — dein Rechnungspreis nur bei einem Börsentarif.": "Exchange price without grid & taxes — your bill price only with an exchange tariff.", "Quelle:": "Source:", "WÄCHTER-KAMERA": "GUARDIAN CAMERA", "LETZTE AUFNAHME": "LAST RECORDING", "Wächter-Aufnahme": "Guardian recording", "LADESÄULEN IN DER NÄHE": "CHARGING STATIONS NEARBY", "Daten: © OpenStreetMap-Mitwirkende (ODbL) · von Freiwilligen gepflegt, ohne Gewähr ·": "Data: © OpenStreetMap contributors (ODbL) · maintained by volunteers, without guarantee ·", "bewusst ohne Preisangaben": "deliberately without price information", "STANDORT": "LOCATION", "🔵 dein Auto · 🟢 Ladesäulen (anklickbar) — Karte © OpenStreetMap-Mitwirkende": "🔵 your car · 🟢 charging stations (clickable) — map © OpenStreetMap contributors", "📱 Auf Tablet/Handy im selben WLAN erreichbar unter": "📱 Reachable on tablet/phone on the same Wi-Fi at", "📷 Eigenes Foto deines Autos einsetzen": "📷 Use your own car's photo", "km entfernt": "km away", "Meldet, wenn das Laden fertig ist (nur solange diese Seite offen ist)": "Notifies when charging is finished (only while this page is open)", "Dein Browser kann keine Benachrichtigungen.": "Your browser can't do notifications.", "Benachrichtigungen an": "Notifications on", "Du bekommst Bescheid, wenn das Laden fertig ist.": "You'll be notified when charging is finished.", "Dein Browser hat Benachrichtigungen für diese Seite blockiert. Du kannst das im Schloss-Symbol neben der Adresse wieder erlauben.": "Your browser has blocked notifications for this page. You can allow it again via the lock icon next to the address.", "🔌 Laden beendet": "🔌 Charging finished", "Dein Auto ist bei": "Your car is at", "% — Kabel kann raus.": "% — you can unplug the cable.", "🔓 Auto ist offen": "🔓 Car is open", "Es war eben noch verriegelt.": "It was locked just a moment ago.", "SCHLÄFT": "SLEEPING", "Ja": "Yes", "Nein": "No", "zu": "closed", "OFFEN": "OPEN", "angesteckt, lädt nicht": "plugged in, not charging", "lädt": "charging", "Schnellladen": "Fast charging", "Wallbox-Tempo": "Wallbox speed", "langsam (Steckdose?)": "slow (household socket?)", "Uhr:": "h:", "⏳ Sende …": "⏳ Sending …", "⚠️ Dienst weg": "⚠️ Service gone", "Auto wirklich zusperren?": "Really lock the car?", "Projekt & Kontakt": "Project & contact", "Freies, nicht-kommerzielles Community-Projekt, quelloffen auf GitHub:": "Free, non-commercial community project, open source on GitHub:", "Fragen oder Fehler? Bitte als Issue melden:": "Questions or bugs? Please report as an issue:", "— Nur wenn du sie im Assistenten aktiv anhakst, sendet das Programm einmal am Tag genau das hier:": "— Only if you actively check it in the wizard does the program send exactly this once a day:", "zufällige Installations-ID": "random installation ID", "dein Automodell": "your car model", "🗺️ Mit dem Routenplaner der BYD-Community verbinden": "🗺️ Connect to the BYD community route planner", "Dein persönlicher Planer auf byd.serveone.at/ev kennt dann den Ladestand deines Autos und plant die Ladestopps damit. Gesendet wird nur der letzte Ladestand, kein Ort. Den persönlichen Link bekommen Mitglieder der BYD-Karte (byd.serveone.at) per E-Mail.": "Your personal planner on byd.serveone.at/ev then knows your car's state of charge and plans charging stops with it. Only the latest charge level is sent, no location. Members of the BYD map (byd.serveone.at) receive the personal link by e-mail.", "Dein persönlicher Planer-Link": "Your personal planner link", "🚗 Fahrzeuge aus dem Planer laden": "🚗 Load vehicles from the planner", "Fahrzeug im Planer": "Vehicle in the planner", "– erst Fahrzeuge laden –": "– load vehicles first –", "🗺️ Karte im Community-Look": "🗺️ Community map style", "Dieselbe Karte wie im Planer und in der Panoptes-App, vom Server der BYD-Community (byd.serveone.at). Ohne Haken: OpenStreetMap.": "The same map as in the planner and the Panoptes app, served by the BYD community server (byd.serveone.at). Unticked: OpenStreetMap.", "ROUTENPLANER": "ROUTE PLANNER", "🗺️ Route planen": "🗺️ Plan a route", "⏳ Frage den Planer …": "⏳ Asking the planner …", "Fahrzeuge gefunden — passendes ist vorausgewählt.": " vehicles found — the matching one is preselected.", "Ladestand an den Planer gemeldet:": "Charge level sent to planner: ", "vor": "", "Verbunden. Der Ladestand wird gemeldet, sobald das Auto wach ist.": "Connected. The charge level is sent as soon as the car is awake.", "Panoptes- (früher SurfMate) oder Overdrive-App, USB-Stick und kabelloses ADB müssen im Auto bereits eingerichtet sein.": "Panoptes (formerly SurfMate) or Overdrive app, USB stick and wireless ADB must already be set up in the car.", "📡 Daten direkt von Panoptes im Auto": "📡 Data directly from Panoptes in the car", "Läuft die Panoptes-App in deinem Auto, holt das Cockpit Ladestand, Kilometer und Standort direkt von dort — schneller, und die BYD-Cloud wird geschont. Ist das Auto aus oder nicht erreichbar, fragt das Cockpit wie bisher die BYD-Cloud. Steuern (Klima, Schloss) läuft weiter über die BYD-Cloud.": "If the Panoptes app runs in your car, the cockpit reads charge level, mileage and location directly from it — faster, and it spares the BYD cloud. If the car is off or unreachable, the cockpit asks the BYD cloud as before. Controls (climate, lock) still go through the BYD cloud.", "Adresse des Autos (Heimnetz oder Tailscale)": "Car address (home network or Tailscale)", "Kopplungs-Code aus der Panoptes-App": "Pairing code from the Panoptes app", "🔌 Verbindung prüfen": "🔌 Test connection", "⏳ Frage das Auto …": "⏳ Asking the car …", "Verbunden — Ladestand": "Connected — charge level ", "Echten Verbrauch lernen": "Learn real consumption", "Deine Fahrten bleiben auf diesem Rechner. Nach jeder Fahrt ohne Laden vergleicht das Cockpit deinen Verbrauch mit dem Planer-Modell und schickt nur eine einzige Zahl (deinen Korrekturfaktor). Keine Fahrten, keine Orte, keine Uhrzeit. Hast du Panoptes im Auto gekoppelt, macht das Panoptes.": "Your trips stay on this computer. After each trip without charging, the cockpit compares your consumption with the planner's model and sends only a single number (your correction factor). No trips, no places, no times. If Panoptes is paired in your car, Panoptes does this.", "Panoptes im Auto meldet Ladestand und Verbrauch selbst.": "Panoptes in the car reports charge level and consumption itself.", "Verbrauch aus": "Consumption learned from", "Fahrt(en) gelernt, Faktor": "trip(s), factor", "TEIL VON PANOPTES": "PART OF PANOPTES", "Fragt schon ein anderes Programm mit diesem Konto bei BYD nach (z. B. Home Assistant), braucht das Cockpit ebenfalls ein eigenes Konto. Hast du Panoptes im Auto, kannst du es stattdessen damit koppeln.": "If another program already queries BYD with this account (e.g. Home Assistant), the cockpit needs its own account too. If you have Panoptes in your car, you can pair with it instead.", "🛡️ Aus Sicherheitsgründen nur bei ausgeschaltetem Auto.": "🛡️ For safety, only when the car is switched off.", "Woher soll das Cockpit die Daten deines Autos holen?": "Where should the cockpit get your car's data from?", "🌐 Über ein BYD-Konto": "🌐 Via a BYD account", "Für die meisten am einfachsten. Das Cockpit fragt die BYD-Cloud, mit einem eigenen zweiten Konto.": "Easiest for most people. The cockpit asks the BYD cloud, using a separate second account.", "🏠 Aus Home Assistant": "🏠 From Home Assistant", "Dein Auto ist schon in Home Assistant (BYD-Integration, Panoptes oder anderes). Das Cockpit liest nur.": "Your car is already in Home Assistant (BYD integration, Panoptes or something else). The cockpit only reads.", "📡 Von Panoptes im Auto": "📡 From Panoptes in the car", "Die Panoptes-App läuft auf deinem Infotainment. Am schnellsten, ganz ohne Cloud.": "The Panoptes app runs on your infotainment system. Fastest, no cloud at all.", "(in Home Assistant: unten links auf deinen Namen → Sicherheit → ganz unten „Langlebiges Zugriffstoken“ → erstellen)": "(in Home Assistant: bottom left click your name → Security → at the bottom “Long-lived access token” → create)", "🔍 Mein Auto in Home Assistant suchen": "🔍 Find my car in Home Assistant", "BYD-Konto": "BYD account", "Optional: BYD-Konto für Fernbefehle (Klima, Zusperren)": "Optional: BYD account for remote commands (climate, locking)", "Datenquelle": "Data source", "Deine Datenquelle": "Your data source", "Woher kommen die Werte deines Autos?": "Where do your car's values come from?", "⏳ Frage Home Assistant …": "⏳ Asking Home Assistant …", "— nicht verwenden —": "— don't use —", "Ladestand (Pflicht)": "Charge level (required)", "Lädt gerade": "Charging now", "Vorausgewählt ist, was nach deinem Auto aussieht. Bitte kurz prüfen — die Zahl in Klammern ist der aktuelle Wert.": "Preselected is what looks like your car. Please check briefly — the number in brackets is the current value.", "Werte deines Autos gefunden.": "values of your car found.", "Nichts gefunden, das sicher nach deinem Auto aussieht — bitte unten selbst auswählen.": "Nothing found that clearly looks like your car — please choose below yourself.", "Überblick für Wallboxen, PV, Speicher und Fahrzeuge via evcc. Steuern nur, wenn du es je Ladepunkt erlaubst.": "Overview of chargers, solar, batteries and vehicles via evcc. Control only if you allow it per charge point.", "⚙ Steuern erlauben": "⚙ Allow control", "Steuern erlauben": "Allow control", "Aus": "Off", "Sofort": "Now", "Min+PV": "Min+PV", "PV": "PV", "Ziel-Ladestand": "Charge limit", "Ziel": "Limit", "Steuern aus": "Control off", "Steuern für diesen Ladepunkt erlauben? Das Cockpit darf dann über evcc den Lademodus und den Ziel-Ladestand ändern. Mehr nicht.": "Allow control for this charge point? The cockpit may then change the charge mode and charge limit via evcc. Nothing else.", "Sende an evcc …": "Sending to evcc …", "evcc hat übernommen": "evcc applied it", "Modus": "mode", "evcc hat die Änderung nicht übernommen": "evcc did not apply the change", "Steuern für freigeschaltete Ladepunkte": "control for unlocked charge points", "nur lesend": "read-only", "↗ im eigenen Fenster": "↗ in its own window", "🗺️ Routenplaner": "🗺️ Route planner", "✕ Schließen": "✕ Close", "Keine Route bereit. Plane eine und schick sie mit „An Auto senden“ ins Auto.": "No route ready. Plan one and send it to the car with “Send to car”.", "Navigation läuft": "navigation running", "im Auto angekommen": "arrived in the car", "im Auto abgelehnt": "rejected in the car", "nächster Ladestopp": "next charging stop", "vom Auto abgeholt": "picked up by the car", "wartet aufs Auto": "waiting for the car", "Route": "Route", "Ladestopp": "charging stop", "Ladestopps": "charging stops", "Ankunft": "arrival", "💳 Meine Ladekarten": "💳 My charging cards", "Kommt bald: Der Planer kann Ladekarten noch nicht speichern.": "Coming soon: the planner can't store charging cards yet.", "Zum Speichern erst mit dem Routenplaner verbinden (Einstellungen → Extras).": "To save, first connect the route planner (settings → extras).", "Ladesäulen auf der Karte zeigen dann den Preis deiner Karte, der Planer bevorzugt passende Ladestopps.": "Chargers on the map then show your card's price, and the planner prefers matching charging stops.", "Speichern": "Save", "Karte": "card", "Karten": "cards", "Gespeichert — gilt auch auf /ev/ und im Planer.": "Saved — also applies on /ev/ and in the planner.", "💳 Deine Ladekarten wählst du danach im Cockpit unter „Routenplaner → Meine Ladekarten“. Gespeichert wird beim Planer nur, welche Karten du hast.": "💳 You choose your charging cards afterwards in the cockpit under “Route planner → My charging cards”. The planner only stores which cards you have.", "Planer-Link ungültig oder abgelaufen — bitte in den Einstellungen neu eintragen": "Planner link invalid or expired — please enter it again in the settings", "Lizenz": "License", "Lizenzen": "Licenses", "Wallbox steuern kommt nach dem Praxistest": "Charger control comes after real-world testing", "Überblick für Wallboxen, PV, Speicher und Fahrzeuge via evcc (nur lesend; Steuern kommt nach dem Praxistest).": "Overview of chargers, solar, batteries and vehicles via evcc (read-only; control comes after real-world testing).", "Kopplungs-Code aus Panoptes („Gerät koppeln“, 10 min gültig, einmal verwendbar)": "Pairing code from Panoptes (“Pair device”, valid 10 min, single use)"}''')
_I18N.update({
    "Übersicht": "Overview", "Klima": "Climate", "Laden": "Charging", "Energie": "Energy",
    "Preise": "Prices", "Standort": "Location", "KLIMA & KOMFORT": "CLIMATE & COMFORT",
    "Jetzt aktualisieren": "Refresh now", "noch nicht aktualisiert": "not updated yet",
    "Energie & Ladepunkte": "Energy & charge points", "Im LAN suchen": "Search LAN",
    "⚡ Energie & Ladepunkte": "⚡ Energy & charge points",
    "Ein lesender Überblick für Wallboxen, PV, Speicher und Fahrzeuge via evcc.":
        "A read-only overview of chargers, solar, batteries and vehicles via evcc.",
    "Optional – noch nicht verbunden": "Optional — not connected yet",
    "evcc IP-Adresse": "evcc IP address", "evcc Port": "evcc port",
    "Verbinden": "Connect", "NICHT VERBUNDEN": "NOT CONNECTED",
    "VERBUNDEN": "CONNECTED", "FEHLER": "ERROR", "gerade eben": "just now", "vor": "ago",
    "FAHRZEUGE & LADEPUNKTE": "VEHICLES & CHARGE POINTS", "PV-Erzeugung": "Solar production",
    "Netz": "Grid", "Speicher": "Battery", "Hausverbrauch": "Home consumption",
    "Netzpreis": "Grid tariff", "Grünstromanteil": "Green energy share",
    "FAHRZEUG": "VEHICLE", "Rechtlich neutrale Silhouette": "Legally neutral silhouette", "geschätzt von Panoptes": "estimated by Panoptes", "Nennkapazität × Akku-Gesundheit": "nominal capacity × battery health", "Mit Panoptes übernimmt das Cockpit die Schätzung von Panoptes (höchstens die Nennkapazität des Modells).": "With Panoptes the cockpit uses Panoptes' estimate (at most the model's nominal capacity).", "Unerwartete Antwort vom Cockpit-Server": "Unexpected answer from the cockpit server", "Keine Antwort nach 60 s – der Routenplaner ist gerade zu langsam. Bitte gleich noch einmal.": "No answer after 60 s – the route planner is too slow right now. Please try again shortly.", "Ladenetze einstellen (Planer → Route → Erweitert)": "Set charging networks (planner → Route → Advanced)", "Der Routenplaner hat nach 50 s nicht geantwortet – bitte gleich noch einmal versuchen": "The route planner did not answer within 50 s – please try again shortly", "Routenplaner nicht erreichbar – Internetverbindung prüfen": "Route planner not reachable – check your internet connection", "Der Routenplaner wird gerade neu gestartet oder ist ausgelastet (HTTP 503) – bitte in einer Minute erneut": "The route planner is restarting or busy (HTTP 503) – please try again in a minute", "Der Routenplaner wird gerade neu gestartet oder ist ausgelastet (HTTP 502) – bitte in einer Minute erneut": "The route planner is restarting or busy (HTTP 502) – please try again in a minute", "Der Routenplaner wird gerade neu gestartet oder ist ausgelastet (HTTP 504) – bitte in einer Minute erneut": "The route planner is restarting or busy (HTTP 504) – please try again in a minute", "Zu viele Anfragen – bitte eine Minute warten": "Too many requests – please wait a minute", "Öffnungszeit unbekannt": "opening hours unknown", "24 h geöffnet": "open 24 h", "Start": "Start", "Ziel": "Destination", "Akku jetzt": "Battery now", "Ankunft mind.": "Arrive with at least", "Wie": "How", "ausgewogen": "balanced", "günstig": "cheap", "schnell": "fast", "🗺️ Route berechnen": "🗺️ Calculate route", "Start und Ziel gehen nur beim Klick auf „Route berechnen“ an den Routenplaner (byd.serveone.at) – das ist die Anfrage selbst. Kein Dauerversand, nichts im Hintergrund. Die Ortssuche fragt nur, während du tippst.": "Start and destination are sent to the route planner (byd.serveone.at) only when you click “Calculate route” – that is the request itself. Nothing is sent continuously or in the background. Place search only asks while you type.", "📤 Ins Auto schicken": "📤 Send to car", "„Ins Auto schicken“ legt nur die Route beim Routenplaner ab; Panoptes im Auto holt sie dort ab. Am Fahrzeug wird nichts ausgelöst – kein Befehl, keine Navigation startet von selbst.": "“Send to car” only stores the route with the route planner; Panoptes in the car picks it up there. Nothing is triggered on the vehicle – no command, no navigation starts by itself.", "Nichts gefunden": "Nothing found", "Bitte ein Ziel aus der Liste wählen": "Please choose a destination from the list", "Bitte einen Start aus der Liste wählen oder das Feld leeren (dann gilt dein Auto)": "Please choose a start from the list or clear the field (then your car is used)", "⏳ Frage den Routenplaner …": "⏳ Asking the route planner …", "vom Auto": "from the car", "Fahrt": "driving", "Ladestopp": "charging stop", "Ladestopps": "charging stops", "Ankunft mit": "Arrival with", "Deine Ladevorlieben gelten": "Your charging preferences apply", "Ladevorlieben (z. B. nur bestimmte Ladenetze) stellst du im Planer-Konto ein": "Charging preferences (e.g. only certain networks) are set in your planner account", "Konto-Einstellungen": "Account settings", "Profil": "Profile", "nach": "after", "Kein Ladestopp nötig.": "No charging stop needed.", "nur": "only", "bevorzugt": "preferred", "Umweg bis": "detour up to", "nur wenn bei Ankunft geöffnet": "only if open on arrival", "ohne Kartenbilder (keine Kartenquelle gewählt)": "without map images (no map source chosen)", "⚪ Start · 🟢 Ladestopp · 🟠 Ziel": "⚪ start · 🟢 charging stop · 🟠 destination", "Route liegt im Planer bereit – Panoptes im Auto holt sie ab.": "Route is ready in the planner – Panoptes in the car picks it up.", "Öffnungszeit unbekannt": "opening hours unknown", "rund um die Uhr geöffnet": "open 24/7", "offen bis": "open until", "bei Ankunft geschlossen": "closed on arrival", "ROUTE": "ROUTE", "Route": "Route", "📍 Mein Auto": "📍 My car", "Ort, Adresse, Link oder Plus Code": "Place, address, link or Plus Code", "Keine Autoposition bekannt – bitte einen Start eingeben": "No car position known – please enter a start", "Bitte zuerst eine Route berechnen": "Please calculate a route first", "Wie oft beim Auto nachfragen?": "How often to ask the car?", "Geparkt": "Parked", "Bei Fahrt bzw. Laden": "While driving or charging", "nur manuell": "manual only", "Jede Abfrage weckt die App im Auto. Ist dieser Tab verborgen, wird pausiert.": "Every query wakes the app in the car. While this tab is hidden, queries pause.", "Nach jedem Antippen kurz alle 5 s (höchstens 60 s), dann wieder der gewählte Takt.": "After each tap briefly every 5 s (at most 60 s), then back to the chosen interval.", "Akku nutzbar in kWh": "Usable battery in kWh", "vom Auto": "from the car", "von dir eingetragen": "entered by you", "Mit Panoptes wird der Wert vom Auto übernommen.": "With Panoptes the value is taken from the car.", "lernt aus deinen Fahrten": "learns from your trips", "liefert diese Datenquelle nicht": "not provided by this data source", "Ich habe den Hinweis gelesen und verstanden.": "I have read and understood the notice.", "Deine Passwörter und Schlüssel liegen unverschlüsselt in der Einstellungsdatei (nur für deinen Benutzer lesbar), weil hier kein Schlüsselbund verfügbar ist. Unter Linux hilft das Paket „libsecret-tools“ (secret-tool) mit einem laufenden Schlüsselbund.": "Your passwords and keys are stored unencrypted in the settings file (readable only by your user) because no keyring is available here. On Linux, the package “libsecret-tools” (secret-tool) with a running keyring helps.", "Wer die Kartenbilder liefert, sieht deine IP-Adresse und die Gegend, die du anschaust. Du entscheidest:": "Whoever delivers the map images sees your IP address and the area you look at. You decide:", "Keine Karte": "No map", "Es werden keine Kartenbilder geladen.": "No map images are loaded.", "Kartenbilder von OpenStreetMap (fremder Dienst).": "Map images from OpenStreetMap (third-party service).", "Community-Karte": "Community map", "Dieselbe Karte wie im Planer und in der Panoptes-App, vom Server der BYD-Community (byd.serveone.at). Nur damit gibt es die Live-Belegung der Ladesäulen.": "The same map as in the planner and the Panoptes app, from the BYD community server (byd.serveone.at). Live charger availability only works with it.", "Karte anzeigen?": "Show the map?", "Wer die Kartenbilder liefert, sieht deine IP-Adresse und die Gegend, die du anschaust.": "Whoever delivers the map images sees your IP address and the area you look at.", "Neu: Karte und 3D-Modell sind freiwillig": "New: map and 3D model are optional", "Beides lädt Daten von fremden Servern; die sehen dabei deine IP-Adresse (und bei der Karte die Gegend, beim 3D-Modell dein Automodell). Ohne deine Wahl bleibt beides aus.": "Both load data from other servers, which see your IP address (and the area for the map, your car model for the 3D model). Without your choice both stay off.", "Karte": "Map", "Dein Auto in 3D (vom Community-Server)": "Your car in 3D (from the community server)", "Speichern": "Save", "Dieselbe Karte wie im Planer und in der Panoptes-App. Die Kartenkacheln deiner Gegend lädt dann der Server der BYD-Community (byd.serveone.at); er sieht dabei deine IP-Adresse und den Kartenausschnitt. Ohne Haken lädt sie OpenStreetMap.": "The same map as in the planner and the Panoptes app. The map tiles for your area are then loaded from the BYD community server (byd.serveone.at); it sees your IP address and the map area. Without the tick, OpenStreetMap loads them.", "🚗 Dein Auto in 3D": "🚗 Your car in 3D", "Lädt einmal das 3D-Modell deines Autos vom Server der BYD-Community (byd.serveone.at). Der Server sieht dabei deine IP-Adresse und welches Modell du fährst. Ohne Haken: neutrale Silhouette oder dein Foto.": "Loads your car's 3D model once from the BYD community server (byd.serveone.at). The server sees your IP address and which model you drive. Without the tick: a neutral silhouette or your photo.", "Zeigt öffentliche Ladestationen am Standort deines Autos mit Entfernung und Steckertyp. Dafür geht die Position deines Autos an OpenStreetMap (Overpass-Dienst) oder an deinen eigenen OpenGlance-Server, wenn du ihn unten einträgst. Mit der Community-Karte kommt die Live-Belegung dazu: dafür geht nur die Kartenmitte, auf etwa 5 km gerundet, an den Server der BYD-Community.": "Shows public chargers at your car's location with distance and connector type. For this, your car's position is sent to OpenStreetMap (Overpass service) or to your own OpenGlance server if you enter it below. With the community map, live availability is added: only the map centre, rounded to about 5 km, goes to the BYD community server.", "Kurz vorab": "Quick note first", "Das EV-Cockpit ist ein privates Freizeitprojekt, kostenlos und ohne Gewähr. Du nutzt es auf eigenes Risiko, nur privat. Es verwendet dein BYD-Konto, Home Assistant oder deine Wallbox so, wie du es einstellst. Für Fernbefehle (z. B. Klima, Zusperren) und Ladebefehle an die Wallbox bist du selbst verantwortlich. Werte wie Ladestand, Reichweite und Preise können abweichen. Das EV-Cockpit ist nicht mit BYD verbunden.": "EV-Cockpit is a private hobby project, free and without warranty. You use it at your own risk, for private use only. It uses your BYD account, Home Assistant or your wallbox as you configure it. You are responsible for remote commands (e.g. climate, locking) and charging commands to your wallbox. Values such as charge level, range and prices may be inaccurate. EV-Cockpit is not affiliated with BYD.", "Alle Hinweise lesen": "Read all notes", "Gelesen und einverstanden": "Read and agreed", "Bitte bestätige die Hinweise, um fortzufahren.": "Please confirm the notes to continue.", "Freizeitprojekt.": "Hobby project.", "Panoptes, das EV-Cockpit und der Routenplaner sind ein privates Freizeitprojekt von Alfred Aigner. Sie werden kostenlos und ohne Gewähr angeboten.": "Panoptes, EV-Cockpit and the route planner are a private hobby project by Alfred Aigner. They are provided free of charge and without warranty.", "Ohne Gewähr.": "No warranty.", "Es gibt keine Garantie, dass alles fehlerfrei, vollständig oder jederzeit verfügbar ist. Das gilt auch für Ladestände, Reichweiten, Preise, Belegung von Ladesäulen, Routen, Blitzer- und Gefahrenhinweise. Prüfe Wichtiges selbst; im Straßenverkehr gilt immer, was du siehst und was die Schilder sagen.": "There is no guarantee that everything is correct, complete or always available. This includes charge levels, range, prices, charger availability, routes, speed camera and hazard warnings. Check anything important yourself; on the road, what you see and the road signs always come first.", "Eigenes Risiko.": "Your own risk.", "Du nutzt alles auf eigenes Risiko. Soweit gesetzlich zulässig, übernimmt Alfred Aigner keine Haftung für Schäden, die aus der Nutzung entstehen, auch nicht für Schäden am Fahrzeug, an Daten oder durch Fernbefehle.": "You use everything at your own risk. To the extent permitted by law, Alfred Aigner accepts no liability for any damage resulting from its use, including damage to your vehicle, to data, or caused by remote commands.", "Du bist verantwortlich.": "You are responsible.", "Du allein entscheidest, wie du die Funktionen einsetzt, und bist dafür verantwortlich, dass das erlaubt ist. Das betrifft vor allem Datenschutz, Kamera-Aufnahmen, Fernbefehle über das BYD-Konto und die Regeln im Straßenverkehr.": "You alone decide how you use the features, and you are responsible for making sure that use is legal. This applies especially to data protection, camera recordings, remote commands via your BYD account, and traffic rules.", "Nur privat.": "Private use only.", "Gedacht ist alles nur für die private Nutzung mit deinem eigenen Fahrzeug. Ein gewerblicher Einsatz (z. B. Flotten, Vermietung, Taxi, Firmenwagen-Überwachung) ist nicht vorgesehen.": "Everything is intended for private use with your own vehicle only. Commercial use (e.g. fleets, rental, taxi, monitoring company cars) is not intended.", "Wächter nur auf eigenem Grund.": "Guardian on your own property only.", "Kamera-Aufnahmen des Wächters sind für deinen eigenen Privatgrund gedacht (z. B. Garage, Einfahrt). Richte die Kameras so aus, dass weder öffentlicher Raum (Straße, Gehweg, öffentlicher Parkplatz) noch das Grundstück der Nachbarn erfasst wird. Aufnahmen nicht veröffentlichen.": "Guardian recordings are intended for your own private property (e.g. garage, driveway). Point the cameras so that neither public space (street, pavement, public car park) nor your neighbours' property is captured. Do not publish recordings.", "Nicht von BYD.": "Not BYD.", "Dieses Projekt ist nicht mit BYD verbunden und wird von BYD weder unterstützt noch geprüft. „BYD“, „DiLink“ und alle anderen genannten Namen und Marken gehören ihren jeweiligen Inhabern.": "This project is not affiliated with BYD and is not supported or reviewed by BYD. “BYD”, “DiLink” and all other names and trademarks mentioned belong to their respective owners.", "Gesetzliche Rechte bleiben.": "Your legal rights remain.", "Die Haftung für Vorsatz und grobe Fahrlässigkeit, für Personenschäden sowie zwingende Rechte von Verbraucherinnen und Verbrauchern werden durch diese Hinweise nicht eingeschränkt.": "Liability for intent and gross negligence, for personal injury, and mandatory consumer rights are not limited by these notes.", "🔗 Mit Panoptes verbinden": "🔗 Connect to Panoptes", "Bestätige in Telegram oder hier:": "Confirm in Telegram or here:", "will sich verbinden. Prüfzahl:": "wants to connect. Check number:", "Panoptes öffnen („Gekoppelte Geräte“)": "Open Panoptes (“Paired devices”)", "Vergleiche die Prüfzahl und tippe auf „Erlauben“. Die Anfrage gilt 2 Minuten.": "Compare the check number and tap “Allow”. The request is valid for 2 minutes.", "Erweitert: mit Kopplungs-Code oder Link": "Advanced: with pairing code or link", "Kopplungs-Code oder Link aus Panoptes („Neues Gerät koppeln“, 10 min gültig, einmal verwendbar)": "Pairing code or link from Panoptes (“Pair new device”, valid 10 min, single use)", "482913 oder https://…/system.html#koppeln=…": "482913 or https://…/system.html#koppeln=…", "🔗 Mit Routenplaner verbinden": "🔗 Connect to route planner", "Im Browser bestätigen:": "Confirm in your browser:", "Code": "Code", "Routenplaner öffnen und erlauben": "Open route planner and allow", "Melde dich dort als Mitglied an und tippe auf „Erlauben“. Der Code gilt 10 Minuten.": "Sign in there as a member and tap “Allow”. The code is valid for 10 minutes.", "Erweitert: mit persönlichem Planer-Link": "Advanced: with your personal planner link", "Warte auf „Erlauben“ …": "Waiting for “Allow” …", "Verbunden": "Connected", "Ladestand ": "charge level ", "Mit dem Routenplaner verbunden": "Connected to the route planner", "Schon gekoppelt. Nur neu verbinden, wenn die Kopplung in Panoptes entfernt wurde.": "Already paired. Only connect again if the pairing was removed in Panoptes.", "3D-Modell nicht geladen": "3D model not loaded", "Erneut versuchen": "Try again", "3D-Modell wird geladen …": "Loading 3D model …", "Laden fehlgeschlagen": "Loading failed", "Dieser Browser kann kein WebGL": "This browser has no WebGL",
    "Eigenes Foto verwenden": "Use your own photo", "Reichweite": "Range",
    "Verbunden": "Connected", "Nicht verbunden": "Not connected",
    "Kompakt": "Compact", "Limousine": "Sedan", "Kombi": "Estate", "SUV": "SUV", "Van": "Van",
    "Fahrzeugformen sind neutrale Illustrationen, keine Herstellerlogos oder exakten Modellabbildungen.":
        "Vehicle shapes are neutral illustrations, not manufacturer logos or exact model images.",
    "Geräte automatisch finden": "Find devices automatically", "Kein IP-Wissen nötig": "No IP knowledge needed",
    "Manuell verbinden (Experten)": "Connect manually (experts)", "Suche im Heimnetz …": "Searching your home network …",
    "Eigenes Autofoto hinzufügen": "Add your own car photo", "Foto wird vorbereitet …": "Preparing photo …",
    "Foto gespeichert": "Photo saved", "Solar wird automatisch angezeigt, sobald evcc oder Home Assistant Werte liefert.":
        "Solar appears automatically as soon as evcc or Home Assistant provides data.",
})
I18N_HEAD = ("<script>window.__TR__=" + json.dumps(_I18N, ensure_ascii=False, separators=(',',':')) + ";"
    "window.__LANG__=(function(){try{var s=localStorage.getItem('evc_lang');if(s==='de'||s==='en')return s;}catch(e){}"
    "return (navigator.language||'de').toLowerCase().indexOf('de')===0?'de':'en';})();"
    "window.__T=function(de){if(window.__LANG__!=='en'||de==null)return de;"
    "var s=''+de,k=s.trim().replace(/[\\t\\n\\r ]+/g,' ');if(!k)return de;var e=window.__TR__[k];"
    "return e===undefined?de:s.match(/^\\s*/)[0]+e+s.match(/\\s*$/)[0];};</script>")
I18N_BODY = r'''<script>
(function(){
  var TR=window.__TR__||{}, LANG=window.__LANG__||'de';
  function tr(t){if(t==null)return null;var k=(''+t).trim().replace(/[\t\n\r ]+/g,' ');if(!k)return null;
    var en=TR[k];if(en===undefined)return null;
    return t.match(/^\s*/)[0]+en+t.match(/\s*$/)[0];}
  function swap(root){
    if(LANG!=='en'||!root)return;
    if(root.nodeType===3){var e=tr(root.nodeValue);if(e!==null)root.nodeValue=e;return;}
    if(root.nodeType!==1)return;
    var w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,null),n,l=[];
    while(n=w.nextNode()){var p=n.parentNode;if(!p)continue;
      var tg=p.nodeName.toLowerCase();if(tg==='script'||tg==='style')continue;
      if(n.nodeValue&&n.nodeValue.trim())l.push(n);}
    l.forEach(function(n){var e=tr(n.nodeValue);if(e!==null)n.nodeValue=e;});
    var q=function(x){return root.querySelectorAll?root.querySelectorAll(x):[];};
    ['placeholder','title','aria-label'].forEach(function(a){
      Array.prototype.forEach.call(q('['+a+']'),function(el){var e=tr(el.getAttribute(a));if(e!==null)el.setAttribute(a,e);});});
    Array.prototype.forEach.call(q('input[type=button],input[type=submit],button'),function(el){
      if(el.value){var e=tr(el.value);if(e!==null)el.value=e;}});
    if(root.getAttribute){['placeholder','title','aria-label'].forEach(function(a){
      if(root.hasAttribute(a)){var e=tr(root.getAttribute(a));if(e!==null)root.setAttribute(a,e);}});}
  }
  function boot(){
    document.documentElement.lang=LANG;
    swap(document.body);
    if(LANG==='en'){
      var mo=new MutationObserver(function(m){m.forEach(function(x){
        Array.prototype.forEach.call(x.addedNodes,function(nd){swap(nd);});});});
      mo.observe(document.body,{childList:true,subtree:true});
    }
    var SPR=[['de','Deutsch'],['en','English']];
    var b=document.createElement('button');
    b.textContent='🌐 '+LANG.toUpperCase();
    b.setAttribute('aria-label',LANG==='en'?'Language: English. Change language':'Sprache: Deutsch. Sprache ändern');
    b.setAttribute('aria-haspopup','true');
    b.style.cssText='position:fixed;right:12px;bottom:12px;z-index:9999;padding:7px 12px;border-radius:20px;border:1px solid rgba(160,230,240,.35);background:rgba(12,20,34,.85);color:#E8FBFD;font:600 13px system-ui,sans-serif;cursor:pointer;-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)';
    var m=document.createElement('div');
    m.style.cssText='position:fixed;right:12px;bottom:52px;z-index:9999;display:none;padding:6px;border-radius:14px;border:1px solid rgba(160,230,240,.35);background:rgba(12,20,34,.96);font:600 13px system-ui,sans-serif';
    SPR.forEach(function(x){var o=document.createElement('button');o.textContent=(x[0]===LANG?'✓ ':'   ')+x[1];
      o.style.cssText='display:block;width:100%;text-align:left;padding:8px 14px;border:0;border-radius:10px;background:'+(x[0]===LANG?'rgba(95,214,230,.18)':'transparent')+';color:#E8FBFD;font:inherit;cursor:pointer;white-space:pre';
      o.onclick=function(){if(x[0]===LANG){m.style.display='none';return;}
        try{localStorage.setItem('evc_lang',x[0]);}catch(e){}location.reload();};
      m.appendChild(o);});
    b.onclick=function(e){e.stopPropagation();m.style.display=m.style.display==='none'?'block':'none';};
    document.addEventListener('click',function(){m.style.display='none';});
    document.body.appendChild(m);
    document.body.appendChild(b);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
</script>'''
def _i18n(h):
    h = h.replace('<head><meta charset=utf-8>', '<head><meta charset=utf-8>' + I18N_HEAD, 1)
    if '</head>' in h:
        h = h.replace('</head>', LOOK_CSS + '</head>', 1)
    return h.replace('</body>', I18N_BODY + '</body>', 1) if '</body>' in h else h + I18N_BODY

# Look wie die Panoptes-App (Ozean, Aqua, Limette; Sora + Manrope). Schriften im Paket (OFL), kein CDN.
LOOK_CSS = """<style>
@font-face{font-family:'Sora';font-weight:400;font-display:swap;src:url(/static/fonts/sora-400.woff2) format('woff2')}
@font-face{font-family:'Sora';font-weight:600;font-display:swap;src:url(/static/fonts/sora-600.woff2) format('woff2')}
@font-face{font-family:'Sora';font-weight:700;font-display:swap;src:url(/static/fonts/sora-700.woff2) format('woff2')}
@font-face{font-family:'Manrope';font-weight:400;font-display:swap;src:url(/static/fonts/manrope-400.woff2) format('woff2')}
@font-face{font-family:'Manrope';font-weight:500;font-display:swap;src:url(/static/fonts/manrope-500.woff2) format('woff2')}
@font-face{font-family:'Manrope';font-weight:600;font-display:swap;src:url(/static/fonts/manrope-600.woff2) format('woff2')}
@font-face{font-family:'Manrope';font-weight:700;font-display:swap;src:url(/static/fonts/manrope-700.woff2) format('woff2')}
:root{--deep:#071a2b;--ocean:#0A2238;--aqua:#5FD6E6;--lime:#B5F23D;--lime-ink:#1d2a00;--coral:#FF8A6B;--amber:#FFC266;
 --ink:#EAF6F8;--ink-2:#A9C7CE;--ink-3:#6E8E97;--line:rgba(160,230,240,.14)}
body{font-family:'Manrope',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif!important;
 background:radial-gradient(1200px 700px at 85% -10%,rgba(11,92,102,.55),transparent 60%) fixed,
  linear-gradient(160deg,var(--ocean),var(--deep) 70%) fixed!important}
html{background:var(--deep)}
h1,h2,h3,.sect,.big,.val,.v,.nav button,.kpi,.num{font-family:'Sora',system-ui,sans-serif}
</style>"""

ABOUT = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Über &amp; Rechtliches</title>
<style>
:root{--blue:#5FD6E6;--txt:#EAF6F8;--mut:#A9C7CE;--line:rgba(160,230,240,.18)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1100px 700px at 50% -8%,#0d3a4a,#071a2b 55%,#04101b);
 color:var(--txt);font:15px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:26px}
.w{max-width:700px;margin:0 auto}
h1{font-weight:300;font-size:28px;margin:0 0 18px}
h2{font-size:15px;letter-spacing:1px;color:var(--mut);margin:22px 0 8px;text-transform:uppercase}
.card{background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));border:1px solid var(--line);
 border-radius:16px;padding:18px 20px;margin-bottom:14px}
.warn{background:rgba(255,176,32,.09);border:1px solid rgba(255,176,32,.4)}
a{color:var(--blue)}
.back{display:inline-block;margin-bottom:18px;color:var(--mut);text-decoration:none}
small{color:var(--mut)}
</style></head><body><div class=w>
<a class=back href="/">← zurück zum Cockpit</a>
<h1>EV-Cockpit __VERSION__</h1>

<div class=card>
 <h2 style="margin-top:0">Was das ist</h2>
 Ein <b>freies Werkzeug für die BYD-Community</b>. Es zeigt dir die Daten deines eigenen Autos
 auf deinem eigenen Rechner — ohne Umweg über fremde Server. Gebaut aus Freude an der Sache
 und im Sinne des Rechts auf Reparatur. Kostenlos, für niemanden ein Geschäft.
</div>

<div class=card>
 <h2 style="margin-top:0">Projekt &amp; Kontakt</h2>
 Freies, nicht-kommerzielles Community-Projekt, quelloffen auf GitHub:<br>
 <a href="https://github.com/samuelvoltarius/byd-ev-cockpit" target="_blank" rel="noopener">github.com/samuelvoltarius/byd-ev-cockpit</a><br>
 <small>Fragen oder Fehler? Bitte als Issue melden:</small><br>
 <a href="https://github.com/samuelvoltarius/byd-ev-cockpit/issues" target="_blank" rel="noopener">github.com/samuelvoltarius/byd-ev-cockpit/issues</a>
</div>

<div class="card warn">
 <h2 style="margin-top:0">⚠️ Haftungsausschluss — bitte lesen</h2>
 <b>Keine Verbindung zu BYD.</b> Dies ist <b>kein offizielles Produkt</b> der BYD Auto Co. Ltd.
 und steht in keinerlei Verbindung zu BYD. „BYD" ist eine Marke ihrer jeweiligen Inhaber und wird
 hier nur genannt, um die Kompatibilität zu beschreiben.<br><br>

 <b>Nutzung auf eigene Gefahr.</b> Diese Software wird kostenlos und <b>ohne jede Gewähr</b>
 bereitgestellt — ohne Zusicherung von Funktion, Richtigkeit oder Verfügbarkeit. Sie <b>steuert
 ein echtes Fahrzeug</b> (z.B. die Klimaanlage). Für Schäden jeder Art, Datenverlust oder Folgen
 aus der Nutzung wird <b>keine Haftung</b> übernommen, soweit gesetzlich zulässig.<br><br>

 <b>BYDs Nutzungsbedingungen.</b> Der Zugriff auf die BYD-Cloud über eine fremde Anwendung kann
 den Nutzungsbedingungen von BYD widersprechen. Im ungünstigsten Fall kann BYD einen Account
 einschränken oder sperren. <b>Das entscheidest du selbst und trägst es selbst.</b><br><br>

 <b>Zweiter Account.</b> Die BYD-Cloud erlaubt pro Account nur eine aktive Sitzung. Nutze einen
 zweiten Account als Zusatznutzer — sonst stört dieses Werkzeug deine eigene BYD-App.
</div>

<div class=card>
 <h2 style="margin-top:0">🔒 Datenschutz</h2>
 <b>Deine Daten bleiben auf diesem Rechner.</b> Zugangsdaten und Fahrzeugdaten werden
 ausschließlich lokal gespeichert (<code>~/.evcockpit/</code>). Die einzige Gegenstelle im Normalbetrieb
 ist die <b>BYD-Cloud selbst</b> — also der Dienst, dessen Daten du abrufst.<br><br>
 <b>Zwei freiwillige Ausnahmen</b>, beide <b>standardmäßig aus</b> und im Assistenten anhakbar:<br>1. <b>Strompreis</b> — dein Rechner fragt aWATTar bzw. energy-charts.info nach den Börsenpreisen deines Landes. Übertragen wird dabei nur die Anfrage selbst (die Gegenstelle sieht deine IP, wie bei jedem Webseitenbesuch) — <b>keine Fahrzeugdaten</b>.<br>2. <b>Nutzungszählung</b> —
 Nur wenn du sie im Assistenten aktiv anhakst, sendet das Programm einmal am Tag genau das hier:
 <div style="background:rgba(0,0,0,.3);border-radius:9px;padding:11px;margin-top:9px;font-family:ui-monospace,monospace;font-size:12.5px">
 { "id": "<span>zufällige Installations-ID</span>", "version": "__VERSION__", "model": "<span>dein Automodell</span>" }
 </div>
 <small style="display:block;margin-top:8px">Kein Name, keine E-Mail, keine VIN, kein Standort, keine Fahrdaten.
 Die ID ist eine Zufallszahl ohne Personenbezug. Häkchen jederzeit im Assistenten abschaltbar.</small>
</div>

<div class=card>
 <h2 style="margin-top:0">Quelloffen</h2>
 Du sollst uns nicht glauben müssen — <b>schau nach</b>. Der gesamte Quelltext liegt offen;
 die Datei, die du gestartet hast, ist lesbarer Python-Code.
</div>
<div class=card>
 <h2 style="margin-top:0">Lizenzen</h2>
 <b>3D-Automodelle</b> (dieselben wie in Panoptes, Manifest live vom Community-Server): teils von
 <a href="https://sketchfab.com/NazhDesign" target=_blank rel=noopener>Nazh Design</a> unter
 <a href="https://creativecommons.org/licenses/by/4.0/" target=_blank rel=noopener>CC BY 4.0</a> (für Panoptes angepasst:
 Herstellerlogos entfernt, Netz reduziert, Lack als eigenes Material), teils Eigenbauten des Panoptes-Projekts unter CC0.
 Die Angabe zum gezeigten Modell steht direkt unter dem Auto. Alle Modelle mit Quelle:
 <a href="https://byd.serveone.at/tiles/models/MODELLE_LIZENZEN.md" target=_blank rel=noopener>Modell-Lizenzen</a>.<br>
 <b>three.js</b> (3D-Darstellung, im Paket): MIT-Lizenz, © three.js authors.<br>
 <b>Leaflet</b>, <b>MapLibre GL</b>, <b>PMTiles</b>: BSD/MIT-Lizenzen. Schriften <b>Sora</b> und <b>Manrope</b>: SIL Open Font License.<br>
 Kartendaten © OpenStreetMap-Mitwirkende.
</div>
</div></body></html>"""


# ---------------------------------------------------------------- Panoptes-Einstellungen (HTML)
# Generisch aus GET /api/einstellungen/schema (Vertrag EINSTELLUNGEN_SCHEMA.md) - keine eigene Feldliste.
PANOPTES_SEITE = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Panoptes-Einstellungen</title>
<style>
body{margin:0;color:#EAF6F8;font:15px/1.5 system-ui,sans-serif}.w{max-width:760px;margin:0 auto;padding:22px 16px 80px}
a{color:#5FD6E6}.card{background:rgba(255,255,255,.04);border:1px solid rgba(160,230,240,.16);border-radius:16px;padding:14px 16px;margin:14px 0}
h1{font-size:24px;margin:.2em 0}h2{font-size:17px;margin:0 0 8px}.f{padding:10px 0;border-top:1px solid rgba(160,230,240,.08)}
.f:first-of-type{border-top:0}.t{font-weight:600}.h{color:#A9C7CE;font-size:13px;margin-top:2px}
input,select{background:rgba(0,0,0,.25);color:#EAF6F8;border:1px solid rgba(160,230,240,.22);border-radius:8px;padding:7px 9px;font-size:14px;margin-top:6px;max-width:100%;box-sizing:border-box}
input[type=checkbox]{width:20px;height:20px}.lock{color:#A9C7CE;font-size:12.5px}.err{color:#FFC266;font-size:13px}
.ok{color:#B5F23D}.leiste{position:sticky;bottom:0;background:#071a2b;padding:12px 0;display:flex;gap:10px;align-items:center}
button{background:#B5F23D;color:#1d2a00;font-weight:700;border:0;border-radius:12px;padding:10px 16px;cursor:pointer}
.best{background:rgba(255,194,102,.08);border:1px solid rgba(255,194,102,.35);border-radius:10px;padding:8px 10px;margin-top:8px;font-size:13px}
</style></head><body><div class=w>
<a href="/">← Cockpit</a>
<h1>📡 Panoptes-Einstellungen</h1>
<div class=h>Direkt aus Panoptes in deinem Auto. Hier ändern sich nur gespeicherte Einstellungen — am Auto wird dadurch nichts ausgelöst.
Fernzugang, Login, Ports und adb siehst du hier nur; ändern lassen sie sich aus Sicherheitsgründen nur im Auto.</div>
<div id=inhalt><div class=card>⏳ Frage Panoptes …</div></div>
<div class=leiste><button id=speichern onclick="speichern()" disabled>Speichern</button><span id=msg class=h></span></div>
</div>
<script>
const SPR=(window.__LANG__==='en')?'en':'de';let STAND=null,AEND={},BEST=new Set();
const esc=t=>String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const wert=k=>((STAND.werte||{}).werte||{})[k]||{};
function sichtbar(f){const n=f.nurWenn;if('sichtbar' in f&&!(n&&n.key))return !!f.sichtbar;if(!n)return true;
 if(n.key)return (k=>k in AEND?AEND[k]:wert(k).wert)(n.key)===n.gleich;return false;}
// Pflichttext wortgleich wie im Web: Titel, Einleitung, je Option Name + Erklaerung, Schluss
function pflichttext(t){if(!t)return '';if(typeof t==='string')return '<div>'+esc(t)+'</div>';
 const buch=[...new Set(Object.keys(t).map(k=>k.split('.')[0]).filter(x=>/^[a-z]$/.test(x)))].sort();
 return (t.title?'<div class=t>'+esc(t.title)+'</div>':'')+(t.intro?'<div>'+esc(t.intro)+'</div>':'')+
  buch.map(b=>'<div style="margin-top:6px"><b>'+esc(t[b+'.label']||'')+'</b>'+(t[b+'.desc']?' — '+esc(t[b+'.desc']):'')+
   (t[b+'.note']?'<div style="font-size:.92em;margin-top:2px">'+esc(t[b+'.note'])+'</div>':'')+'</div>').join('')+
  (t.footer?'<div style="margin:6px 0">'+esc(t.footer)+'</div>':'');}
function feldHtml(f){const w=wert(f.key),v=(f.key in AEND)?AEND[f.key]:w.wert,lock=!!f.nurLesendExtern,
 id='f_'+f.key.replace(/[^a-zA-Z0-9]/g,'_'),dis=lock?' disabled':'';let e='';
 if(f.typ==='bool')e='<input type=checkbox id='+id+(v?' checked':'')+dis+' onchange="setze(\''+f.key+'\',this.checked)">';
 else if(f.typ==='int'||f.typ==='zahl')e='<input type=number id='+id+' value="'+esc(v??f.standard??'')+'"'+(f.min!=null?' min='+f.min:'')+(f.max!=null?' max='+f.max:'')+
  (f.schritt?' step='+f.schritt:(f.typ==='int'?' step=1':' step=any'))+dis+' onchange="setze(\''+f.key+'\',this.value===\'\'?null:Number(this.value))"> '+esc(f.einheit||'');
 else if(f.typ==='auswahl')e='<select id='+id+dis+' onchange="setze(\''+f.key+'\',this.value)">'+(v==null?'<option value="">— bitte wählen —</option>':'')+
  (f.optionen||[]).map(o=>'<option value="'+esc(o.wert)+'"'+(o.wert===v?' selected':'')+(o.gesperrt?' disabled':'')+'>'+esc(o.titel||o.wert)+(o.gesperrt&&o.gesperrtGrund?' ('+esc(o.gesperrtGrund)+')':'')+'</option>').join('')+'</select>';
 else if(f.typ==='zeit')e='<input type=time id='+id+' value="'+esc(v||'')+'"'+dis+' onchange="setze(\''+f.key+'\',this.value)">';
 else if(f.typ==='farbe')e='<input type=color id='+id+' value="'+esc(v||'#000000')+'"'+dis+' onchange="setze(\''+f.key+'\',this.value)">';
 else if(f.typ==='text')e='<input id='+id+' value="'+esc(v??'')+'"'+dis+' onchange="setze(\''+f.key+'\',this.value)">';
 else if(f.typ==='geheim')e='<input type=password id='+id+' placeholder="'+(w.gesetzt?'••••••• (gesetzt — leer lassen zum Behalten)':'nicht gesetzt')+'"'+dis+' onchange="if(this.value)setze(\''+f.key+'\',this.value)">';
 else e='<div class=h>'+(Array.isArray(v)?v.length+' Einträge':'')+' — bearbeiten im Auto oder im Panoptes-Web.</div>';
 const best=f.bestaetigung&&(f.key in AEND)?'<div class=best>'+pflichttext(f.bestaetigungText)+'<label><input type=checkbox onchange="this.checked?BEST.add(\''+f.key+'\'):BEST.delete(\''+f.key+'\')"> '+
  esc(__T('Ich habe den Hinweis gelesen und verstanden.'))+'</label></div>':'';
 const wirk=(w.gesetzt===false&&w.wirksam!=null&&w.wirksam!==v)?'<div class=lock>derzeit wirksam: '+esc(((f.optionen||[]).find(o=>o.wert===w.wirksam)||{}).titel||w.wirksam)+'</div>':'';
 return '<div class=f><div class=t>'+esc(f.titel||f.key)+(f.gefahr?' ⚠️':'')+'</div>'+(f.hilfe?'<div class=h>'+esc(f.hilfe)+'</div>':'')+e+wirk+
  (lock?'<div class=lock>🔒 nur im Auto änderbar</div>':'')+(f.neustartNoetig?'<div class=lock>↻ wirkt nach einem Neustart von Panoptes</div>':'')+best+
  '<div class=err id=e_'+id+'></div></div>';}
const OFFEN=new Set();   // aufgeklappte "Erweitert"-Bereiche bleiben beim Neuzeichnen offen
function zeichne(){const g=(STAND.schema||{}).gruppen||[],ord=(a,b)=>(a.reihenfolge||0)-(b.reihenfolge||0);
 document.getElementById('inhalt').innerHTML=g.slice().sort(ord).map(x=>{
  const ff=(x.felder||[]).filter(sichtbar).sort(ord);if(!ff.length)return '';
  const abs=[];ff.forEach(f=>{const a=f.abschnitt||{id:'',titel:'',reihenfolge:-1};let z=abs.find(y=>y.id===a.id);
   if(!z){z={id:a.id,titel:a.titel,reihenfolge:a.reihenfolge||0,f:[]};abs.push(z);}z.f.push(f);});
  return '<div class=card><h2>'+esc(x.titel||x.id)+'</h2>'+abs.sort(ord).map(a=>{const normal=a.f.filter(f=>!f.erweitert),erw=a.f.filter(f=>f.erweitert);
   return (a.titel?'<div class=t style="margin-top:10px;color:#5FD6E6">'+esc(a.titel)+'</div>':'')+normal.map(feldHtml).join('')+
    (erw.length?'<details id="d_'+esc(x.id+'_'+a.id)+'"'+(OFFEN.has('d_'+x.id+'_'+a.id)?' open':'')+' ontoggle="this.open?OFFEN.add(this.id):OFFEN.delete(this.id)"><summary class=h style="cursor:pointer">Erweitert ('+erw.length+')</summary>'+erw.map(feldHtml).join('')+'</details>':'');}).join('')+'</div>';
 }).join('')||'<div class=card>Keine Einstellungen.</div>';
 document.getElementById('speichern').disabled=!Object.keys(AEND).length;}
function setze(k,v){const f=((STAND.schema.gruppen||[]).flatMap(g=>g.felder||[])).find(x=>x.key===k);
 if(f&&f.gefahr&&!confirm('Diese Einstellung verändert sichtbares Verhalten am Auto. Wirklich ändern?')){zeichne();return;}
 AEND[k]=v;zeichne();}
async function laden(){try{const d=await (await fetch('/panoptes/einstellungen?sprache='+SPR,{cache:'no-store'})).json();
 if(!d.gekoppelt){document.getElementById('inhalt').innerHTML='<div class=card>Panoptes ist nicht gekoppelt. Koppeln: Einstellungen → Datenquelle → Panoptes im Auto.</div>';return;}
 if(d.fehler){document.getElementById('inhalt').innerHTML='<div class=card>⚠️ '+esc(d.fehler)+'</div>';return;}
 STAND=d;AEND={};BEST=new Set();zeichne();}catch(e){document.getElementById('inhalt').innerHTML='<div class=card>⚠️ '+esc(e)+'</div>';}}
async function speichern(){const m=document.getElementById('msg');m.textContent='⏳ Speichere …';
 try{const r=await (await fetch('/panoptes/einstellungen',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({sprache:SPR,etag:(STAND.werte||{}).etag,werte:AEND,bestaetigt:[...BEST]})})).json();
  if(r.grund==='veraltet'){m.textContent='⚠️ Inzwischen wurde im Auto etwas geändert — neu geladen, bitte nochmal.';await laden();return;}
  const fe=r.fehler||{};if(r.neu){STAND=Object.assign({},r.neu,{gekoppelt:true});}
  AEND=Object.fromEntries(Object.entries(AEND).filter(([k])=>k in fe));zeichne();
  Object.entries(fe).forEach(([k,g])=>{const el=document.getElementById('e_f_'+k.replace(/[^a-zA-Z0-9]/g,'_'));if(el)el.textContent='⚠️ '+g;});
  const n=Object.keys(r.gespeichert||{}).length;
  m.innerHTML=(n?'<span class=ok>✅ '+n+' gespeichert und im Auto nachgelesen.</span> ':'')+(Object.keys(fe).length?'⚠️ '+Object.keys(fe).length+' nicht übernommen.':'');
 }catch(e){m.textContent='⚠️ '+e;}}
laden();
</script></body></html>"""


# ---------------------------------------------------------------- Assistent (HTML)
WIZARD = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Einrichtung</title>
<style>
:root{--blue:#5FD6E6;--cyan:#43c9db;--txt:#EAF6F8;--mut:#A9C7CE;--line:rgba(160,230,240,.18)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1100px 700px at 50% -8%,#0d3a4a,#071a2b 55%,#04101b);
 color:var(--txt);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:26px 20px 60px}
.w{max-width:680px;margin:0 auto}
h1{font-weight:300;font-size:29px;margin:0 0 4px}.sub{color:var(--mut);margin-bottom:20px;font-size:15px}
/* Fortschritt */
.dots{display:flex;align-items:center;gap:0;margin:0 0 22px}
.dot2{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;position:relative}
.dot2 i{width:26px;height:26px;border-radius:50%;background:rgba(255,255,255,.07);border:1px solid var(--line);
 display:flex;align-items:center;justify-content:center;font-size:12px;font-style:normal;color:var(--mut);z-index:2}
.dot2 b{font-size:10px;color:var(--mut);font-weight:400;text-align:center;letter-spacing:.3px}
.dot2:not(:last-child):after{content:"";position:absolute;top:13px;left:50%;width:100%;height:1px;background:var(--line);z-index:1}
.dot2.on i{background:linear-gradient(135deg,#5FD6E6,#43c9db);color:#04101b;border-color:transparent;font-weight:700}
.dot2.on b{color:var(--txt)}
.dot2.done i{background:rgba(91,227,163,.25);border-color:rgba(91,227,163,.5);color:#B5F23D}
.card{background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:1px solid var(--line);
 border-radius:18px;padding:20px;margin-bottom:14px}
.warn{background:rgba(255,176,32,.10);border:1px solid rgba(255,176,32,.45);border-radius:16px;padding:16px 18px;margin-bottom:14px}
.warn b{color:#FFC266}
.ok{background:rgba(91,227,163,.08);border:1px solid rgba(91,227,163,.35);border-radius:16px;padding:14px 16px;margin-bottom:14px;font-size:14px}
label{display:block;color:var(--mut);font-size:12px;letter-spacing:1px;margin:12px 0 5px}
input,select{width:100%;padding:12px 13px;border-radius:11px;border:1px solid var(--line);
 background:rgba(255,255,255,.05);color:var(--txt);font-size:15px}
select{background-color:#0A2238;color:#EAF6F8}
select option{background-color:#0A2238;color:#EAF6F8}
input::placeholder{color:#6f83a0}
input[type=file]{padding:9px;background:rgba(255,255,255,.05)}
input[type=file]::file-selector-button{background:rgba(95,214,230,.18);color:#E8FBFD;border:1px solid var(--line);
 border-radius:8px;padding:7px 12px;margin-right:10px;cursor:pointer}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:560px){.row{grid-template-columns:1fr}.dot2 b{display:none}}
button{padding:13px 22px;border:0;border-radius:26px;background:linear-gradient(90deg,#5FD6E6,#43c9db);
 color:#04101b;font-weight:700;font-size:15px;cursor:pointer}
button:disabled{opacity:.45;cursor:not-allowed}
button.sec{background:rgba(255,255,255,.08);color:var(--txt);border:1px solid var(--line)}
.nav{display:flex;justify-content:space-between;gap:10px;margin-top:18px}
.msg{margin-top:10px;font-size:14px;min-height:20px}
small{color:var(--mut)}
.chk{display:flex;align-items:flex-start;gap:11px;margin-top:12px;padding:13px;border:1px solid var(--line);
 border-radius:12px;background:rgba(255,255,255,.03)}
.chk input{width:20px;height:20px;margin-top:2px;flex:0 0 auto}
.chk div{font-size:14px}.chk .h{font-weight:600;margin-bottom:2px}
.chk small{display:block;color:var(--mut);margin-top:3px;line-height:1.45}
.pan{display:none}.pan.on{display:block;animation:fade .25s ease}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
code{background:rgba(0,0,0,.3);padding:1px 5px;border-radius:5px;font-size:12.5px}
</style></head><body><div class=w>
<h1 id=wtitle>EV-Cockpit einrichten</h1>
<div class=sub id=wsub>Dein Auto, dein Rechner, deine Daten.</div>

<div class=dots id=dots>
 <div class=dot2 data-d=1><i>1</i><b>Wichtig</b></div>
 <div class=dot2 data-d=2><i>2</i><b>Datenquelle</b></div>
 <div class=dot2 data-d=3><i>3</i><b>Dein Auto</b></div>
 <div class=dot2 data-d=4><i>4</i><b>Aussehen</b></div>
 <div class=dot2 data-d=5><i>5</i><b>Extras</b></div>
</div>

<!-- ============ 1: WICHTIG ============ -->
<div class="pan on" data-p=1>
 <div class=warn>
  <b>⚠️ Bitte lies das hier — es ist der wichtigste Punkt</b><br><br>
  Die BYD-Cloud erlaubt pro Konto nur <b>eine</b> aktive Verbindung. Wenn du hier <b>dasselbe Konto</b>
  einträgst wie in deiner BYD-App am Handy, <b>stören sich beide gegenseitig</b> — mal spinnt das
  Cockpit, mal die App (Fehler 6024).<br><br>
  <b>So machst du es richtig:</b>
  <ol style="margin:8px 0 0 18px;padding:0">
   <li>In der BYD-App ein <b>zweites Konto</b> anlegen (andere E-Mail-Adresse)</li>
   <li>Dieses zweite Konto im Auto als <b>„Zusatznutzer"</b> freigeben</li>
   <li>Hier gleich das <b>zweite</b> Konto eintragen — nicht dein Haupt-Konto</li>
  </ol>
  <br>Dann laufen App und Cockpit friedlich nebeneinander.
  <br><br>Fragt schon ein anderes Programm mit diesem Konto bei BYD nach (z. B. Home Assistant), braucht das
  Cockpit ebenfalls ein eigenes Konto. Hast du Panoptes im Auto, kannst du es stattdessen damit koppeln.
 </div>
 <div class=ok>
  🔒 <b>Deine Daten bleiben auf diesem Rechner.</b> Zugangsdaten und Fahrzeugdaten werden nur lokal
  gespeichert. Dieses Programm sendet <b>nichts</b> an den Entwickler — es spricht nur mit der
  BYD-Cloud selbst. Nachlesbar: die Datei <code>evcockpit.py</code> ist normaler, lesbarer Text.
 </div>
 <div class=warn style="border-color:#3b5268;background:rgba(56,189,248,.06)">
  <b>Kurz vorab</b><br>
  <span>Das EV-Cockpit ist ein privates Freizeitprojekt, kostenlos und ohne Gewähr. Du nutzt es auf eigenes Risiko, nur privat. Es verwendet dein BYD-Konto, Home Assistant oder deine Wallbox so, wie du es einstellst. Für Fernbefehle (z. B. Klima, Zusperren) und Ladebefehle an die Wallbox bist du selbst verantwortlich. Werte wie Ladestand, Reichweite und Preise können abweichen. Das EV-Cockpit ist nicht mit BYD verbunden.</span>
  <details style="margin-top:8px"><summary style="cursor:pointer">Alle Hinweise lesen</summary>
   <ol style="margin:8px 0 0 18px;padding:0">
    <li><b>Freizeitprojekt.</b> <span>Panoptes, das EV-Cockpit und der Routenplaner sind ein privates Freizeitprojekt von Alfred Aigner. Sie werden kostenlos und ohne Gewähr angeboten.</span></li>
    <li><b>Ohne Gewähr.</b> <span>Es gibt keine Garantie, dass alles fehlerfrei, vollständig oder jederzeit verfügbar ist. Das gilt auch für Ladestände, Reichweiten, Preise, Belegung von Ladesäulen, Routen, Blitzer- und Gefahrenhinweise. Prüfe Wichtiges selbst; im Straßenverkehr gilt immer, was du siehst und was die Schilder sagen.</span></li>
    <li><b>Eigenes Risiko.</b> <span>Du nutzt alles auf eigenes Risiko. Soweit gesetzlich zulässig, übernimmt Alfred Aigner keine Haftung für Schäden, die aus der Nutzung entstehen, auch nicht für Schäden am Fahrzeug, an Daten oder durch Fernbefehle.</span></li>
    <li><b>Du bist verantwortlich.</b> <span>Du allein entscheidest, wie du die Funktionen einsetzt, und bist dafür verantwortlich, dass das erlaubt ist. Das betrifft vor allem Datenschutz, Kamera-Aufnahmen, Fernbefehle über das BYD-Konto und die Regeln im Straßenverkehr.</span></li>
    <li><b>Nur privat.</b> <span>Gedacht ist alles nur für die private Nutzung mit deinem eigenen Fahrzeug. Ein gewerblicher Einsatz (z. B. Flotten, Vermietung, Taxi, Firmenwagen-Überwachung) ist nicht vorgesehen.</span></li>
    <li><b>Wächter nur auf eigenem Grund.</b> <span>Kamera-Aufnahmen des Wächters sind für deinen eigenen Privatgrund gedacht (z. B. Garage, Einfahrt). Richte die Kameras so aus, dass weder öffentlicher Raum (Straße, Gehweg, öffentlicher Parkplatz) noch das Grundstück der Nachbarn erfasst wird. Aufnahmen nicht veröffentlichen.</span></li>
    <li><b>Nicht von BYD.</b> <span>Dieses Projekt ist nicht mit BYD verbunden und wird von BYD weder unterstützt noch geprüft. „BYD“, „DiLink“ und alle anderen genannten Namen und Marken gehören ihren jeweiligen Inhabern.</span></li>
    <li><b>Gesetzliche Rechte bleiben.</b> <span>Die Haftung für Vorsatz und grobe Fahrlässigkeit, für Personenschäden sowie zwingende Rechte von Verbraucherinnen und Verbrauchern werden durch diese Hinweise nicht eingeschränkt.</span></li>
   </ol></details>
 </div>
 <div class=chk>
  <input type=checkbox id=disc onchange="schritt1()">
  <div><div class=h>Gelesen und einverstanden</div></div>
 </div>
 <div class=chk>
  <input type=checkbox id=ack onchange="schritt1()">
  <div><div class=h>Verstanden — ich verwende ein zweites BYD-Konto</div>
   <small>Oder: mir ist bewusst, dass es sonst mit meiner BYD-App kollidieren kann.</small></div>
 </div>
 <div class=msg id=discmsg></div>
 <div class=nav><span></span><button id=n1 disabled onclick="go(2)">Weiter →</button></div>
</div>

<!-- ============ 2: DATENQUELLE ============ -->
<div class=pan data-p=2>
 <div class=card>
  <div class=h style="font-weight:700;margin-bottom:4px">Woher soll das Cockpit die Daten deines Autos holen?</div>
  <div class=chk><input type=radio name=quelle id=q_byd value=byd checked onchange="quelleUm()">
   <div><div class=h>🌐 Über ein BYD-Konto</div>
    <small>Für die meisten am einfachsten. Das Cockpit fragt die BYD-Cloud, mit einem eigenen zweiten Konto.</small></div></div>
  <div class=chk><input type=radio name=quelle id=q_ha value=ha onchange="quelleUm()">
   <div><div class=h>🏠 Aus Home Assistant</div>
    <small>Dein Auto ist schon in Home Assistant (BYD-Integration, Panoptes oder anderes). Das Cockpit liest nur.</small></div></div>
  <div class=chk><input type=radio name=quelle id=q_pan value=panoptes onchange="quelleUm()">
   <div><div class=h>📡 Von Panoptes im Auto</div>
    <small>Die Panoptes-App läuft auf deinem Infotainment. Am schnellsten, ganz ohne Cloud.</small></div></div>
 </div>

 <div class=card id=srcha style="display:none">
  <label>Adresse deines Home Assistant</label>
  <input id=hasrcurl placeholder="z.B. http://192.168.0.10:8123">
  <label>Zugriffs-Token <small style="text-transform:none;letter-spacing:0">(in Home Assistant: unten links auf deinen Namen → Sicherheit → ganz unten „Langlebiges Zugriffstoken“ → erstellen)</small></label>
  <input id=hasrctoken type=password placeholder="den langen Text hier einfügen">
  <div style="margin-top:12px"><button class=sec type=button onclick="haSuchen()">🔍 Mein Auto in Home Assistant suchen</button></div>
  <div class=msg id=hasrcmsg></div>
  <div id=hasrcpick style="display:none"></div>
 </div>

 <div class=card id=srcpan style="display:none">
  <input type=checkbox id=panoptes style="display:none">
  <div id=panoptesrow>
   <label>Adresse des Autos (Heimnetz oder Tailscale)</label>
   <input id=panoptesurl placeholder="http://100.x.x.x:8180">
   <div style="margin:10px 0"><button type=button onclick="panoptesAnfrage()">🔗 Mit Panoptes verbinden</button></div>
   <div id=panoptesbest style="display:none;border:1px solid #2a4a63;border-radius:14px;padding:12px 14px;margin:8px 0">
    <div class=h>Bestätige in Telegram oder hier:</div>
    <div style="margin:6px 0">„<span id=pangeraet></span>“ <span>will sich verbinden. Prüfzahl:</span>
     <b id=panpz style="font-size:26px;letter-spacing:.12em;margin-left:6px"></b></div>
    <a id=panweb class=sec target=_blank rel=noopener style="display:inline-block;padding:8px 14px;border-radius:10px;border:1px solid #2a4a63;text-decoration:none;color:#5FD6E6;font-weight:600">Panoptes öffnen („Gekoppelte Geräte“)</a>
    <small style="display:block;margin-top:8px">Vergleiche die Prüfzahl und tippe auf „Erlauben“. Die Anfrage gilt 2 Minuten.</small>
   </div>
   <div class=msg id=panoptesmsg></div>
   <details style="margin-top:10px"><summary style="cursor:pointer">Erweitert: mit Kopplungs-Code oder Link</summary>
    <label>Kopplungs-Code oder Link aus Panoptes („Neues Gerät koppeln“, 10 min gültig, einmal verwendbar)</label>
    <input id=panoptescode type=password placeholder="482913 oder https://…/system.html#koppeln=…">
    <div style="margin:10px 0"><button class=sec type=button onclick="panoptesTest()">🔌 Verbindung prüfen</button></div>
   </details>
  </div>
 </div>

 <details id=srcbydwrap open><summary id=srcbydsum style="cursor:pointer;margin:6px 0 10px;font-weight:600">BYD-Konto</summary>
 <div class=card id=srcbyd>
  <div class=ok style="margin:0 0 16px"><b>Hier gehört nur das separate Cockpit-Konto hinein.</b><br>
   Dein Hauptkonto bleibt ausschließlich in der BYD-App und wird hier bewusst nicht gespeichert.</div>
  <label>E-Mail des separaten Cockpit-Kontos</label>
  <input id=username placeholder="name@beispiel.at" autocomplete=off>
  <label>Passwort</label>
  <input id=password type=password placeholder="Passwort" autocomplete=off>
  <label>Steuer-PIN (6-stellig — dieselbe wie in der BYD-App)</label>
  <input id=pin placeholder="z.B. 123456" maxlength=6 autocomplete=off>
  <div class=row>
   <div><label>Land</label><select id=country>__COUNTRIES__</select></div>
   <div><label>Zeitzone</label><select id=tz>__TZ__</select></div>
  </div>
  <div style="margin-top:16px"><button class=sec id=detectbtn onclick="detect()">🔍 Verbindung einmal prüfen</button></div>
  <div class=msg id=dmsg></div>
 </div>
 <small>Der Knopf führt genau einen Anmeldeversuch aus. Bei falschem Passwort werden weitere Versuche
 automatisch gestoppt, damit BYD das Konto nicht sperrt.</small>
 </details>
 <div class=nav><button class=sec onclick="go(1)">← Zurück</button>
  <button id=n2 disabled onclick="go(3)">Weiter →</button></div>
</div>

<!-- ============ 3: DEIN AUTO ============ -->
<div class=pan data-p=3>
 <div class=card>
  <div id=vinwrap><label>Dein Fahrzeug</label>
  <select id=vin><option value="">— erst Fahrzeuge abrufen —</option></select></div>
  <label>Modell (setzt die Akkugröße)</label>
  <select id=model onchange="setkwh()">__MODELS__</select>
  <div class=row>
   <div><label id=kwhlbl>Akku nutzbar in kWh — <b>bitte prüfen</b></label><input id=kwh value="43.2" oninput="KWH_HAND=true">
    <small id=kwhauto style="display:none;margin-top:4px">Mit Panoptes übernimmt das Cockpit die Schätzung von Panoptes (höchstens die Nennkapazität des Modells).</small>
    <small id=kwhhinweis style="display:none;margin-top:4px"></small></div>
   <div><label>Reifendruck-Sollwert (kPa, optional)</label><input id=tyretarget placeholder="z.B. 250"></div>
  </div>
  <div id=capswrap>
  <div style="margin-top:18px"><button class=sec id=capsbtn onclick="capsLaden()">🔎 Fahrzeugfunktionen laden</button></div>
  <div class=msg id=capsmsg></div>
  <div id=capsbox style="display:none;margin-top:6px">
   <small style="display:block;margin-bottom:8px">Dein Auto hat uns gesagt, was es kann.
   <b>Hak an, was du im Cockpit haben willst</b> — den Rest siehst du gar nicht erst.</small>
   <div id=capslist></div>
   <small style="display:block;margin-top:8px">Ausgegraute Zeilen kann dein Auto nicht — die
   liegen nicht an uns.<br>
   <b>Aufsperren bieten wir bewusst nicht an</b>, auch wenn dein Auto es könnte: Ein Knopf im
   Browser, der dein Auto öffnet, wäre ein Einbruchswerkzeug für jeden, der an deinen Rechner
   kommt. Zusperren ist dagegen harmlos.</small>
  </div>
  </div>

  <small style="display:block;margin-top:6px">Der <b>Reifendruck-Sollwert</b> steht bei dir im
  <b>Türrahmen der Fahrertür</b> (oft in bar: 2,5 bar = 250 kPa). Trägst du ihn ein, warnt dich das
  Cockpit bei zu wenig Druck. Lässt du das Feld leer, zeigt es den Druck nur an — <b>ich rate den Wert
  bewusst nicht</b>, er hängt an deiner Reifengröße und Beladung.</small>
  <small style="display:block;margin-top:6px">Diese Zahl braucht nur die <b>ehrliche
  Reichweiten-Rechnung</b>. Steht in deinen Fahrzeugpapieren oder im Prospekt. Stimmt sie nicht
  genau, ist das halb so wild — die Reichweite wird dann nur etwas ungenauer.</small>
 </div>
 <div class=nav><button class=sec onclick="go(2)">← Zurück</button><button onclick="go(4)">Weiter →</button></div>
</div>

<!-- ============ 4: AUSSEHEN ============ -->
<div class=pan data-p=4>
 <div class=card>
  <div class=chk>
   <input type=checkbox id=modell3d>
   <div><div class=h>🚗 Dein Auto in 3D</div>
    <small>Lädt einmal das 3D-Modell deines Autos vom Server der BYD-Community (byd.serveone.at). Der Server sieht dabei deine IP-Adresse und welches Modell du fährst. Ohne Haken: neutrale Silhouette oder dein Foto.</small></div>
  </div>
  <label>Foto deines Autos (optional)</label>
  <input type=file id=photofile accept="image/*" onchange="pickphoto(this)">
  <small style="display:block;margin-top:7px">Am schönsten ist ein Foto von <b>deinem eigenen</b>
  Auto — freigestellt vor hellem Hintergrund wirkt es am besten. Bleibt natürlich auch nur auf
  diesem Rechner. Kannst du auch später noch nachreichen.</small>
  <div id=pprev style="margin-top:10px"></div>

  <label style="margin-top:18px">Wie oft soll beim Auto nachgefragt werden?</label>
  <select id=poll>
   <option value="2">alle 2 Minuten — sehr frisch, viele Abfragen</option>
   <option value="5" selected>alle 5 Minuten — empfohlen</option>
   <option value="10">alle 10 Minuten — sparsam</option>
   <option value="15">alle 15 Minuten</option>
   <option value="30">alle 30 Minuten — sehr sparsam</option>
  </select>
  <div class=chk style="margin-top:16px">
   <input type=checkbox checked disabled>
   <div><div class=h>🔔 Bescheid geben, wenn das Laden fertig ist</div>
    <small>Im Cockpit gibt es oben rechts eine <b>Glocke</b> — einmal draufklicken, dann meldet
    dir dein Browser, wenn das Auto fertig geladen hat (und wenn es plötzlich offen ist).<br>
    <b>Nichts zu konfigurieren:</b> Die Meldung entsteht <b>in deinem Browser</b> — kein Telegram,
    kein Konto, es verlässt nichts deinen Rechner.<br>
    <b>Ehrliche Grenze:</b> Es meldet nur, solange die Cockpit-Seite offen ist (ein Hintergrund-Tab
    reicht). Browser zu = keine Meldung.</small></div>
  </div>

  <small style="display:block;margin-top:6px">Gilt, solange das Auto <b>aktiv</b> ist. Steht es länger,
  fragt das Cockpit nur alle 15 Minuten — das schont die 12V-Batterie. Während der Fahrt fragt es
  automatisch öfter.<br>
  <b>Fürs Vorklimatisieren spielt das keine Rolle</b> — das geht jederzeit, auch beim geparkten Auto.</small>
 </div>
 <div class=nav><button class=sec onclick="go(3)">← Zurück</button><button onclick="go(5)">Weiter →</button></div>
</div>

<!-- ============ 5: EXTRAS ============ -->
<div class=pan data-p=5>
 <div class=card>
  <b>Alles hier ist freiwillig.</b> <small>Lass ruhig alles aus — das Cockpit funktioniert komplett
  ohne. Du kannst jederzeit zurückkommen und etwas dazuschalten.</small>

  <div class=chk>
   <input type=checkbox id=price>
   <div><div class=h>💶 Strompreis anzeigen — „wann ist Laden am billigsten?"</div>
    <small>Zeigt den Börsenpreis und die günstigste Stunde. Netzgebühren und Steuern sind nicht
    enthalten. Quelle: aWATTar bzw. energy-charts.info; es werden keine Fahrzeugdaten gesendet.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=chargers>
   <div><div class=h>🔌 Ladesäulen in der Nähe anzeigen</div>
    <small>Zeigt öffentliche Ladestationen am Standort deines Autos mit Entfernung und Steckertyp. Dafür geht die Position deines Autos an OpenStreetMap (Overpass-Dienst) oder an deinen eigenen OpenGlance-Server, wenn du ihn unten einträgst. Mit der Community-Karte kommt die Live-Belegung dazu: dafür geht nur die Kartenmitte, auf etwa 5 km gerundet, an den Server der BYD-Community.</small></div>
  </div>
  <details style="margin:0 0 14px 46px">
   <summary style="cursor:pointer;color:var(--mut);font-size:13px">Eigener OpenGlance-Server</summary>
   <label>Serveradresse</label>
   <input id=chargerurl placeholder="https://dein-server.ts.net:8464">
   <label>Token <small style="text-transform:none;letter-spacing:0">(meist leer; Tailscale meldet dich automatisch an)</small></label>
   <input id=chargertoken type=password placeholder="optional">
  </details>

  <div class=chk>
   <input type=checkbox id=planer onchange="document.getElementById('planerrow').style.display=this.checked?'block':'none'">
   <div><div class=h>🗺️ Mit dem Routenplaner der BYD-Community verbinden</div>
    <small>Dein persönlicher Planer auf byd.serveone.at/ev kennt dann den Ladestand deines Autos und plant
    die Ladestopps damit. Gesendet wird nur der letzte Ladestand, kein Ort. Den persönlichen Link bekommen
    Mitglieder der BYD-Karte (byd.serveone.at) per E-Mail.</small></div>
  </div>
  <div id=planerrow style="display:none;margin:0 0 14px 46px">
   <div style="margin:4px 0 10px"><button type=button onclick="planerVerbinden()">🔗 Mit Routenplaner verbinden</button></div>
   <div id=planerbest style="display:none;border:1px solid #2a4a63;border-radius:14px;padding:12px 14px;margin:8px 0">
    <div class=h>Im Browser bestätigen:</div>
    <div style="margin:6px 0"><span>Code</span> <b id=planercode style="font-size:22px;letter-spacing:.08em;margin-left:6px"></b></div>
    <a id=planerweb target=_blank rel=noopener style="display:inline-block;padding:8px 14px;border-radius:10px;border:1px solid #2a4a63;text-decoration:none;color:#5FD6E6;font-weight:600">Routenplaner öffnen und erlauben</a>
    <small style="display:block;margin-top:8px">Melde dich dort als Mitglied an und tippe auf „Erlauben“. Der Code gilt 10 Minuten.</small>
   </div>
   <details style="margin:6px 0 10px"><summary style="cursor:pointer">Erweitert: mit persönlichem Planer-Link</summary>
    <label>Dein persönlicher Planer-Link</label>
    <input id=planerlink type=password placeholder="https://byd.serveone.at/ev/#z=…">
   </details>
   <div style="margin:10px 0"><button class=sec type=button onclick="planerFz()">🚗 Fahrzeuge aus dem Planer laden</button></div>
   <label>Fahrzeug im Planer</label>
   <select id=planerfz><option value="">– erst Fahrzeuge laden –</option></select>
   <div class=chk style="margin-top:10px">
    <input type=checkbox id=planerfahrten>
    <div><div class=h>Echten Verbrauch lernen</div>
     <small>Deine Fahrten bleiben auf diesem Rechner. Nach jeder Fahrt ohne Laden vergleicht das Cockpit
     deinen Verbrauch mit dem Planer-Modell und schickt nur eine einzige Zahl (deinen Korrekturfaktor).
     Keine Fahrten, keine Orte, keine Uhrzeit. Hast du Panoptes im Auto gekoppelt, macht das Panoptes.</small></div>
   </div>
   <div class=msg id=planermsg></div>
   <small style="display:block;margin-top:6px">💳 Deine Ladekarten wählst du danach im Cockpit unter
   „Routenplaner → Meine Ladekarten“. Gespeichert wird beim Planer nur, welche Karten du hast.</small>
  </div>

  <div class=h style="margin:10px 0 4px">🗺️ Karte</div>
  <small style="display:block;margin-bottom:6px">Wer die Kartenbilder liefert, sieht deine IP-Adresse und die Gegend, die du anschaust. Du entscheidest:</small>
  <div class=chk><input type=radio name=kartenquelle id=kq_keine value=keine checked>
   <div><div class=h>Keine Karte</div><small>Es werden keine Kartenbilder geladen.</small></div></div>
  <div class=chk><input type=radio name=kartenquelle id=kq_osm value=osm>
   <div><div class=h>OpenStreetMap</div><small>Kartenbilder von OpenStreetMap (fremder Dienst).</small></div></div>
  <div class=chk><input type=radio name=kartenquelle id=kq_community value=community>
   <div><div class=h>Community-Karte</div><small>Dieselbe Karte wie im Planer und in der Panoptes-App, vom Server der BYD-Community (byd.serveone.at). Nur damit gibt es die Live-Belegung der Ladesäulen.</small></div></div>

  <div class=chk>
   <input type=checkbox id=lan>
   <div><div class=h>📱 Auch auf Tablet/Handy im Heimnetz öffnen</div>
    <small>Erlaubt den Zugriff von Geräten in deinem eigenen WLAN. Nur in einem vertrauenswürdigen
    Heimnetz einschalten, weil das Cockpit Fahrzeugfunktionen steuern kann.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=ha onchange="document.getElementById('harow').style.display=this.checked?'block':'none'">
   <div><div class=h>🏠 Mit Home Assistant verbinden</div>
    <small>Sendet Fahrzeugdaten und Bedienelemente an Home Assistant. Solarwerte kann das Cockpit
    auch von dort lesen. Für das Senden wird ein MQTT-Broker wie Mosquitto benötigt.</small></div>
  </div>
  <div id=harow style="display:none;margin-top:8px">
   <div style="margin-bottom:10px"><button class=sec type=button onclick="haAuto()">⌕ Home Assistant automatisch finden</button></div>
   <div class=row>
    <div><label>MQTT-Broker (Adresse)</label><input id=hahost placeholder="z.B. 192.168.0.10"></div>
    <div><label>Port</label><input id=haport value="1883"></div>
   </div>
   <div class=row>
    <div><label>Benutzer (falls nötig)</label><input id=hauser placeholder="leer lassen wenn keiner"></div>
    <div><label>Passwort</label><input id=hapass type=password placeholder="leer lassen wenn keins"></div>
   </div>
   <div style="margin-top:10px"><button class=sec onclick="haTest()">🔌 Verbindung testen</button></div>
   <div class=msg id=hamsg></div>
  </div>

  <div class=chk>
   <input type=checkbox id=pv onchange="document.getElementById('pvrow').style.display=this.checked?'block':'none'">
   <div><div class=h>☀️ PV-Leistung aus Home Assistant holen</div>
    <small>Zeigt die aktuelle Solarleistung aus einem Home-Assistant-Sensor – unabhängig vom
    Hersteller deiner PV-Anlage. Der Sensor wird nur gelesen.</small></div>
  </div>
  <div id=pvrow style="display:none;margin-top:8px">
   <label>Adresse deines Home Assistant</label>
   <input id=pvurl placeholder="z.B. http://192.168.0.10:8123">
   <label>Zugriffs-Token <small style="text-transform:none;letter-spacing:0">(in HA: unten links auf deinen Namen → Sicherheit → ganz unten „Long-Lived Access Token" → Token erstellen)</small></label>
   <input id=pvtoken type=password placeholder="den langen Text hier einfügen">
   <div style="margin-top:10px"><button class=sec onclick="pvLaden()">🔍 Meine Sensoren laden</button></div>
   <div class=msg id=pvmsg></div>
   <div id=pvpick style="display:none">
    <label>Welcher Sensor ist deine PV-Leistung?</label>
    <select id=pventity></select>
    <small style="display:block;margin-top:6px">Meist heißt er „PV Leistung", „Solar Power" o.ä.
    Nimm den, der die <b>aktuelle Erzeugung in Watt</b> zeigt.</small>
   </div>
  </div>


  <div class=chk>
   <input type=checkbox id=sentry onchange="document.getElementById('adbrow').style.display=this.checked?'block':'none'">
   <div><div class=h>🎥 Wächter-Kamera (optional)</div>
    <small>Das Cockpit prüft selbst, ob <b>adb</b> und ein verbundenes Auto gefunden werden.
    Panoptes- (früher SurfMate) oder Overdrive-App, USB-Stick und kabelloses ADB müssen im Auto bereits eingerichtet sein.</small>
    <div class=msg id=adbstatus>Prüfe Voraussetzungen …</div></div>
  </div>
  <div id=adbrow style="display:none;margin-top:8px">
   <label>adb-Adresse des Autos (z.B. 192.168.0.50:5555)</label>
   <input id=caradb placeholder="IP:Port">
  </div>

  <div class=chk>
   <input type=checkbox id=upd>
   <div><div class=h>🔔 Auf neue Versionen hinweisen</div>
    <small>Prüft einmal täglich die aktuelle Versionsnummer. Es werden dabei keine Fahrzeugdaten
    oder Kennungen gesendet.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=count>
   <div><div class=h>📊 Anonym mitzählen, dass ich das Tool nutze</div>
    <small>Sendet einmal täglich eine zufällige Installations-ID, Version und Modell. Niemals Name,
    E-Mail, VIN, Standort oder Fahrdaten. Ohne Haken wird nichts gesendet.</small></div>
  </div>
 </div>

 <div class=nav><button class=sec onclick="go(4)">← Zurück</button>
  <button onclick="save()">✅ Fertig — Cockpit starten</button></div>
 <div class=msg id=smsg></div>

 <div class=card id=logoutbox style="display:none;margin-top:18px">
  <div style="color:var(--mut);font-size:12px;letter-spacing:1px;margin-bottom:8px">ABMELDEN</div>
  <small>Löscht deine BYD-Zugangsdaten, die gespeicherten Fahrzeugdaten und dein Foto
  <b>von diesem Rechner</b>. Dein BYD-Konto selbst bleibt unangetastet.</small>
  <div style="margin-top:12px"><button class=sec style="border-color:rgba(255,120,90,.5);color:#FF8A6B"
   onclick="logout()">🚪 Abmelden & Daten löschen</button></div>
  <div class=msg id=lmsg></div>
 </div>
</div>

<div style="text-align:center;margin-top:20px">
 <a href="/about" style="color:var(--mut);font-size:13px">Impressum · Haftungsausschluss · Datenschutz</a>
</div>
</div>
<script>
const KWH=__KWHMAP__, VOR=__VOR__;
let SCHRITT=1;
const TITEL={1:['Bevor es losgeht','Ein Punkt ist wirklich wichtig — bitte kurz lesen.'],
 2:['Deine Datenquelle','Woher kommen die Werte deines Autos?'],
 3:['Dein Auto','Welches Fahrzeug, und wie groß ist der Akku?'],
 4:['Dein Cockpit','Ein Foto und wie oft nachgefragt wird.'],
 5:['Extras','Alles freiwillig — lass ruhig alles aus.']};
function quelle(){const x=document.querySelector('input[name=quelle]:checked');return x?x.value:'byd';}
// Quellenwahl: passende Felder zeigen; BYD-Konto ist bei HA/Panoptes nur optional (fuer Fernbefehle)
function quelleUm(){const q=quelle();
 document.getElementById('srcha').style.display=q==='ha'?'block':'none';
 document.getElementById('srcpan').style.display=q==='panoptes'?'block':'none';
 document.getElementById('panoptes').checked=q==='panoptes';
 const w=document.getElementById('srcbydwrap');
 if(q==='byd'){w.open=true;document.getElementById('srcbydsum').textContent=__T('BYD-Konto');}
 else{document.getElementById('srcbydsum').textContent=__T('Optional: BYD-Konto für Fernbefehle (Klima, Zusperren)');
  if(!document.getElementById('username').value)w.open=false;}
 n2pruefen();}
let HA_OK=false, PAN_OK=false;
function n2pruefen(){const q=quelle(), v=!!document.getElementById('vin').value;
 document.getElementById('n2').disabled=!(q==='byd'?v:(q==='ha'?HA_OK:PAN_OK));}
function go(n){
 if(n===3&&quelle()==='byd'&&!document.getElementById('vin').value){
  document.getElementById('dmsg').textContent='⚠️ Bitte zuerst „Meine Fahrzeuge abrufen" drücken.';return;}
 if(n===3){const ohne=!document.getElementById('vin').value;
  document.getElementById('vinwrap').style.display=ohne?'none':'block';
  document.getElementById('capswrap').style.display=document.getElementById('username').value?'block':'none';}
 SCHRITT=n;
 document.querySelectorAll('.pan').forEach(p=>p.classList.toggle('on',+p.dataset.p===n));
 document.querySelectorAll('.dot2').forEach(d=>{const k=+d.dataset.d;
  d.classList.toggle('on',k===n); d.classList.toggle('done',k<n);
  d.querySelector('i').textContent = k<n ? '✓' : k;});
 document.getElementById('wtitle').textContent=TITEL[n][0];
 document.getElementById('wsub').textContent=TITEL[n][1];
 window.scrollTo({top:0,behavior:'smooth'});
}
let KWH_HAND=false;
function setkwh(){KWH_HAND=false;document.getElementById('kwh').value=KWH[document.getElementById('model').value]||60;}
function body(){return {username:username.value.trim(),password:password.value,control_pin:pin.value.trim(),
 country_code:country.value,time_zone:tz.value,language:'de'};}
// Bestehende Einstellungen zurueckschreiben, damit man z.B. nur ein Foto nachreichen kann.
function vorfuellen(){
 if(!VOR||!VOR.vin) return;
 // Schon eingerichtet -> der Nutzer will nur etwas aendern.
 // Nicht wieder bei Schritt 1 aufhalten und Weiter nicht sperren.
 document.getElementById('ack').checked=true;
 document.getElementById('n1').disabled=false;
 document.getElementById('n2').disabled=false;
 document.getElementById('logoutbox').style.display='block';
 if(VOR.username) username.value=VOR.username;
 if(VOR.country_code) country.value=VOR.country_code;
 if(VOR.time_zone) tz.value=VOR.time_zone;
 if(VOR.model){const m=document.getElementById('model');
  if([...m.options].some(o=>o.value===VOR.model)) m.value=VOR.model;}
 if(VOR.battery_kwh) document.getElementById('kwh').value=VOR.battery_kwh;
 if(String(VOR.battery_quelle||'').indexOf('Panoptes')===0){
  document.getElementById('kwhlbl').innerHTML=__T('Akku nutzbar in kWh')+' — <b>'+__T('geschätzt von Panoptes')+'</b> ('+__T('Nennkapazität × Akku-Gesundheit')+')';
  if(VOR.battery_schaetzung&&VOR.battery_nenn&&VOR.battery_schaetzung>VOR.battery_nenn){const h=document.getElementById('kwhhinweis');h.style.display='block';
   h.textContent=(window.__LANG__==='en'?'Panoptes estimates '+VOR.battery_schaetzung+' kWh, more than the nominal capacity of your model ('+VOR.battery_nenn+' kWh). The cockpit uses '+VOR.battery_nenn+' kWh.':
    'Panoptes schätzt '+String(VOR.battery_schaetzung).replace('.',',')+' kWh, mehr als die Nennkapazität deines Modells ('+String(VOR.battery_nenn).replace('.',',')+' kWh). Das Cockpit rechnet mit '+String(VOR.battery_nenn).replace('.',',')+' kWh.');}}
 else if(VOR.battery_quelle==='manuell'){
  document.getElementById('kwhlbl').innerHTML=__T('Akku nutzbar in kWh')+' — <b>'+__T('von dir eingetragen')+'</b>';}
 else if(VOR.panoptes){document.getElementById('kwhauto').style.display='block';}
 if(VOR.tyre_target) document.getElementById('tyretarget').value=VOR.tyre_target;
 if(VOR.features){document.getElementById('capsmsg').textContent=
   'ℹ️ Deine Auswahl ist gespeichert. Erneut abfragen, um sie zu ändern.';}
 if(VOR.poll_min) document.getElementById('poll').value=String(VOR.poll_min);
 document.getElementById('lan').checked=!!VOR.lan;
 document.getElementById('count').checked=!!VOR.count_optin;
 document.getElementById('upd').checked=!!VOR.update_check;
 document.getElementById('price').checked=!!VOR.show_price;
 document.getElementById('chargers').checked=!!VOR.show_chargers;
 document.getElementById('chargerurl').value=VOR.charger_url||'';
 const q0=VOR.datenquelle||(VOR.panoptes?'panoptes':'byd');
 document.getElementById(q0==='ha'?'q_ha':(q0==='panoptes'?'q_pan':'q_byd')).checked=true;
 document.getElementById('hasrcurl').value=VOR.ha_src_url||'';
 if(VOR.has_ha_src_token) document.getElementById('hasrctoken').placeholder='••••••• (gespeichert — leer lassen zum Behalten)';
 HA_OK=!!(VOR.ha_src_map&&VOR.ha_src_map.soc); PAN_OK=!!VOR.panoptes;
 if(q0==='ha'&&HA_OK) haSuchen();
 document.getElementById('panoptesurl').value=VOR.panoptes_url||'';
 if(VOR.has_panoptes_code) document.getElementById('panoptescode').placeholder='••••••• (gespeichert — leer lassen zum Behalten)';
 if(VOR.has_panoptes_jwt&&VOR.panoptes) document.getElementById('panoptesmsg').textContent='✅ '+__T('Schon gekoppelt. Nur neu verbinden, wenn die Kopplung in Panoptes entfernt wurde.');
 if(VOR.planer_geraet) document.getElementById('planermsg').textContent='✅ '+__T('Mit dem Routenplaner verbunden');
 if(VOR.disclaimer_ok){document.getElementById('disc').checked=true;}
 document.getElementById('planer').checked=!!VOR.planer;
 document.getElementById('planerrow').style.display=VOR.planer?'block':'none';
 document.getElementById('planerfahrten').checked=!!VOR.planer_fahrten;
 {const q=['community','osm'].includes(VOR.kartenquelle)?VOR.kartenquelle:'keine';document.getElementById('kq_'+q).checked=true;}
 document.getElementById('modell3d').checked=VOR.modell3d===true;
 if(VOR.has_planer_token) document.getElementById('planerlink').placeholder='••••••• (gespeichert — leer lassen zum Behalten)';
 if(VOR.planer_fahrzeug){const o=document.createElement('option');o.value=o.textContent=VOR.planer_fahrzeug;o.selected=true;
  document.getElementById('planerfz').appendChild(o);}
 if(VOR.has_charger_token) document.getElementById('chargertoken').placeholder='••••••• (gespeichert — leer lassen zum Behalten)';
 if(VOR.pv){document.getElementById('pv').checked=true;
  document.getElementById('pvrow').style.display='block';
  document.getElementById('pvurl').value=VOR.pv_url||'';
  if(VOR.pv_entity){const s2=document.getElementById('pventity');
   s2.innerHTML='<option value="'+VOR.pv_entity+'">'+VOR.pv_entity+' (gespeichert)</option>';
   document.getElementById('pvpick').style.display='block';}
  document.getElementById('pvtoken').placeholder='••••••• (gespeichert — leer lassen zum Behalten)';}
 if(VOR.ha){document.getElementById('ha').checked=true;
  document.getElementById('harow').style.display='block';
  document.getElementById('hahost').value=VOR.ha_host||'';
  document.getElementById('haport').value=VOR.ha_port||1883;
  document.getElementById('hauser').value=VOR.ha_user||'';}
 if(VOR.sentry){document.getElementById('sentry').checked=true;
  document.getElementById('adbrow').style.display='block';
  document.getElementById('caradb').value=VOR.car_adb||'';}
 // VIN als bekannte Auswahl anbieten, ohne dass man neu abrufen muss
 const s=document.getElementById('vin');
 s.innerHTML='<option value="'+VOR.vin+'">'+VOR.vin+' (gespeichert)</option>';
 if(VOR.has_pw) password.placeholder='••••••• (gespeichert — leer lassen zum Behalten)';
 if(VOR.has_photo) document.getElementById('pprev').innerHTML=
   '<img src="/photo?t='+Date.now()+'" style="max-height:130px;border-radius:12px;border:1px solid rgba(160,230,240,.18)"><br><small>Aktuelles Foto — neues wählen zum Ersetzen</small>';
 document.getElementById('smsg').textContent='ℹ️ Deine Einstellungen sind vorausgefüllt. Ändere, was du willst, und speichere.';
}
async function logout(){
 if(!confirm('Wirklich abmelden? Zugangsdaten, Fahrzeugdaten und Foto werden von diesem Rechner gelöscht.')) return;
 const m=document.getElementById('lmsg'); m.textContent='⏳ Lösche …';
 try{const r=await (await fetch('/logout',{method:'POST'})).json();
  m.textContent=r.ok?'✅ Abgemeldet. Alles gelöscht.':'⚠️ '+r.error;
  if(r.ok) setTimeout(()=>location.reload(),1400);
 }catch(e){m.textContent='⚠️ '+e}}
let CAPS = null;
async function capsLaden(){
 const m=document.getElementById('capsmsg');
 const vin=document.getElementById('vin').value;
 if(!vin){m.textContent='⚠️ Bitte zuerst in Schritt 2 die Fahrzeuge abrufen.';return;}
 m.textContent='⏳ Frage dein Auto …';
 try{
  const b=body(); b.vin=vin;
  const r=await (await fetch('/caps',{method:'POST',body:JSON.stringify(b)})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;if(r.auth_blocked)document.getElementById('capsbtn').disabled=true;return;}
  CAPS=r.features;
  const box=document.getElementById('capslist');
  box.innerHTML=r.features.map(f=>
    '<div class=chk style="'+(f.kann?'':'opacity:.4')+'">'+
    '<input type=checkbox class=capchk data-k="'+f.key+'"'+(f.an?' checked':'')+(f.kann?'':' disabled')+'>'+
    '<div><div class=h style="font-weight:400">'+f.text+'</div>'+
    (f.kann?'':'<small>Dein Auto kann das nicht.</small>')+'</div></div>').join('');
  document.getElementById('capsbox').style.display='block';
  const n=r.features.filter(f=>f.kann).length;
  m.textContent=__T('✅ Dein Auto kann ')+n+__T(' von ')+r.features.length+__T(' Dingen.');
 }catch(e){m.textContent='⚠️ '+e}}
async function pvLaden(){const m=document.getElementById('pvmsg');
 const u=document.getElementById('pvurl').value.trim(), t=document.getElementById('pvtoken').value.trim();
 if(!u||!t){m.textContent='⚠️ Bitte Adresse und Token eintragen.';return;}
 m.textContent='⏳ Frage dein Home Assistant …';
 try{const r=await (await fetch('/pv_entities',{method:'POST',body:JSON.stringify({pv_url:u,pv_token:t})})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  const s=document.getElementById('pventity'); s.innerHTML='';
  r.entities.forEach(e=>{const o=document.createElement('option');o.value=e.id;
   o.textContent=e.name+' — '+e.state+' '+e.unit+'  ('+e.id+')';s.appendChild(o);});
  // Vorschlag: nach Erzeugung suchen — aber Verbrauch/Netz/Wallbox/Ueberschuss AUSSCHLIESSEN.
  // (Sonst schlaegt er z.B. "Strom & PV Haushalt" vor, nur weil "PV" im Namen steht —
  //  das waere der Hausverbrauch, als Solar-Erzeugung gezeigt. Falsche Zahl > keine Zahl.)
  const erzeugung=/pv|solar|erzeug|produc/i;
  const nicht=/last|load|haushalt|verbrauch|consum|bezug|grid|netz|wallbox|charger|lade|ueberschuss|überschuss|surplus|batt|speicher|export|import/i;
  const tipp=r.entities.find(e=>erzeugung.test(e.name+' '+e.id) && !nicht.test(e.name+' '+e.id));
  if(tipp) s.value=tipp.id;
  document.getElementById('pvpick').style.display='block';
  m.textContent='✅ '+r.entities.length+__T(' Leistungs-Sensoren gefunden — wähl deinen PV-Sensor aus.');
 }catch(e){m.textContent='⚠️ '+e}}
async function haAuto(){const m=document.getElementById('hamsg');m.textContent='⌛ Suche Home Assistant im Heimnetz …';
 try{const r=await fetch('/energy/discover',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
  const d=await r.json();if(!r.ok)throw Error(d.error||'Suche fehlgeschlagen');
  const ha=(d.found||[]).find(x=>x.vendor==='Home Assistant');
  if(!ha){m.textContent='Kein Home Assistant automatisch gefunden. Die Adresse kann unten weiterhin manuell eingetragen werden.';return;}
  document.getElementById('hahost').value=ha.ip;document.getElementById('pvurl').value='http://'+ha.ip+':'+(ha.port||8123);
  document.getElementById('pv').checked=true;document.getElementById('pvrow').style.display='block';
  m.textContent='✓ Home Assistant gefunden · Für Fahrzeugdaten MQTT prüfen, für Solar nur noch den Zugriffstoken eintragen.';
 }catch(e){m.textContent='⚠️ '+e.message;}}
async function localCapabilities(){const status=document.getElementById('adbstatus'),check=document.getElementById('sentry');
 try{const d=await (await fetch('/local/capabilities')).json();
  if(!d.adb_installed){check.checked=false;check.disabled=true;document.getElementById('adbrow').style.display='none';status.textContent='Nicht verfügbar: adb ist auf diesem PC nicht installiert.';return;}
  if(d.adb_devices&&d.adb_devices.length===1){if(!document.getElementById('caradb').value)document.getElementById('caradb').value=d.adb_devices[0];status.textContent='✓ adb und ein verbundenes Auto wurden gefunden.';}
  else{status.textContent='adb ist installiert. Das Auto wurde noch nicht eindeutig gefunden; die Adresse kann unten eingetragen werden.';}
 }catch(e){status.textContent='Die Voraussetzungen konnten nicht automatisch geprüft werden.';}}
async function haTest(){const m=document.getElementById('hamsg');
 const h=document.getElementById('hahost').value.trim();
 if(!h){m.textContent='⚠️ Bitte zuerst die Broker-Adresse eintragen.';return;}
 m.textContent='⏳ Verbinde …';
 try{const r=await (await fetch('/ha_test',{method:'POST',body:JSON.stringify({
   ha_host:h, ha_port:parseInt(document.getElementById('haport').value,10)||1883,
   ha_user:document.getElementById('hauser').value.trim(),
   ha_pass:document.getElementById('hapass').value})})).json();
  m.textContent=r.ok?'✅ Broker erreicht — dein Auto erscheint gleich in Home Assistant.':'⚠️ '+r.error;
 }catch(e){m.textContent='⚠️ '+e}}
async function detect(){const m=document.getElementById('dmsg');m.textContent='⏳ Melde mich bei BYD an …';
 const button=document.getElementById('detectbtn');button.disabled=true;
 try{const r=await (await fetch('/detect',{method:'POST',body:JSON.stringify(body())})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;if(!r.auth_blocked)button.disabled=false;return;}
  const s=document.getElementById('vin');s.innerHTML='';
  r.vehicles.forEach(v=>{const o=document.createElement('option');o.value=v.vin;o.textContent=(v.name?v.name+' — ':'')+v.vin;s.appendChild(o);});
  m.textContent='✅ '+r.vehicles.length+__T(' Fahrzeug(e) gefunden — weiter unten mit Weiter');
  n2pruefen();button.disabled=false;
 }catch(e){m.textContent='⚠️ Fehler: '+e;button.disabled=false;}}
let PHOTO='';
function pickphoto(inp){const f=inp.files[0];if(!f)return;
 const r=new FileReader();
 r.onload=e=>{const img=new Image();
  img.onload=()=>{ // auf max 1100px runterrechnen -> aus 4MB-Handyfoto werden ~200KB
   const mx=1100,sc=Math.min(1,mx/Math.max(img.width,img.height));
   const c=document.createElement('canvas');c.width=Math.round(img.width*sc);c.height=Math.round(img.height*sc);
   c.getContext('2d').drawImage(img,0,0,c.width,c.height);
   PHOTO=c.toDataURL('image/jpeg',0.86);
   document.getElementById('pprev').innerHTML='<img src="'+PHOTO+'" style="max-height:130px;border-radius:12px;border:1px solid rgba(160,230,240,.18)">';
  };img.src=e.target.result;};
 r.readAsDataURL(f);}
const HA_FELDER=[['soc','Ladestand (Pflicht)'],['range_km','Reichweite'],['odometer','Kilometerstand'],
 ['charging','Lädt gerade'],['location','Standort']];
async function haSuchen(){const m=document.getElementById('hasrcmsg'), box=document.getElementById('hasrcpick');
 m.textContent=__T('⏳ Frage Home Assistant …');
 try{const r=await (await fetch('/haquelle/vorschlag',{method:'POST',body:JSON.stringify({
    url:document.getElementById('hasrcurl').value.trim(), token:document.getElementById('hasrctoken').value.trim()})})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;HA_OK=false;n2pruefen();return;}
  box.innerHTML=HA_FELDER.map(([f,t])=>{const x=r.felder[f]||{kandidaten:[]};
   return '<label>'+esc(__T(t))+'</label><select class=hasel data-f="'+f+'" onchange="haPruefen()"><option value="">'+
    esc(__T('— nicht verwenden —'))+'</option>'+x.kandidaten.map(k=>'<option value="'+esc(k.id)+'"'+(k.id===x.wahl?' selected':'')+'>'+
    esc(k.name)+' ('+esc(String(k.wert))+')</option>').join('')+'</select>';}).join('')+
   '<small style="display:block;margin-top:8px">'+esc(__T('Vorausgewählt ist, was nach deinem Auto aussieht. Bitte kurz prüfen — die Zahl in Klammern ist der aktuelle Wert.'))+'</small>';
  box.style.display='block';
  const n=HA_FELDER.filter(([f])=>(r.felder[f]||{}).wahl).length;
  m.textContent=n?('✅ '+n+__T(' Werte deines Autos gefunden.')):('⚠️ '+__T('Nichts gefunden, das sicher nach deinem Auto aussieht — bitte unten selbst auswählen.'));
  haPruefen();
 }catch(e){m.textContent='⚠️ '+e;HA_OK=false;n2pruefen();}}
function haPruefen(){const s=document.querySelector('.hasel[data-f=soc]');HA_OK=!!(s&&s.value);n2pruefen();}
function haMap(){const z={};document.querySelectorAll('.hasel').forEach(s=>{if(s.value)z[s.dataset.f]=s.value;});return z;}
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function schritt1(){const ok=document.getElementById('disc').checked&&document.getElementById('ack').checked;
 document.getElementById('n1').disabled=!ok;
 document.getElementById('discmsg').textContent=document.getElementById('disc').checked?'':__T('Bitte bestätige die Hinweise, um fortzufahren.');}
let PAN_POLL=null, PLANER_POLL=null;
async function panoptesAnfrage(){const m=document.getElementById('panoptesmsg'),b=document.getElementById('panoptesbest');
 clearTimeout(PAN_POLL); b.style.display='none'; m.textContent=__T('⏳ Frage das Auto …');
 try{const r=await (await fetch('/panoptes/anfrage',{method:'POST',body:JSON.stringify({
    url:document.getElementById('panoptesurl').value.trim()})})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  m.textContent='⏳ '+__T('Warte auf „Erlauben“ …');
  document.getElementById('panpz').textContent=r.pruefzahl;
  document.getElementById('pangeraet').textContent=r.geraet;
  document.getElementById('panweb').href=r.webseite; b.style.display='block';
  PAN_POLL=setTimeout(panoptesWarte,2000);
 }catch(e){m.textContent='⚠️ '+e}}
async function panoptesWarte(){const m=document.getElementById('panoptesmsg'),b=document.getElementById('panoptesbest');
 try{const r=await (await fetch('/panoptes/anfrage/status',{method:'POST',body:'{}'})).json();
  if(r.ok&&r.status==='wartet'){PAN_POLL=setTimeout(panoptesWarte,2000);return;}
  b.style.display='none';
  if(r.ok&&r.status==='erlaubt'){m.textContent='✅ '+__T('Verbunden')+(r.soc!=null?' — '+__T('Ladestand ')+r.soc+' %':'');
   if(r.url)document.getElementById('panoptesurl').value=r.url;
   PAN_OK=true; n2pruefen(); return;}
  m.textContent='⚠️ '+(r.error||r.status);
 }catch(e){PAN_POLL=setTimeout(panoptesWarte,3000);}}
async function planerVerbinden(){const m=document.getElementById('planermsg'),b=document.getElementById('planerbest');
 clearTimeout(PLANER_POLL); b.style.display='none'; m.textContent=__T('⏳ Frage den Planer …');
 try{const r=await (await fetch('/planer/verbinden',{method:'POST',body:'{}'})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  m.textContent='⏳ '+__T('Warte auf „Erlauben“ …');
  document.getElementById('planercode').textContent=r.code;
  document.getElementById('planerweb').href=r.link; b.style.display='block';
  PLANER_POLL=setTimeout(planerWarte,3000);
 }catch(e){m.textContent='⚠️ '+e}}
async function planerWarte(){const m=document.getElementById('planermsg'),b=document.getElementById('planerbest');
 try{const r=await (await fetch('/planer/verbinden/status',{method:'POST',body:'{}'})).json();
  if(r.ok&&r.status==='wartet'){PLANER_POLL=setTimeout(planerWarte,3000);return;}
  b.style.display='none';
  if(r.ok&&r.status==='erlaubt'){m.textContent='✅ '+__T('Mit dem Routenplaner verbunden');planerFz();return;}
  m.textContent='⚠️ '+(r.error||r.status);
 }catch(e){PLANER_POLL=setTimeout(planerWarte,4000);}}
async function panoptesTest(){const m=document.getElementById('panoptesmsg');
 m.textContent=__T('⏳ Frage das Auto …');
 try{const r=await (await fetch('/panoptes/test',{method:'POST',body:JSON.stringify({
    url:document.getElementById('panoptesurl').value.trim(), code:document.getElementById('panoptescode').value.trim()})})).json();
  m.textContent=r.ok?('✅ '+__T('Verbunden — Ladestand ')+r.soc+' %'):('⚠️ '+r.error);
  if(r.ok&&r.url)document.getElementById('panoptesurl').value=r.url;
  PAN_OK=!!r.ok; n2pruefen();
 }catch(e){m.textContent='⚠️ '+e}}
async function planerFz(){const m=document.getElementById('planermsg'), sel=document.getElementById('planerfz');
 m.textContent=__T('⏳ Frage den Planer …');
 try{const r=await (await fetch('/planer/fahrzeuge',{method:'POST',body:JSON.stringify({
    link:document.getElementById('planerlink').value.trim(), model:document.getElementById('model').value,
    battery_kwh:parseFloat(document.getElementById('kwh').value)||0})})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  const alt=sel.value; sel.innerHTML='';
  r.fahrzeuge.forEach(f=>{const o=document.createElement('option');o.value=o.textContent=f.name;sel.appendChild(o);});
  sel.value=alt&&r.fahrzeuge.some(f=>f.name===alt)?alt:(r.vorschlag||(r.fahrzeuge[0]||{}).name||'');
  m.textContent='✅ '+r.fahrzeuge.length+__T(' Fahrzeuge gefunden — passendes ist vorausgewählt.');
 }catch(e){m.textContent='⚠️ '+e}}
async function save(){const m=document.getElementById('smsg');
 const b=body(); b.vin=document.getElementById('vin').value; b.battery_kwh=parseFloat(document.getElementById('kwh').value);
 b.battery_kwh_hand=KWH_HAND;
 b.model=document.getElementById('model').value; b.photo_data=PHOTO;
 b.tyre_target=parseFloat(document.getElementById('tyretarget').value)||null;
 b.features={}; document.querySelectorAll('.capchk').forEach(c=>{
  b.features[c.dataset.k]= c.checked && !c.disabled; });
 b.lan=document.getElementById('lan').checked;
 b.update_check=document.getElementById('upd').checked;
 b.count_optin=document.getElementById('count').checked;
 b.show_price=document.getElementById('price').checked;
 b.poll_min=parseInt(document.getElementById('poll').value,10);
 b.show_chargers=document.getElementById('chargers').checked;
 b.charger_url=document.getElementById('chargerurl').value.trim();
 b.charger_token=document.getElementById('chargertoken').value.trim();
 b.planer=document.getElementById('planer').checked;
 b.planer_link=document.getElementById('planerlink').value.trim();
 b.disclaimer_ok=document.getElementById('disc').checked;
 b.planer_fahrzeug=document.getElementById('planerfz').value;
 b.planer_fahrten=document.getElementById('planerfahrten').checked;
 b.kartenquelle=(document.querySelector('input[name=kartenquelle]:checked')||{}).value||'keine';
 b.karte=b.kartenquelle==='community'?'community':'osm';
 b.modell3d=document.getElementById('modell3d').checked;
 b.panoptes=document.getElementById('panoptes').checked;
 b.panoptes_url=document.getElementById('panoptesurl').value.trim();
 b.panoptes_code=document.getElementById('panoptescode').value.trim();
 b.pv=document.getElementById('pv').checked;
 b.pv_url=document.getElementById('pvurl').value.trim();
 b.pv_token=document.getElementById('pvtoken').value.trim();
 b.pv_entity=document.getElementById('pventity').value;
 b.ha=document.getElementById('ha').checked;
 b.ha_host=document.getElementById('hahost').value.trim();
 b.ha_port=parseInt(document.getElementById('haport').value,10)||1883;
 b.ha_user=document.getElementById('hauser').value.trim();
 b.ha_pass=document.getElementById('hapass').value;
 b.datenquelle=quelle();
 b.ha_src_url=document.getElementById('hasrcurl').value.trim();
 b.ha_src_token=document.getElementById('hasrctoken').value.trim();
 b.ha_src_map=haMap();
 b.sentry=document.getElementById('sentry').checked;
 b.car_adb=document.getElementById('caradb').value.trim();
 if(!b.vin&&b.datenquelle==='byd'){m.textContent='⚠️ Bitte erst Fahrzeuge abrufen und eins auswählen';return;}
 m.textContent='⏳ Speichere …';
 try{const r=await (await fetch('/save',{method:'POST',body:JSON.stringify(b)})).json();
  if(r.ok){m.innerHTML=b.lan?'✅ Gespeichert — Cockpit startet …<br><small>Für den Tablet-Zugriff das Programm einmal neu starten.</small>'
                            :'✅ Gespeichert — Cockpit startet …';
   setTimeout(()=>location.href='/',b.lan?3200:1600);}
  else m.textContent='⚠️ '+r.error;}catch(e){m.textContent='⚠️ '+e}}
setkwh(); vorfuellen(); quelleUm(); localCapabilities();
</script></body></html>"""


# ---------------------------------------------------------------- Cockpit (HTML)
COCKPIT = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit</title>
<script type=importmap>{"imports":{"three":"/static/three/three.module.min.js"}}</script>
<link rel=stylesheet href="/static/leaflet.css">
<style>
:root{--blue:#5FD6E6;--cyan:#43c9db;--txt:#EAF6F8;--mut:#A9C7CE;--line:rgba(160,230,240,.16)}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:radial-gradient(1100px 720px at 50% -8%,#0d3a4a 0%,#071a2b 55%,#04101b 100%) fixed;
 color:var(--txt);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:22px}
.wrap{max-width:1040px;margin:0 auto}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.brand{color:var(--mut);letter-spacing:4px;font-weight:700;font-size:13px}
.on{color:var(--mut);font-size:12px;display:flex;align-items:center;gap:7px}
.dot{width:9px;height:9px;border-radius:50%;background:#B5F23D;box-shadow:0 0 10px #B5F23D}.dot.off{background:#5a6b7d;box-shadow:none}
.hero{display:grid;grid-template-columns:280px 1fr;gap:12px;align-items:center;margin:6px 0 16px}
.ring{position:relative;width:250px;height:250px;margin:0 auto}
svg.ring{transform:rotate(-90deg)}
.ring .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring .pct{font-size:64px;font-weight:300;line-height:1}.ring .pct small{font-size:22px;color:var(--mut)}
.ring .lbl{color:var(--mut);font-size:12px;letter-spacing:2px;margin-top:4px}
.range{text-align:center;margin-top:8px}.range b{font-size:28px;font-weight:300}.range b small{font-size:16px;color:var(--mut)}
.range .lbl{color:var(--mut);font-size:11px;letter-spacing:2px}
.car{display:flex;align-items:center;justify-content:center;min-height:250px}
.lackwahl{display:flex;gap:8px;justify-content:center;margin:8px 0 2px}.lackwahl button{width:22px;height:22px;border-radius:50%;
 border:2px solid rgba(234,246,248,.55);cursor:pointer;padding:0}
.car img{max-width:100%;max-height:250px;filter:drop-shadow(0 24px 40px rgba(95,214,230,.35))}
.car svg{max-width:100%;max-height:210px;filter:drop-shadow(0 22px 38px rgba(95,214,230,.4))}
.car .hint{margin-top:12px;text-align:center}
.car .hint a,.car .hint button{color:var(--mut);font-size:12px;text-decoration:none;border:1px solid var(--line);background:transparent;cursor:pointer;
 border-radius:20px;padding:7px 14px;display:inline-block;transition:.15s}
.car .hint a:hover,.car .hint button:hover{color:var(--txt);border-color:rgba(160,230,240,.4);background:rgba(255,255,255,.04)}
.car .wrap{display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%}
.car .ph{color:var(--mut);font-size:13px;text-align:center;opacity:.6}
.sect{color:var(--mut);letter-spacing:2px;font-size:11px;font-weight:700;margin:18px 4px 8px}
.grid{display:grid;gap:12px}
.tile{background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:1px solid var(--line);
 border-radius:18px;padding:15px 17px;backdrop-filter:blur(14px)}
.tile .k{color:var(--mut);font-size:11px;letter-spacing:2px}
.tile .v{font-size:25px;font-weight:300;margin-top:5px}.tile .v small{font-size:13px;color:var(--mut)}
.klima{display:flex;gap:12px;margin-top:8px;flex-wrap:wrap}
.pill{flex:1;min-width:110px;border:1px solid var(--line);border-radius:26px;padding:14px;text-align:center;font-weight:600;
 font-size:15px;cursor:pointer;background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.02));color:var(--mut);user-select:none;transition:.15s}
.pill:active{transform:scale(.97)}
.pill.heat.on{background:rgba(255,90,70,.16);border-color:rgba(255,120,90,.55);color:#FF8A6B;box-shadow:0 0 22px rgba(255,90,70,.25)}
.pill.batt.on{background:rgba(255,90,70,.16);border-color:rgba(255,120,90,.55);color:#FF8A6B;box-shadow:0 0 22px rgba(255,90,70,.25)}
.pill.cool.on{background:rgba(95,214,230,.16);border-color:rgba(90,180,255,.55);color:#5FD6E6;box-shadow:0 0 22px rgba(95,214,230,.28)}
.msg{color:var(--mut);font-size:12.5px;min-height:18px;margin:8px 2px;text-align:center}
.chips{display:flex;gap:10px;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:16px;padding:8px 14px;font-size:13px;background:rgba(255,255,255,.03)}
.chip .cm{color:var(--mut)}.okc{color:#B5F23D}.no{color:#A9C7CE}.warnc{color:#FFC266}
.bars{display:flex;align-items:flex-end;gap:3px;height:110px;margin-top:12px;padding:12px 10px 0;
 background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02));border:1px solid var(--line);border-radius:16px}
.bar{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;position:relative}
.bar i{display:block;width:100%;border-radius:4px 4px 0 0;background:rgba(160,230,240,.35);transition:.2s}
.bar.now i{background:linear-gradient(180deg,#43c9db,#5FD6E6);box-shadow:0 0 12px rgba(95,214,230,.6)}
.bar.cheap i{background:linear-gradient(180deg,#B5F23D,#8fcf2a);box-shadow:0 0 12px rgba(91,227,163,.5)}
.bar b{font-size:9px;color:var(--mut);margin-top:4px;font-weight:400}
.bar.now b,.bar.cheap b{color:var(--txt);font-weight:700}
.bar span.t{position:absolute;top:-13px;font-size:9px;color:var(--mut);white-space:nowrap}
.chg{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 13px;
 border-bottom:1px solid rgba(160,230,240,.10)}
.chg:last-child{border-bottom:0}
.chg .nm{font-size:14px}.chg .sub{color:var(--mut);font-size:11.5px;margin-top:2px}
.chg .km{color:var(--cyan);font-size:15px;white-space:nowrap;font-weight:300}
.chg a{color:inherit;text-decoration:none}
.map{border:1px solid var(--line);border-radius:18px;overflow:hidden;height:340px;position:relative;z-index:0}
#lmap{width:100%;height:100%;background:#071a2b}
.leaflet-tile{filter:grayscale(.55) brightness(.72) contrast(1.06)}
.leaflet-container{background:#071a2b;font:inherit}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#0A2238;color:#EAF6F8}
.leaflet-popup-content{margin:11px 14px;font-size:13px;line-height:1.5}
.leaflet-popup-content b{color:#5FD6E6}
.leaflet-control-attribution{background:rgba(10,17,32,.8)!important;color:#A9C7CE!important;font-size:10px!important}
.leaflet-control-attribution a{color:#A9C7CE!important}
.leaflet-bar a{background:#0A2238!important;color:#EAF6F8!important;border-color:rgba(160,230,240,.2)!important}
.mk-car{width:22px;height:22px;border-radius:50%;background:linear-gradient(180deg,#43c9db,#5FD6E6);
 border:2px solid #EAF6F8;box-shadow:0 0 0 6px rgba(95,214,230,.28),0 0 16px rgba(95,214,230,.7)}
.mk-chg{width:18px;height:18px;border-radius:50%;background:#8fcf2a;border:2px solid #071a2b;
 box-shadow:0 0 10px rgba(91,227,163,.6);display:flex;align-items:center;justify-content:center;
 font-size:10px;color:#04101b;font-weight:700}

.err{background:rgba(255,90,70,.10);border:1px solid rgba(255,120,90,.4);border-radius:14px;padding:10px 14px;
 font-size:13px;color:#FF8A6B;margin-bottom:12px;display:none}
a.cfg{color:var(--mut);font-size:12px;text-decoration:none}
.glocke{cursor:pointer;font-size:14px;user-select:none;opacity:.55;transition:.15s}
.glocke:hover{opacity:1}.glocke.an{opacity:1}
@media(max-width:640px){.hero{grid-template-columns:1fr}.car{min-height:170px}.car img{max-height:180px}}
/* Industrial ops refresh: shared local design tokens, flat surfaces, fast controls. */
:root{color-scheme:dark;--bg:#071a2b;--surface:#0A2238;--soft:#0f2c40;--border:#1d4152;
 --txt:#EAF6F8;--mut:#A9C7CE;--blue:#5FD6E6;--cyan:#43c9db;--line:#1d4152;
 --ok:#B5F23D;--warn:#FFC266;--danger:#FF8A6B;--fast:160ms;--ease:cubic-bezier(.22,1,.36,1)}
html{scroll-behavior:smooth}body{background:radial-gradient(900px 500px at 50% -220px,rgba(95,214,230,.22),transparent 70%),var(--bg);background-attachment:fixed;
 font:15px/1.5 Inter,"Segoe UI Variable",Segoe UI,sans-serif;padding:24px}
button,input{font:inherit}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid rgba(95,214,230,.45);outline-offset:3px}
.wrap{max-width:1160px}.top{gap:18px;margin-bottom:14px;padding:4px 2px}.brand{color:var(--txt);letter-spacing:2.5px;font-size:15px}
.brand b{color:var(--cyan)}.brand-sub{color:var(--mut);font-size:11px;letter-spacing:.04em;margin-top:2px}
.on{gap:9px;flex-wrap:wrap;justify-content:flex-end}.dot{background:var(--ok);box-shadow:0 0 0 5px rgba(34,197,94,.12)}
.dot.off{background:#64748B}.fresh{font-variant-numeric:tabular-nums}
.taktbox{position:absolute;right:16px;z-index:900;max-width:330px;margin-top:-6px;padding:14px 16px;border-radius:16px;
 border:1px solid var(--border);background:var(--surface);box-shadow:0 12px 40px rgba(0,0,0,.35);font-size:13px;line-height:1.45}
.taktbox label{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:10px}
.taktbox select{padding:6px 8px;border-radius:10px;border:1px solid var(--border);background:var(--soft);color:var(--txt);font:inherit}
.taktbox p{margin:10px 0 0;color:var(--mut)}.wrap{position:relative}
.rrow{display:grid;grid-template-columns:70px 1fr;gap:10px;align-items:start;margin:0 0 10px}.rrow label{padding-top:10px;color:var(--mut);font-size:13px}
.rfeld{position:relative}.rfeld input,.rrow3 input,.rrow3 select{width:100%;box-sizing:border-box;padding:10px 12px;border-radius:12px;border:1px solid var(--border);background:var(--soft);color:var(--txt);font:inherit}
.rvor{position:absolute;left:0;right:0;top:100%;z-index:60;background:var(--surface);border:1px solid var(--border);border-radius:12px;margin-top:4px;display:none;overflow:hidden}
.rvor div{padding:9px 12px;cursor:pointer;font-size:13.5px}.rvor div:hover{background:var(--soft)}
.rrow3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:4px 0 12px}.rrow3 label{display:flex;flex-direction:column;gap:5px;color:var(--mut);font-size:12.5px}
.rin{display:flex;align-items:center;gap:6px;color:var(--txt)}.rmut{color:var(--blue);font-size:11px;white-space:nowrap}
.rgo{background:#B5F23D;color:#1d2a00;font-weight:700;border:0;cursor:pointer;padding:11px 18px;border-radius:12px;font:inherit;font-weight:700}
.rsec{margin-top:12px;background:var(--soft);color:var(--txt);border:1px solid var(--border);cursor:pointer;padding:10px 16px;border-radius:12px;font:inherit;font-weight:600}
.rhint{color:var(--mut);font-size:12px;line-height:1.45;margin-top:8px}.rmsg{font-size:13px;margin-top:8px}
.rsum{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:14px;font-size:14px}.rsum b{font-size:20px;color:var(--txt)}
.rstopp{border-top:1px solid var(--line);padding:10px 2px;font-size:13.5px}.rstopp .sub{color:var(--mut);font-size:12.5px;margin-top:3px}
@media(max-width:460px){.rrow3{grid-template-columns:1fr 1fr}.rrow{grid-template-columns:1fr}.rrow label{padding-top:0}}

.iconbtn{min-width:40px;height:40px;border:1px solid var(--border);border-radius:12px;background:var(--surface);color:var(--txt);cursor:pointer;
 transition:background var(--fast),border-color var(--fast),transform var(--fast)}
.iconbtn:hover{background:var(--soft);border-color:#2a5566}.iconbtn:active{transform:scale(.96)}
.quicknav{position:sticky;top:10px;z-index:800;display:flex;gap:5px;overflow-x:auto;padding:6px;margin:0 0 18px;
 background:rgba(18,26,43,.96);border:1px solid var(--border);border-radius:16px;box-shadow:0 10px 30px rgba(11,16,32,.25)}
.quicknav a{color:var(--mut);text-decoration:none;padding:9px 13px;border-radius:10px;font-size:12px;font-weight:700;white-space:nowrap;
 transition:color var(--fast),background var(--fast)}.quicknav a:hover{color:var(--txt);background:var(--soft)}
.hero{grid-template-columns:300px minmax(0,1fr);gap:28px;margin:4px 0 22px;padding:24px;background:var(--surface);border:1px solid var(--border);border-radius:20px}
.ring .pct{font-weight:700;letter-spacing:-.05em}.ring .pct small,.range b small{font-weight:500}.range b{font-weight:700}
.car img,.car svg{filter:drop-shadow(0 22px 34px rgba(11,16,32,.55))}
.vehicle-caption{display:flex;align-items:center;justify-content:center;gap:9px;flex-wrap:wrap;margin-top:8px;text-align:center}
.vehicle-caption strong{font-size:15px;letter-spacing:.01em}.vehicle-caption span{color:var(--mut);font-size:11px}
.overview-kpis{grid-template-columns:repeat(4,minmax(0,1fr))!important;margin-top:-8px}
.overview-kpis .tile:first-child{border-color:rgba(95,214,230,.55);box-shadow:inset 0 3px #5FD6E6}
.overview-kpis .tile:nth-child(2){box-shadow:inset 0 3px #43c9db}.overview-kpis .tile .k:before{margin-right:7px;opacity:.9}
.overview-kpis .tile:nth-child(1) .k:before{content:'↗'}.overview-kpis .tile:nth-child(2) .k:before{content:'◉'}
.overview-kpis .tile:nth-child(3) .k:before{content:'∿'}.overview-kpis .tile:nth-child(4) .k:before{content:'●'}
.sect{letter-spacing:1.8px;font-weight:800;margin:26px 4px 9px;scroll-margin-top:84px}
.tile{background:var(--surface);border-color:var(--border);border-radius:14px;padding:17px 18px;backdrop-filter:none;transition:border-color var(--fast),transform var(--fast)}
.tile:hover{border-color:#2a5566}.tile .k{font-size:10px;letter-spacing:1.6px;font-weight:800}.tile .v{font-size:26px;font-weight:700;letter-spacing:-.025em}
.tile .v small{font-weight:500}.pill{min-width:120px;border-color:var(--border);border-radius:14px;padding:15px;font-size:14px;font-weight:700;background:var(--surface);
 transition:background var(--fast),border-color var(--fast),color var(--fast),transform var(--fast)}
.pill:hover{background:var(--soft);border-color:#2a5566;color:var(--txt)}.pill.busy{opacity:.55;pointer-events:none}
.chip{border-color:var(--border);border-radius:999px;padding:8px 13px;font-size:12px;font-weight:650;background:var(--surface)}
.bars{height:118px;background:var(--surface);border-color:var(--border);border-radius:14px}.map{border-color:var(--border);border-radius:20px;height:380px}
.err{background:rgba(239,68,68,.10);border-color:rgba(239,68,68,.45);border-radius:14px;color:#FFB4A0}
@media(max-width:760px){body{padding:14px}.hero{grid-template-columns:1fr;padding:18px}.grid[style]{grid-template-columns:repeat(2,minmax(0,1fr))!important}
 .overview-kpis{margin-top:0}
 .top{align-items:flex-start}.brand-sub{display:none}}
@media(max-width:460px){.grid[style]{grid-template-columns:1fr!important}.on #onl{display:none}.fresh{font-size:11px}.hero{padding:14px}.quicknav{top:6px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{transition:none!important}}
</style></head><body><div class=wrap>
 <div id=updbar style="display:none;background:linear-gradient(90deg,rgba(95,214,230,.16),rgba(95,214,230,.10));
  border:1px solid rgba(90,180,255,.45);border-radius:14px;padding:11px 15px;margin-bottom:14px;font-size:13.5px">
  🔔 <b>Version <span id=updver></span> ist da.</b> <span id=updwas style="color:var(--mut)"></span>
  <a id=updlink href="#" target="_blank" rel="noopener" style="color:var(--blue);margin-left:6px">Ansehen →</a>
 </div>
 <div class=top><div><div class=brand>EV <b>•</b> COCKPIT</div><div class=brand-sub>TEIL VON PANOPTES</div></div>
  <div class=on><span id=dot class=dot></span><span id=onl>—</span><span id=fresh class=fresh>noch nicht aktualisiert</span>
   <button class=iconbtn id=refreshbtn onclick="manualRefresh()" title="Jetzt aktualisieren" aria-label="Jetzt aktualisieren">↻</button>
   <button class=iconbtn id=taktbtn onclick="taktUm(event)" title="Wie oft beim Auto nachfragen?" aria-label="Wie oft beim Auto nachfragen?" style="display:none">⏱</button>
   &nbsp;<span id=glocke class=glocke onclick="glockeUm()" title="Benachrichtigen, wenn das Laden fertig ist">🔕</span>
   &nbsp;<a class=cfg href="/setup">⚙︎</a></div></div>
 <div id=taktbox class=taktbox style="display:none" onclick="event.stopPropagation()">
  <b>Wie oft beim Auto nachfragen?</b>
  <label>Geparkt<select id=taktpark onchange="taktSpeichern()"></select></label>
  <label>Bei Fahrt bzw. Laden<select id=taktfahrt onchange="taktSpeichern()"></select></label>
  <p><span>Jede Abfrage weckt die App im Auto. Ist dieser Tab verborgen, wird pausiert.</span>
  <span>Nach jedem Antippen kurz alle 5 s (höchstens 60 s), dann wieder der gewählte Takt.</span></p>
  <p id=taktheute></p>
 </div>
 <nav class=quicknav aria-label="Schnellnavigation"><a href="#overview">Übersicht</a><a href="#climate">Klima</a>
  <a href="#charging">Laden</a><a href="#energy-panel">Energie</a><a href="#prices">Preise</a><a href="#route" id=navroute style="display:none">Route</a><a href="#location">Standort</a></nav>
 <div class=err id=err></div>
 <div class=hero id=overview>
  <div>
   <div class=ring><svg class=ring width=250 height=250 viewBox="0 0 250 250">
    <circle cx=125 cy=125 r=112 fill=none stroke="#16243f" stroke-width=14/>
    <circle id=arc cx=125 cy=125 r=112 fill=none stroke="#5FD6E6" stroke-width=14 stroke-linecap=round stroke-dasharray=703 stroke-dashoffset=703/>
    <defs><linearGradient id=g x1=0 y1=0 x2=1 y2=1><stop offset=0% stop-color="#5FD6E6"/><stop offset=100% stop-color="#43c9db"/></linearGradient></defs>
   </svg><div class=val><div class=pct><span id=soc>–</span><small>%</small></div><div class=lbl>AKKU</div></div></div>
   <div class=range><b><span id=range>–</span><small> km</small></b><div class=lbl>REICHWEITE (ECHT)</div>
    <div class=lbl style="margin-top:3px">BYD sagt: <span id=bydrange>–</span> km</div>
    <div id=rangehint class=lbl style="margin-top:3px;display:none;text-transform:none;letter-spacing:0">lernt aus deinen Fahrten</div></div>
  </div>
  <div class=car id=car><div class=ph>Kein Foto hinterlegt<br><small>⚙︎ → Foto-URL</small></div></div>
 </div>
 <input id=car-photo-input type=file accept="image/*" hidden onchange="uploadCarPhoto(this)">

 <div class="grid overview-kpis" aria-label="Fahrzeugübersicht" style="grid-template-columns:repeat(4,1fr)">
  <div class=tile><div class=k>KILOMETERSTAND</div><div class=v><span id=odo>–</span><small> km</small></div></div>
  <div class=tile><div class=k>AUSSEN</div><div class=v><span id=tout>–</span><small> °C</small></div></div>
  <div class=tile><div class=k>VERBRAUCH Ø</div><div class=v><span id=cons>–</span><small> kWh</small></div>
   <div id=conshint style="font-size:11px;margin-top:4px;line-height:1.35;color:var(--mut);display:none">lernt aus deinen Fahrten</div></div>
  <div class=tile id=tyrebox><div class=k>REIFEN</div><div class=v><span id=tyre>–</span><small> kPa</small></div>
   <div id=tyremsg style="font-size:11px;margin-top:4px;line-height:1.35;display:none"></div></div>
 </div>

 <div id=pvbox style="display:none">
  <div class=sect>DEINE PV-ANLAGE</div>
  <div class=grid style="grid-template-columns:1fr">
   <div class=tile><div class=k>ERZEUGT GERADE</div>
    <div class=v><span id=pvw>–</span><small> W</small></div>
    <div style="color:var(--mut);font-size:11.5px;margin-top:4px">
     <span>Quelle: dein Home Assistant</span> · <span id=pvsrc>–</span></div>
    <div id=pverr style="display:none;color:#FFC266;font-size:12px;margin-top:6px"></div>
   </div>
  </div>
 </div>

 <div class=sect id=climate>KLIMA &amp; KOMFORT</div>
 <div class=klima>
  <div class="pill heat" onclick="cmd('heat')">🔥&nbsp; Heizen</div>
  <div class="pill cool" onclick="cmd('cool')">❄&nbsp; Kühlen</div>
  <div class="pill" onclick="cmd('off')">◼&nbsp; Aus</div>
  <div class="pill batt" id=p_batt onclick="battUm()">🔋&nbsp; Batterie vorheizen</div>
 </div>
 <div style="color:var(--mut);font-size:12px;margin-top:8px">🛡️ Aus Sicherheitsgründen nur bei ausgeschaltetem Auto.</div>
 <div class=klima id=extras style="margin-top:10px">
  <div class="pill" id=p_find onclick="cmd('find')">🔍&nbsp; Auto finden</div>
  <div class="pill" id=p_lock onclick="zusperren()">🔒&nbsp; Zusperren</div>
 </div>
 <div id=seatbox style="display:none;margin-top:10px">
  <div style="color:var(--mut);font-size:11px;letter-spacing:2px;margin:0 4px 6px">SITZE (FAHRER + BEIFAHRER)</div>
  <div class=klima>
   <div class="pill" onclick="cmd('seat_off')">💺&nbsp; Aus</div>
   <div class="pill" onclick="cmd('seat_lo')">💺&nbsp; Stufe 1</div>
   <div class="pill" onclick="cmd('seat_hi')">💺&nbsp; Stufe 2</div>
  </div>
 </div>
 <div id=ventbox style="display:none;margin-top:10px">
  <div class=klima>
   <div class="pill" onclick="cmd('vent_off')">💨&nbsp; Belüftung aus</div>
   <div class="pill" onclick="cmd('vent_lo')">💨&nbsp; Stufe 1</div>
   <div class="pill" onclick="cmd('vent_hi')">💨&nbsp; Stufe 2</div>
  </div>
 </div>
 <div class=msg id=msg></div>
 <div style="color:var(--mut);font-size:11.5px;text-align:center;margin-top:2px">
  Heizen zielt auf 26 °C, Kühlen auf 19 °C. <b>Batterie vorheizen</b> hilft im Winter vor dem Schnellladen — eine warme Batterie lädt deutlich schneller. Das geht auch bei geparktem Auto.
 </div>

 <div id=ladebox style="display:none">
  <div class=sect id=charging>LADEN</div>
  <div class=grid style="grid-template-columns:repeat(3,1fr)">
   <div class=tile><div class=k>LEISTUNG</div><div class=v><span id=l_kw>–</span><small> kW</small></div>
    <div style="color:var(--mut);font-size:11px;margin-top:2px" id=l_art>–</div></div>
   <div class=tile><div class=k>FERTIG IN</div><div class=v style="font-size:22px"><span id=l_rest>–</span></div>
    <div style="color:var(--mut);font-size:11px;margin-top:2px">laut Auto</div></div>
   <div class=tile id=l_preisbox style="display:none"><div class=k>STROM GERADE</div>
    <div class=v><span id=l_preis>–</span><small> ct/kWh</small></div>
    <div style="color:var(--mut);font-size:11px;margin-top:2px">Börse, ohne Netz &amp; Steuern</div></div>
  </div>
 </div>

 <div class=sect>STATUS</div>
 <div class=chips>
  <span class=chip>Verriegelt <span id=s_lock class=cm>–</span></span>
  <span class=chip>Türen <span id=s_door class=cm>–</span></span>
  <span class=chip>Fenster <span id=s_win class=cm>–</span></span>
  <span class=chip>Angesteckt <span id=s_plug class=cm>–</span></span>
  <span class=chip>Lädt <span id=s_charge class=cm>–</span></span>
  <span class=chip>Gang <span id=s_gear class=cm>–</span></span>
 </div>

 <div id=pricebox style="display:none">
  <div class=sect id=prices>STROMPREIS (BÖRSE)</div>
  <div class=grid style="grid-template-columns:repeat(3,1fr)">
   <div class=tile><div class=k>JETZT</div><div class=v><span id=p_now>–</span><small> ct/kWh</small></div></div>
   <div class=tile><div class=k>GÜNSTIGSTE STUNDE</div><div class=v><span id=p_cheap>–</span><small> ct</small></div>
    <div style="color:var(--mut);font-size:12px;margin-top:2px">um <span id=p_cheapt>–</span> Uhr</div></div>
   <div class=tile><div class=k>TEUERSTE</div><div class=v><span id=p_max>–</span><small> ct</small></div></div>
  </div>
  <div class=bars id=bars></div>
  <div style="color:var(--mut);font-size:11.5px;margin:8px 2px 0;line-height:1.5">
   <span>Börsenpreis ohne Netz &amp; Steuern — dein Rechnungspreis nur bei einem Börsentarif.</span>
   <span>Zone:</span> <span id=p_zone>–</span> · <span>Quelle:</span> <span id=p_src>–</span><span id=p_lic></span>
  </div>
 </div>

 <div id=sentrybox style="display:none">
  <div class=sect>WÄCHTER-KAMERA</div>
  <div class=tile style="padding:14px">
   <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px">
    <div class=k>LETZTE AUFNAHME</div>
    <div style="color:var(--blue);font-size:13px" id=s_time>–</div>
   </div>
   <div id=s_err style="display:none;color:#FFC266;font-size:12.5px;margin-top:8px"></div>
   <img id=s_img alt="Wächter-Aufnahme" style="display:none;width:100%;max-height:440px;object-fit:contain;
    background:#071a2b;border:1px solid var(--line);border-radius:14px;margin-top:10px">
  </div>
 </div>

 <div id=chgbox style="display:none">
  <div class=sect>LADESÄULEN IN DER NÄHE</div>
  <div class=tile style="padding:6px 4px"><div id=chglist></div></div>
  <div style="color:var(--mut);font-size:11.5px;margin:8px 2px 0">
   Quelle: <b id=chgsrc>OpenStreetMap</b> · Angaben ohne Gewähr
  </div>
 </div>

 <a id=panoptes-link href="/panoptes" style="display:none;margin:6px 0 12px;font-weight:600;color:var(--blue)">📡 Panoptes-Einstellungen</a>
 <div id=planerbox style="display:none">
  <div class=sect>ROUTENPLANER</div>
  <div class=tile style="padding:14px 16px">
   <div id=routebox style="display:none;margin:0 0 12px"></div>
   <a href="#route"
      style="display:inline-block;background:#B5F23D;color:#1d2a00;font-weight:700;text-decoration:none;padding:10px 16px;border-radius:12px">🗺️ Route planen</a>
   <a href="/planer/oeffnen" target="_blank" rel="noopener" style="margin-left:10px;font-size:12.5px;color:var(--mut)">↗ im eigenen Fenster</a>
   <div id=planerstat style="color:var(--mut);font-size:12.5px;margin-top:10px"></div>
   <details id=kartenbox style="margin-top:12px" ontoggle="if(this.open)kartenLaden()">
    <summary style="cursor:pointer;font-weight:600">💳 Meine Ladekarten <span id=kartensum style="color:var(--mut);font-weight:400"></span></summary>
    <div id=kartenliste style="margin-top:8px;font-size:13.5px"></div>
    <div id=kartenmsg style="font-size:12.5px;margin-top:6px;color:var(--mut)"></div>
   </details>
  </div>
 </div>

 <div id=planerlayer style="display:none;position:fixed;inset:0;z-index:2000;background:#071a2b;padding:12px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin:0 0 8px">
   <b style="font-family:Sora,system-ui">🗺️ Routenplaner</b>
   <button type=button onclick="planerZu()" style="background:rgba(255,255,255,.08);color:#EAF6F8;border:1px solid rgba(160,230,240,.22);border-radius:999px;padding:7px 14px;cursor:pointer">✕ Schließen</button>
  </div>
  <iframe id=planerframe title="Routenplaner" style="width:100%;height:calc(100% - 44px);border:0;border-radius:14px;background:#071a2b"></iframe>
 </div>

 <div id=routesect style="display:none">
  <div class=sect id=route>ROUTE</div>
  <div class=tile style="padding:14px 16px" id=routetile>
   <div class=rrow><label for=rstart>Start</label>
    <div class=rfeld><input id=rstart placeholder="📍 Mein Auto" autocomplete=off oninput="rSuche('start')">
     <div class=rvor id=rvor_start></div></div></div>
   <div class=rrow><label for=rziel>Ziel</label>
    <div class=rfeld><input id=rziel placeholder="Ort, Adresse, Link oder Plus Code" autocomplete=off oninput="rSuche('ziel')"
      onkeydown="if(event.key==='Enter')rSuche('ziel',true)">
     <div class=rvor id=rvor_ziel></div></div></div>
   <div class=rrow3>
    <label>Akku jetzt<span class=rin><input id=rsoc type=number min=1 max=100 oninput="this.dataset.hand=1;document.getElementById('rsocq').textContent=''"> % <span class=rmut id=rsocq></span></span></label>
    <label>Ankunft mind.<span class=rin><input id=rsocmin type=number min=0 max=80 value=15> %</span></label>
    <label>Wie<select id=rmodus><option value=kompromiss>ausgewogen</option><option value=billig>günstig</option><option value=schnell>schnell</option></select></label>
   </div>
   <button type=button id=rbtn onclick="rPlanen()" class=rgo>🗺️ Route berechnen</button>
   <div class=rhint>Start und Ziel gehen nur beim Klick auf „Route berechnen“ an den Routenplaner (byd.serveone.at) – das ist die Anfrage selbst. Kein Dauerversand, nichts im Hintergrund. Die Ortssuche fragt nur, während du tippst.</div>
   <div id=rmsg class=rmsg></div>
   <div id=rerg style="display:none">
    <div class=rsum id=rsum></div>
    <div id=rvorl class=rhint></div>
    <div class=map style="margin:12px 0;height:300px"><div id=rmap style="height:100%"></div></div>
    <div id=rstopps></div>
    <div id=rwarn class=rhint></div>
    <button type=button id=rauto onclick="rAnAuto()" class=rsec>📤 Ins Auto schicken</button>
    <div class=rhint>„Ins Auto schicken“ legt nur die Route beim Routenplaner ab; Panoptes im Auto holt sie dort ab. Am Fahrzeug wird nichts ausgelöst – kein Befehl, keine Navigation startet von selbst.</div>
    <div id=rautomsg class=rmsg></div>
   </div>
  </div>
 </div>

 <div class=sect id=location>STANDORT</div>
 <div class=map><div id=lmap></div></div>
 <div style="color:var(--mut);font-size:11.5px;margin:8px 2px 0">
  🔵 dein Auto · 🟢 Ladesäulen (anklickbar) — Karte © OpenStreetMap-Mitwirkende
 </div>
 <div id=lanhint style="display:none;margin:16px 2px 0;color:var(--mut);font-size:13px;text-align:center">
  📱 Auf Tablet/Handy im selben WLAN erreichbar unter <b id=lanurl style="color:var(--blue)"></b>
 </div>
 <!--ENERGIE-PANEL-->
 <div style="text-align:center;margin:18px 0 4px">
  <a href="/about" style="color:var(--mut);font-size:12px;text-decoration:none">Impressum · Haftungsausschluss · Datenschutz</a>
 </div>
</div>
<script src="/static/leaflet.js"></script>
<script src="/static/panoptes-karte-1.1.0.js" integrity="sha384-WFV5q2HBex9eBQHZgdppShpKNwUGDJS+1xYid+boekvLEIzWPflpxKMRzPjeDs0m"></script>
<script>
const SIL={
klein:'<svg viewBox="0 0 320 130" xmlns="http://www.w3.org/2000/svg"><g transform="translate(16,14)"><path d="M 8,96 L 10,70 C 12,57 22,49 40,46 L 66,43 L 96,15 C 102,8 112,5 126,5 L 200,5 C 214,5 224,9 230,17 L 250,45 L 272,51 C 284,55 288,65 288,76 L 288,96 Z" fill="#5FD6E6"/><circle cx="60" cy="96" r="19" fill="#071a2b"/><circle cx="60" cy="96" r="12" fill="#5FD6E6"/><circle cx="240" cy="96" r="19" fill="#071a2b"/><circle cx="240" cy="96" r="12" fill="#5FD6E6"/></g></svg>',
suv:'<svg viewBox="0 0 320 135" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,12)"><path d="M 6,100 L 8,62 C 10,48 20,40 38,37 L 60,34 L 88,10 C 94,4 104,1 118,1 L 214,1 C 228,1 238,5 242,13 L 252,36 L 278,42 C 290,46 294,56 294,68 L 294,100 Z" fill="#5FD6E6"/><circle cx="58" cy="100" r="22" fill="#071a2b"/><circle cx="58" cy="100" r="14" fill="#5FD6E6"/><circle cx="244" cy="100" r="22" fill="#071a2b"/><circle cx="244" cy="100" r="14" fill="#5FD6E6"/></g></svg>',
limo:'<svg viewBox="0 0 330 130" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,14)"><path d="M 6,96 L 8,72 C 10,60 20,52 38,49 L 74,45 L 108,17 C 114,10 124,7 138,7 L 196,7 C 210,7 220,11 226,18 L 258,46 L 282,50 C 294,54 298,64 298,74 L 298,96 Z" fill="#5FD6E6"/><circle cx="62" cy="96" r="19" fill="#071a2b"/><circle cx="62" cy="96" r="12" fill="#5FD6E6"/><circle cx="248" cy="96" r="19" fill="#071a2b"/><circle cx="248" cy="96" r="12" fill="#5FD6E6"/></g></svg>',
gross:'<svg viewBox="0 0 335 145" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,12)"><path d="M 4,112 L 6,66 C 8,52 18,44 36,41 L 56,38 L 82,14 C 88,8 98,5 112,5 L 228,5 C 242,5 252,9 256,17 L 264,40 L 288,46 C 300,50 304,60 304,72 L 304,112 Z" fill="#5FD6E6"/><circle cx="58" cy="112" r="23" fill="#071a2b"/><circle cx="58" cy="112" r="15" fill="#5FD6E6"/><circle cx="252" cy="112" r="23" fill="#071a2b"/><circle cx="252" cy="112" r="15" fill="#5FD6E6"/></g></svg>',
kombi:'<svg viewBox="0 0 330 135" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,13)"><path d="M6 100 8 67c2-12 12-20 30-23l42-5 24-25c6-7 16-10 30-10h102c13 0 22 5 27 15l10 23 20 5c12 4 16 14 16 25v28Z" fill="#5FD6E6"/><circle cx="61" cy="100" r="20" fill="#071a2b"/><circle cx="61" cy="100" r="12" fill="#5FD6E6"/><circle cx="250" cy="100" r="20" fill="#071a2b"/><circle cx="250" cy="100" r="12" fill="#5FD6E6"/></g></svg>',
van:'<svg viewBox="0 0 330 145" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,11)"><path d="M5 111 7 43c1-16 12-28 28-31h165c17 0 29 7 37 22l20 39 32 8c11 4 15 13 15 30Z" fill="#5FD6E6"/><circle cx="62" cy="111" r="22" fill="#071a2b"/><circle cx="62" cy="111" r="13" fill="#5FD6E6"/><circle cx="251" cy="111" r="22" fill="#071a2b"/><circle cx="251" cy="111" r="13" fill="#5FD6E6"/></g></svg>'};
const C=703;
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function nv(x){return (x==null||x==='')?'–':x}
function chooseCarPhoto(){document.getElementById('car-photo-input').click();}
function uploadCarPhoto(input){
 const file=input.files&&input.files[0];if(!file)return;
 const msg=document.getElementById('msg');msg.dataset.hold=1;msg.textContent=__T('Foto wird vorbereitet …');
 const image=new Image(), reader=new FileReader();
 reader.onload=()=>{image.onload=async()=>{
  const max=1600,scale=Math.min(1,max/Math.max(image.naturalWidth,image.naturalHeight));
  const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(image.naturalWidth*scale));canvas.height=Math.max(1,Math.round(image.naturalHeight*scale));
  canvas.getContext('2d').drawImage(image,0,0,canvas.width,canvas.height);
  try{const response=await fetch('/photo/upload',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({photo:canvas.toDataURL('image/jpeg',.86)})});
   const data=await response.json();if(!response.ok||!data.ok)throw Error(data.error||'Foto konnte nicht gespeichert werden');
   msg.textContent='✓ '+__T('Foto gespeichert');const car=document.getElementById('car');car.dataset.p='';manualRefresh();
  }catch(ex){msg.textContent='⚠️ '+ex.message;}finally{input.value='';setTimeout(()=>{msg.dataset.hold='';},3000);}
 };image.onerror=()=>{msg.textContent='⚠️ Bilddatei konnte nicht gelesen werden';};image.src=reader.result;};reader.readAsDataURL(file);
}
function yn(id,cond,ja,nein,warn){var e=document.getElementById(id);if(!e)return;
 e.textContent=cond?ja:nein;e.className=warn?(cond?'warnc':'okc'):(cond?'okc':'no');}

// --- Basiskarte: Community-Look (MapLibre-Stil wie Planer/Panoptes) sobald der Server ihn
// komplett liefert; sonst - und bei jedem Fehler - OpenStreetMap. Bibliotheken liegen im Paket.
const KARTEN_STIL='__KARTENSTIL__', EINW=__EINWILLIGUNG__;
async function einwilligung(werte){
 try{const r=await (await fetch('/einwilligung',{method:'POST',body:JSON.stringify(werte)})).json();
  if(r.ok)location.reload();}catch(e){}}
function karteWahl(el){            // ohne ausdrueckliche Wahl: keine Kacheln, sondern die Frage
 el.innerHTML='<div style="padding:18px;text-align:center;color:var(--mut)"><div style="font-weight:700;color:var(--txt);margin-bottom:6px">'+
  __T('Karte anzeigen?')+'</div><div style="font-size:13px;margin-bottom:12px">'+
  __T('Wer die Kartenbilder liefert, sieht deine IP-Adresse und die Gegend, die du anschaust.')+'</div>'+
  '<button type=button onclick="einwilligung({kartenquelle:\'osm\'})">'+__T('OpenStreetMap')+'</button> '+
  '<button type=button onclick="einwilligung({kartenquelle:\'community\'})">'+__T('Community-Karte')+'</button></div>';}
function einwHinweis(){            // einmal nach dem Update: Karte und 3D sind freiwillig
 if(!EINW.fragen)return;
 const d=document.createElement('div');d.id='einwhinweis';d.className='card';
 d.style.cssText='margin:12px 0;padding:14px 16px;border:1px solid var(--line);border-radius:14px';
 const q=EINW.kartenquelle;
 d.innerHTML='<div style="font-weight:700;margin-bottom:4px">'+__T('Neu: Karte und 3D-Modell sind freiwillig')+'</div>'+
  '<div style="font-size:13px;color:var(--mut);margin-bottom:8px">'+__T('Beides lädt Daten von fremden Servern; die sehen dabei deine IP-Adresse (und bei der Karte die Gegend, beim 3D-Modell dein Automodell). Ohne deine Wahl bleibt beides aus.')+'</div>'+
  '<div style="margin:4px 0"><b>'+__T('Karte')+':</b> '+
  ['keine','osm','community'].map(v=>'<label style="margin-right:12px"><input type=radio name=ewk value='+v+(q===v?' checked':'')+'> '+
   __T({keine:'Keine Karte',osm:'OpenStreetMap',community:'Community-Karte'}[v])+'</label>').join('')+'</div>'+
  '<div style="margin:4px 0"><label><input type=checkbox id=ew3d'+(EINW.modell3d?' checked':'')+'> '+__T('Dein Auto in 3D (vom Community-Server)')+'</label></div>'+
  '<button type=button style="margin-top:8px" onclick="einwilligung({kartenquelle:(document.querySelector(\'input[name=ewk]:checked\')||{}).value||\'keine\',modell3d:document.getElementById(\'ew3d\').checked})">'+__T('Speichern')+'</button>';
 const ziel=document.getElementById('overview')||document.body.firstElementChild;
 ziel.parentNode.insertBefore(d,ziel);}
document.addEventListener('DOMContentLoaded',einwHinweis);
function basiskarte(m){
 const osm=()=>L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap'}).addTo(m);
 if(!KARTEN_STIL){osm();return;}
 const lade=src=>new Promise((ok,f)=>{const x=document.createElement('script');x.src=src;x.onload=ok;x.onerror=f;document.head.appendChild(x);});
 fetch(KARTEN_STIL,{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('Stil '+r.status);return r.json();}).then(stil=>{
  // Blitzer/Kontrollen nie zeigen (CH Art. 98a SVG, Einschraenkungen DE/FR)
  stil.layers=(stil.layers||[]).filter(l=>!(/camera|blitz|enforcement|speed_?trap/i.test(l.id||'')||
   (l['source-layer']==='signals'&&/camera/.test(JSON.stringify(l.filter||'')))));
  const q=Object.values(stil.sources||{}).find(x=>x.type==='vector'&&/^pmtiles:\/\//.test(x.url||''));
  if(!q) return stil;
  return fetch(q.url.replace(/^pmtiles:\/\//,''),{headers:{Range:'bytes=0-15'}})
   .then(r=>{if(r.status!==206)throw new Error('Kacheln fehlen');return stil;});
 }).then(stil=>{
  const c=document.createElement('link');c.rel='stylesheet';c.href='/static/maplibre-gl.css';document.head.appendChild(c);
  return lade('/static/maplibre-gl.js').then(()=>lade('/static/pmtiles.js')).then(()=>lade('/static/leaflet-maplibre-gl.js'))
   .then(()=>{const pr=new pmtiles.Protocol();maplibregl.addProtocol('pmtiles',pr.tile);
    // Quellenangaben einmal und ohne Doppelungen (der Stil nennt OSM je Quelle)
    Object.values(stil.sources||{}).forEach(q=>{delete q.attribution;});
    m.attributionControl.setPrefix(false);
    window.GL_KARTE=L.maplibreGL({style:stil}).addTo(m);
    m.attributionControl.addAttribution('© OpenStreetMap-Mitwirkende · Protomaps · Höhen: Mapterhorn');
    // Ladesaeulen zeigt dann die Karte selbst (Ebene 'chargers', wie Planer und Panoptes);
    // die eigenen Infos (Preis, Entfernung) haengen per Klick daran.
    window.OSM_SAEULEN=(stil.layers||[]).some(l=>l.id==='chargers');
    if(window.OSM_SAEULEN){MK_CHG.forEach(x=>m.removeLayer(x));m.on('click',klickSaeule);liveSaeulen(m);}});
 }).catch(()=>osm());
}

// Live-Belegung: gemeinsames Kartenmodul panoptes-karte 1.1.0 (gleich wie /ev/ und Panoptes; Vertrag
// https://byd.serveone.at/tiles/lib/README.md). Die Anfrage laeuft ueber den lokalen Server (/live/umkreis),
// der die eigenen Ladekarten anhaengt; die Pflicht-Quellenangabe (z. B. EnBW CC BY 4.0) steht in der Kartenfusszeile.
// Das "?" fuer OSM-Saeulen nur ab Zoom 11 (v2.1) erledigt das Modul selbst.
let LIVE_ROH={};
function liveSaeulen(m){
 const PK=window.PanoptesKarte,g=GL_KARTE.getMaplibreMap();if(!PK)return;
 PK.liveEbene(g,{umkreisUrl:'/live/umkreis',sprache:window.__LANG__==='en'?'en':'de',
  beiDaten:stand=>{LIVE_ROH={};(stand.liste||[]).forEach(x=>{if(x.id!=null)LIVE_ROH[x.id]=x;});},
  quellen:t=>{if(t!==(window.LIVE_QUELLEN||'')){if(window.LIVE_QUELLEN)m.attributionControl.removeAttribution(esc(window.LIVE_QUELLEN));
   if(t)m.attributionControl.addAttribution(esc(t));window.LIVE_QUELLEN=t;}}});
}

// Routenplaner: eingebettet (gleiche Seite wie byd.serveone.at/ev/ mit Login) + Route/Rueckmeldung aus dem Auto
let ROUTE_T=0;

// --- Route (1.10): Planer ueber den Cockpit-Server; Start = Autoposition, Daten gehen nur beim Klick raus
const RW={start:null,ziel:null,start_name:'',ziel_name:''};let RT={},RMAP=null,RLAYER=null,RERG=null;
function rSuche(feld,sofort){const el=document.getElementById('r'+feld),box=document.getElementById('rvor_'+feld);
 RW[feld]=null;RW[feld+'_name']='';const q=el.value.trim();clearTimeout(RT[feld]);
 if(q.length<3){box.style.display='none';return;}
 RT[feld]=setTimeout(async()=>{try{const d=await (await fetch('/route/orte',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q:q})})).json();
  const o=d.orte||[];if(!o.length){box.innerHTML='<div style="color:var(--mut);cursor:default">'+esc(d.error||__T('Nichts gefunden'))+'</div>';box.style.display='block';return;}
  box.innerHTML=o.map((x,i)=>'<div data-i='+i+'>'+esc(x.name)+'</div>').join('');box.style.display='block';
  [...box.children].forEach(c=>c.onclick=()=>{const x=o[+c.dataset.i];RW[feld]=[x.lat,x.lon];RW[feld+'_name']=x.name;el.value=x.name;box.style.display='none';});
 }catch(e){}},sofort?0:450);}
function rDauer(m){m=Math.round(m||0);return m>=60?Math.floor(m/60)+' h '+String(m%60).padStart(2,'0')+' min':m+' min';}
function rSocVomAuto(s){const f=document.getElementById('rsoc');if(document.activeElement!==f&&!f.dataset.hand&&s.soc!=null){f.value=Math.round(s.soc);
 document.getElementById('rsocq').textContent=__T('vom Auto');}}
async function rPlanen(){const m=document.getElementById('rmsg'),b=document.getElementById('rbtn');
 if(!RW.ziel){m.textContent='⚠️ '+__T('Bitte ein Ziel aus der Liste wählen');return;}
 if(document.getElementById('rstart').value.trim()&&!RW.start){m.textContent='⚠️ '+__T('Bitte einen Start aus der Liste wählen oder das Feld leeren (dann gilt dein Auto)');return;}
 b.disabled=true;const t0=Date.now(),ab=new AbortController(),warte=()=>{m.textContent=__T('⏳ Frage den Routenplaner …')+' '+Math.round((Date.now()-t0)/1000)+' s';};
 warte();const uhr=setInterval(warte,1000),stopp=setTimeout(()=>ab.abort(),60000);
 try{const r=await fetch('/route/plan',{method:'POST',signal:ab.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({
   start:RW.start,ziel:RW.ziel,start_name:RW.start_name,ziel_name:RW.ziel_name,
   soc_start:document.getElementById('rsoc').dataset.hand?document.getElementById('rsoc').value:'',
   soc_ziel_min:document.getElementById('rsocmin').value,modus:document.getElementById('rmodus').value})});
  let d;try{d=await r.json();}catch(x){throw Error(__T('Unerwartete Antwort vom Cockpit-Server')+' (HTTP '+r.status+')');}
  if(!d.ok)throw Error(d.error||'Fehler');m.textContent='';RERG=d.route;rZeigen(d.route);
 }catch(e){m.textContent='⚠️ '+(e.name==='AbortError'?__T('Keine Antwort nach 60 s – der Routenplaner ist gerade zu langsam. Bitte gleich noch einmal.'):__T(e.message));}
 finally{clearInterval(uhr);clearTimeout(stopp);b.disabled=false;}}
function rZeigen(k){document.getElementById('rerg').style.display='block';document.getElementById('rautomsg').textContent='';
 const en=window.__LANG__==='en';
 document.getElementById('rsum').innerHTML='<span><b>'+Math.round(k.km||0)+'</b> km</span><span><b>'+rDauer(k.minuten)+'</b> '+__T('Fahrt')+'</span>'+
  '<span><b>'+(k.stopps.length)+'</b> '+(k.stopps.length===1?__T('Ladestopp'):__T('Ladestopps'))+(k.lade_min?' · '+rDauer(k.lade_min):'')+'</span>'+
  '<span>'+__T('Ankunft mit')+' <b>'+Math.round(k.soc_ankunft||0)+' %</b></span>'+(k.kosten!=null?'<span>≈ <b>'+Number(k.kosten).toFixed(2).replace('.',en?'.':',')+' €</b></span>':'');
 const v=k.vorlieben,vl=document.getElementById('rvorl');
 vl.innerHTML=(v?'⚡ '+__T('Deine Ladevorlieben gelten')+': '+esc(rVorlieben(v))+' · ':'⚡ '+__T('Ladevorlieben (z. B. nur bestimmte Ladenetze) stellst du im Planer-Konto ein')+' · ')+
  '<a href="https://byd.serveone.at/ev/" target=_blank rel=noopener style="color:var(--blue)">'+__T('Ladenetze einstellen (Planer → Route → Erweitert)')+' ↗</a>'+
  (k.fahrzeug?' · '+__T('Profil')+': '+esc(k.fahrzeug):'');
 document.getElementById('rstopps').innerHTML=k.stopps.map((s,i)=>'<div class=rstopp><b>'+(i+1)+'. '+esc(s.name)+'</b>'+
  (s.eigene_karte?' 💳':'')+(s.bevorzugt?' ⭐':'')+(s.geschlossen?' <span style="color:#FFC266">'+esc(__T('bei Ankunft geschlossen'))+'</span>':'')+'<div class=sub>'+[s.km!=null?__T('nach')+' '+Math.round(s.km)+' km':'',s.kw?Math.round(s.kw)+' kW':'',
  (s.soc_an!=null&&s.soc_ab!=null)?Math.round(s.soc_an)+' → '+Math.round(s.soc_ab)+' %':'',s.dauer_min?rDauer(s.dauer_min):'',
  s.preis!=null?'≈ '+Number(s.preis).toFixed(2).replace('.',en?'.':',')+' €':'',rOeff(s.oeffnung)].filter(Boolean).map(esc).join(' · ')+'</div></div>').join('')||
  '<div class=rhint>'+__T('Kein Ladestopp nötig.')+'</div>';
 document.getElementById('rwarn').innerHTML=(k.warnungen||[]).map(w=>'⚠️ '+esc(w)).join('<br>');
 rKarte(k);}
function rOeff(t){t=String(t||'');return t.indexOf('offen bis ')===0?__T('offen bis')+' '+t.slice(10):__T(t);}
function rVorlieben(v){if(typeof v==='string')return v;const t=[];
 if(v.netze&&v.netze.length)t.push((v.modus==='nur'?__T('nur'):__T('bevorzugt'))+' '+v.netze.join(', '));
 if(v.umweg_min)t.push(__T('Umweg bis')+' '+v.umweg_min+' min');if(v.nur_offen)t.push(__T('nur wenn bei Ankunft geöffnet'));
 return t.join(' · ')||JSON.stringify(v).slice(0,120);}
function rKarte(k){const el=document.getElementById('rmap'),g=k.geometrie||[];if(g.length<2){el.parentNode.style.display='none';return;}
 el.parentNode.style.display='';
 if(EINW.kartenquelle==='keine'||typeof L==='undefined'){       // ohne Kartenquelle: nur die Linie, keine Kacheln
  let a=90,b=-90,c=180,d=-180;g.forEach(p=>{a=Math.min(a,p[0]);b=Math.max(b,p[0]);c=Math.min(c,p[1]);d=Math.max(d,p[1]);});
  const W=600,H=300,sx=W/Math.max(d-c,1e-6),sy=H/Math.max(b-a,1e-6),s=Math.min(sx,sy)*.9,ox=(W-(d-c)*s)/2,oy=(H-(b-a)*s)/2;
  const P=p=>[(ox+(p[1]-c)*s).toFixed(1),(H-oy-(p[0]-a)*s).toFixed(1)];
  el.innerHTML='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:100%"><polyline fill=none stroke="#5FD6E6" stroke-width=3 points="'+
   g.map(p=>P(p).join(',')).join(' ')+'"/>'+k.stopps.filter(s=>s.lat!=null).map(s=>{const q=P([s.lat,s.lon]);
   return '<circle cx='+q[0]+' cy='+q[1]+' r=7 fill="#B5F23D"/>';}).join('')+
   '<circle cx='+P(g[0])[0]+' cy='+P(g[0])[1]+' r=6 fill="#fff"/><circle cx='+P(g[g.length-1])[0]+' cy='+P(g[g.length-1])[1]+' r=6 fill="#FF8A65"/></svg>'+
   '<div class=rhint style="position:relative;margin-top:-26px;padding:0 10px">'+__T('⚪ Start · 🟢 Ladestopp · 🟠 Ziel')+' – '+__T('ohne Kartenbilder (keine Kartenquelle gewählt)')+'</div>';return;}
 if(!RMAP){RMAP=L.map('rmap',{scrollWheelZoom:false});basiskarte(RMAP);}
 if(RLAYER)RMAP.removeLayer(RLAYER);
 const lin=L.polyline(g,{color:'#5FD6E6',weight:4});
 const ic=L.divIcon({className:'',html:'<div class=mk-chg>⚡</div>',iconSize:[18,18],iconAnchor:[9,9]});
 RLAYER=L.featureGroup([lin].concat(k.stopps.filter(s=>s.lat!=null).map(s=>L.marker([s.lat,s.lon],{icon:ic}).bindPopup('<b>'+esc(s.name)+'</b><br>'+esc(rOeff(s.oeffnung))))))
  .addTo(RMAP);setTimeout(()=>{RMAP.invalidateSize();RMAP.fitBounds(lin.getBounds().pad(.08));},50);}
async function rAnAuto(){const m=document.getElementById('rautomsg'),b=document.getElementById('rauto');b.disabled=true;m.textContent='⏳ …';
 try{const d=await (await fetch('/route/an-auto',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).json();
  if(!d.ok)throw Error(d.error||'Fehler');m.textContent='✓ '+__T('Route liegt im Planer bereit – Panoptes im Auto holt sie ab.');ROUTE_T=0;routeLaden();
 }catch(e){m.textContent='⚠️ '+__T(e.message);}finally{b.disabled=false;}}
document.addEventListener('click',e=>{if(!e.target.closest||!e.target.closest('.rfeld'))document.querySelectorAll('.rvor').forEach(x=>x.style.display='none');});
function planerAuf(){const f=document.getElementById('planerframe');if(!f.src)f.src='/planer/oeffnen';
 document.getElementById('planerlayer').style.display='block';document.body.style.overflow='hidden';}
function planerZu(){document.getElementById('planerlayer').style.display='none';document.body.style.overflow='';ROUTE_T=0;routeLaden();}
async function routeLaden(){if(Date.now()-ROUTE_T<30000)return;ROUTE_T=Date.now();
 try{const d=await (await fetch('/planer/route',{cache:'no-store'})).json(), b=document.getElementById('routebox');
  if(!d.an){b.style.display='none';return;}
  if(!d.route){b.style.display='block';b.innerHTML='<small style="color:var(--mut)">'+esc(__T('Keine Route bereit. Plane eine und schick sie mit „An Auto senden“ ins Auto.'))+'</small>';return;}
  const r=d.route,h=r.minuten?Math.floor(r.minuten/60)+' h '+String(r.minuten%60).padStart(2,'0')+' min':'';
  const st=r.status?(__T(r.status)+(r.status==='Navigation läuft'&&r.stopp!=null?' · '+__T('nächster Ladestopp')+' '+(r.stopp+1):'')):
   (r.abgeholt?__T('vom Auto abgeholt'):__T('wartet aufs Auto'));
  b.style.display='block';
  b.innerHTML='<div style="font-weight:700">'+esc(r.titel||__T('Route'))+'</div>'+
   '<div style="color:var(--mut);font-size:13px;margin-top:2px">'+[r.km?Math.round(r.km)+' km':'',h,
    r.stopps+' '+__T(r.stopps===1?'Ladestopp':'Ladestopps'),r.soc_ankunft!=null?__T('Ankunft')+' '+r.soc_ankunft+' %':''].filter(Boolean).map(esc).join(' · ')+'</div>'+
   '<div style="font-size:13px;margin-top:4px">🚗 '+esc(st)+'</div>'+(d.fehler?'<small style="color:#FFC266">⚠️ '+esc(d.fehler)+'</small>':'');
 }catch(e){}}

// Meine Ladekarten: dieselbe Liste wie auf /ev/ mit Login (beim Planer gespeichert, nur WELCHE Karten)
let KARTEN=null;
async function kartenLaden(){const l=document.getElementById('kartenliste'),m=document.getElementById('kartenmsg');
 m.textContent=__T('⏳ Frage den Planer …');
 try{const d=await (await fetch('/karten',{cache:'no-store'})).json();KARTEN=d;
  if(!d.tarife){m.textContent='⚠️ '+(d.fehler||'');return;}
  if(d.meine===null&&d.an){m.textContent=__T('Kommt bald: Der Planer kann Ladekarten noch nicht speichern.');}
  else if(d.fehler){m.textContent='⚠️ '+__T(d.fehler);}
  else if(!d.an){m.textContent=__T('Zum Speichern erst mit dem Routenplaner verbinden (Einstellungen → Extras).');}
  else m.textContent=__T('Ladesäulen auf der Karte zeigen dann den Preis deiner Karte, der Planer bevorzugt passende Ladestopps.');
  const meine=new Set(d.meine||[]),aus=!(d.an&&d.meine!==null);
  l.innerHTML=d.tarife.map(t=>'<label style="display:flex;gap:8px;align-items:center;margin:3px 0"><input type=checkbox class=karte value="'+t.id+'"'+
   (meine.has(t.id)?' checked':'')+(aus?' disabled':'')+'> '+esc(t.msp)+' · '+esc(t.name)+'</label>').join('')+
   (aus?'':'<button type=button onclick="kartenSpeichern()" style="margin-top:8px;background:#B5F23D;color:#1d2a00;font-weight:700;border:0;border-radius:10px;padding:8px 14px;cursor:pointer">'+esc(__T('Speichern'))+'</button>');
  kartenSumme();
 }catch(e){m.textContent='⚠️ '+e;}}
function kartenSumme(){const n=(KARTEN&&KARTEN.meine||[]).length;
 document.getElementById('kartensum').textContent=n?'· '+n+' '+__T(n===1?'Karte':'Karten'):'';}
async function kartenSpeichern(){const m=document.getElementById('kartenmsg');
 const ids=[...document.querySelectorAll('.karte:checked')].map(x=>+x.value);
 m.textContent=__T('⏳ Speichere …');
 try{const r=await (await fetch('/karten',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({karten:ids})})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  KARTEN.meine=r.meine;kartenSumme();m.textContent='✅ '+__T('Gespeichert — gilt auch auf /ev/ und im Planer.');
 }catch(e){m.textContent='⚠️ '+e;}}

// 3D-Auto wie in Panoptes (gemeinsame Modelle, CC BY 4.0 Nazh Design). Faellt still auf Foto/Silhouette zurueck.
const AUTO3D={ok:null,farbe:null,lack:[],r:null,grund:'',still:false,wieder:0};
function auto3dNochmal(){AUTO3D.ok=null;AUTO3D.lack=[];AUTO3D.grund='';document.getElementById('car').dataset.p='';load();}
async function auto3d(car,s){AUTO3D.ok='laedt';
 car.dataset.p='laedt';car.innerHTML='<div class=wrap><div class=ph>⏳ '+__T('3D-Modell wird geladen …')+'</div></div>';
 try{const i=await (await fetch('/modell3d/info',{cache:'no-store'})).json();
  if(!i.verfuegbar)throw {grund:i.grund||'',still:!!i.still};
  if(!window.WebGLRenderingContext)throw {grund:__T('Dieser Browser kann kein WebGL'),still:false};
  const THREE=await import('three');
  const {GLTFLoader}=await import('/static/three/examples/jsm/loaders/GLTFLoader.js');
  const {DRACOLoader}=await import('/static/three/examples/jsm/loaders/DRACOLoader.js');
  car.dataset.p='3d';
  car.innerHTML='<div class=wrap><canvas id=auto3d style="width:100%;max-width:560px;height:250px;display:block"></canvas>'+
   '<div class=hint id=laedt3d>⏳ '+__T('3D-Modell wird geladen …')+'</div>'+
   '<div class=vehicle-caption><strong>'+esc(s.model||i.name)+'</strong><span>3D: '+esc(i.attribution)+
   ' · <a href="'+esc(i.lizenzen)+'" target=_blank rel=noopener style="color:inherit">'+esc(__T('Lizenz'))+'</a></span></div>'+
   '<div class=lackwahl>'+(i.farben||[]).map(f=>'<button type=button title="'+esc(f.name)+'" data-farbe="'+esc(f.hex)+
    '" style="background:'+esc(f.hex)+'"></button>').join('')+'</div>'+
   '<div class=hint><button type=button onclick="chooseCarPhoto()">📷 '+__T('Eigenes Autofoto hinzufügen')+'</button></div></div>';
  const cv=document.getElementById('auto3d'),r=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
  r.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
  const sc=new THREE.Scene(),cam=new THREE.PerspectiveCamera(30,1,0.1,100);
  sc.add(new THREE.HemisphereLight(0xeaf6f8,0x0a2238,2.2));const dl=new THREE.DirectionalLight(0xffffff,2.4);dl.position.set(4,6,5);sc.add(dl);
  const dr=new DRACOLoader();dr.setDecoderPath('/static/three/examples/jsm/libs/draco/gltf/');
  const lo=new GLTFLoader();lo.setDRACOLoader(dr);
  const g=await lo.loadAsync('/modell3d/datei');const auto=g.scene;
  auto.traverse(o=>{if(o.isMesh){const n=((o.name||'')+' '+((o.material&&o.material.name)||'')).toLowerCase();
   if(n.includes(i.paint)){o.material=o.material.clone();AUTO3D.lack.push(o.material);}}});
  const box=new THREE.Box3().setFromObject(auto),gr=box.getSize(new THREE.Vector3()),mi=box.getCenter(new THREE.Vector3());
  auto.position.sub(mi);const pivot=new THREE.Group();pivot.add(auto);sc.add(pivot);
  const lang=Math.max(gr.x,gr.z);cam.position.set(lang*1.15,lang*0.42,lang*1.15);cam.lookAt(0,-gr.y*0.05,0);
  const farbe=hex=>{AUTO3D.lack.forEach(m=>m.color&&m.color.set(hex));};
  farbe(i.farbe||((i.farben||[])[0]||{}).hex||'#E8E8EC');
  car.querySelectorAll('[data-farbe]').forEach(b=>b.onclick=async()=>{farbe(b.dataset.farbe);
   try{await fetch('/modell3d/farbe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({farbe:b.dataset.farbe})});}catch(e){}});
  const groesse=()=>{const w=cv.clientWidth||520,h=cv.clientHeight||250;r.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();};
  groesse();window.addEventListener('resize',groesse);
  r.setAnimationLoop(()=>{if(document.hidden)return;pivot.rotation.y+=0.004;r.render(sc,cam);});
  const l3=document.getElementById('laedt3d');if(l3)l3.remove();
  AUTO3D.ok=true;
 }catch(e){AUTO3D.ok=false;AUTO3D.still=!!(e&&e.still);
  AUTO3D.grund=(e&&e.grund!==undefined)?e.grund:(__T('Laden fehlgeschlagen')+(e&&e.message?' ('+e.message+')':''));
  if(!AUTO3D.still){console.warn('3D-Modell nicht geladen:',e);
   if(!AUTO3D.wieder){AUTO3D.wieder=1;setTimeout(auto3dNochmal,60000);}}   // ein zweiter Versuch von selbst
  document.getElementById('car').dataset.p='';load();}}

// Klick auf ein Saeulensymbol der Karte: eigene Infos der naechsten Saeule (<120 m), sonst OSM-Angaben
function klickSaeule(e){
 if(!window.OSM_SAEULEN||!window.GL_KARTE) return;
 const g=GL_KARTE.getMaplibreMap(), p=g.project([e.latlng.lng,e.latlng.lat]);
 const live=g.getLayer('chargers-live')?g.queryRenderedFeatures([[p.x-9,p.y-9],[p.x+9,p.y+9]],{layers:['chargers-live']})[0]:null;
 if(live){const q=live.properties||{},r=LIVE_ROH[q.id]||{},pm=r.preis_meine;
  const preis=pm&&pm.preis_kwh!=null?(pm.karte||__T('Deine Karte'))+': '+Number(pm.preis_kwh).toFixed(2).replace('.',',')+' €/kWh':'';
  L.popup().setLatLng([e.latlng.lat,e.latlng.lng])
  .setContent('<b>'+esc(r.name||'Ladestation')+'</b><br>'+esc(q.lbl||'')+(preis?'<br>💳 '+esc(preis):'')+
   (r.karte_hinweis?'<br><small>'+esc(r.karte_hinweis)+'</small>':'')+
   (q.zustand!=='unbekannt'&&r.live_quelle?'<br><small>Live · '+esc(r.live_quelle)+'</small>':'')).openOn(MAP);return;}
 let f=g.queryRenderedFeatures([[p.x-9,p.y-9],[p.x+9,p.y+9]],{layers:['chargers']})[0];
 if(!f){let d0=24*24;g.queryRenderedFeatures({layers:['chargers']}).forEach(x=>{const q=g.project(x.geometry.coordinates),
   d=(q.x-p.x)**2+(q.y-p.y)**2;if(d<d0){d0=d;f=x;}});}
 if(!f) return;
 const c=f.geometry.coordinates,pos=[c[1],c[0]],pr=f.properties||{};
 let best=null,ab=1e9;MK_CHG.forEach(mk=>{const d=MAP.distance(pos,mk.getLatLng());if(d<ab){ab=d;best=mk;}});
 const html=(best&&ab<120)?best.getPopup().getContent():'<b>'+esc(pr.op||'Ladestation')+'</b>'+(pr.lbl?'<br>'+esc(pr.lbl):'');
 L.popup().setLatLng(pos).setContent(html).openOn(MAP);
}

// --- Leaflet-Karte: dein Auto + die Ladesaeulen auf EINER Karte ---
let MAP=null, MK_CAR=null, MK_CHG=[];
function zeichneKarte(s){
 if(!s.latitude||!s.longitude||typeof L==='undefined') return;
 const pos=[s.latitude,s.longitude];
 if(!MAP){
  if(EINW.kartenquelle==='keine'){const el=document.getElementById('lmap');if(!el.dataset.wahl){el.dataset.wahl=1;karteWahl(el);}return;}
  MAP=L.map('lmap',{zoomControl:true,attributionControl:true,scrollWheelZoom:false}).setView(pos,13);
  basiskarte(MAP);
 }
 const ic=L.divIcon({className:'',html:'<div class=mk-car></div>',iconSize:[22,22],iconAnchor:[11,11]});
 if(!MK_CAR){MK_CAR=L.marker(pos,{icon:ic,zIndexOffset:1000}).addTo(MAP).bindPopup('<b>Dein Auto</b>');}
 else{MK_CAR.setLatLng(pos);}
 const key=JSON.stringify((s.chargers||[]).map(c=>c.lat+','+c.lon));
 if(MAP._k!==key){
  MAP._k=key; MK_CHG.forEach(m=>{if(MAP.hasLayer(m))MAP.removeLayer(m);}); MK_CHG=[];
  const ic2=L.divIcon({className:'',html:'<div class=mk-chg>⚡</div>',iconSize:[18,18],iconAnchor:[9,9]});
  (s.chargers||[]).forEach(c=>{
   const d=[c.operator,c.sockets,(c.kw?c.kw+' kW':''),(c.eur_kwh?'€ '+Number(c.eur_kwh).toFixed(2).replace('.',',')+'/kWh':'')].filter(Boolean).join(' · ');
   const mk=L.marker([c.lat,c.lon],{icon:ic2})
    .bindPopup('<b>'+esc(c.name)+'</b>'+(d?'<br>'+esc(d):'')+'<br>'+c.km+__T(' km entfernt'));
   if(!window.OSM_SAEULEN) mk.addTo(MAP);       // sonst zeigt die Karte die Saeulen selbst
   MK_CHG.push(mk);
  });
  if(MK_CHG.length){MAP.fitBounds(L.featureGroup(MK_CHG.concat([MK_CAR])).getBounds().pad(0.15));}
 }
}

// --- Benachrichtigungen: entstehen im Browser, verlassen den Rechner NICHT ---
let LETZTER = {};                       // vorheriger Zustand, um Wechsel zu erkennen
let LOAD_BUSY=false, POLL_TIMER=null, LAST_STATE=null, LAST_OK=0, LAST_LATENCY=0, DATA_TS=0;
const TAKT_WAHL=[1,2,5,10,15,30,0];
function taktText(m){return m?(window.__LANG__==='en'?'every '+m+' min':'alle '+m+' min'):__T('nur manuell');}
function taktFuellen(a){
 ['taktpark','taktfahrt'].forEach(function(id,i){const el=document.getElementById(id);
  if(!el.options.length)el.innerHTML=TAKT_WAHL.map(m=>'<option value="'+m+'">'+taktText(m)+'</option>').join('');
  if(document.activeElement!==el)el.value=String(i?a.fahrt:a.geparkt);});
 document.getElementById('taktheute').textContent=(window.__LANG__==='en'?'Queries to the car today: ':'Heute ans Auto gefragt: ')+a.heute+'×';}
function taktUm(e){e.stopPropagation();const b=document.getElementById('taktbox');b.style.display=b.style.display==='none'?'block':'none';}
document.addEventListener('click',function(){const b=document.getElementById('taktbox');if(b)b.style.display='none';});
async function taktSpeichern(){
 try{const r=await fetch('/abfrage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(
  {geparkt:parseInt(document.getElementById('taktpark').value,10),fahrt:parseInt(document.getElementById('taktfahrt').value,10)})});
  const d=await r.json();if(d.abfrage)taktFuellen(d.abfrage);}catch(e){}
 schedulePoll();}
function freshness(){
 const e=document.getElementById('fresh');if(!e)return;
 if(!LAST_OK){e.textContent=__T('noch nicht aktualisiert');return;}
 const age=Math.max(0,Math.round((Date.now()-(DATA_TS||LAST_OK))/1000)), en=window.__LANG__==='en';
 const alt=age<2?__T('gerade eben'):(age<120?(en?age+' s ago':'vor '+age+' s'):(en?Math.round(age/60)+' min ago':'vor '+Math.round(age/60)+' min'));
 const a=LAST_STATE&&LAST_STATE.panoptes_an&&LAST_STATE.abfrage;
 e.textContent=alt+(a&&a.takt_s==null&&!a.pausiert?' · '+__T('nur manuell'):'')+' · '+LAST_LATENCY+' ms'+
  (window.__QUELLE__?' · '+window.__QUELLE__:'');
}
function schedulePoll(){
 clearTimeout(POLL_TIMER);
 if(document.hidden)return;          // Tab verborgen: nichts abrufen -> der Server pausiert die Abfragen beim Auto
 POLL_TIMER=setTimeout(load,5000);   // nur der lokale Zwischenspeicher; wie oft das Auto gefragt wird, steht unter ⏱
}
function melden(titel, text){
 try{ if(window.Notification && Notification.permission==='granted'){
   new Notification(titel, {body:text, icon:'/photo', tag:'evcockpit'});
 }}catch(e){}
}
function glockeAn(){ return localStorage.getItem('evc_melden')==='1'
                     && window.Notification && Notification.permission==='granted'; }
function glockeMalen(){
 const g=document.getElementById('glocke'); if(!g) return;
 const an=glockeAn(); g.textContent=an?'🔔':'🔕'; g.classList.toggle('an',an);
 g.title = an ? 'Meldet, wenn das Laden fertig ist (nur solange diese Seite offen ist)'
              : 'Benachrichtigen, wenn das Laden fertig ist';
}
async function glockeUm(){
 if(!window.Notification){ alert('Dein Browser kann keine Benachrichtigungen.'); return; }
 if(localStorage.getItem('evc_melden')==='1'){        // ausschalten
   localStorage.setItem('evc_melden','0'); glockeMalen(); return;
 }
 let p = Notification.permission;
 if(p!=='granted') p = await Notification.requestPermission();
 if(p==='granted'){ localStorage.setItem('evc_melden','1'); glockeMalen();
   melden('Benachrichtigungen an', 'Du bekommst Bescheid, wenn das Laden fertig ist.');
 } else {
   alert('Dein Browser hat Benachrichtigungen für diese Seite blockiert. '
       + 'Du kannst das im Schloss-Symbol neben der Adresse wieder erlauben.');
 }
}
function meldeWenn(s){
 const alt = LETZTER; LETZTER = {charging:s.charging, locked:s.locked, plugged:s.plugged, soc:s.soc};
 if(!glockeAn() || !alt.charging) return;              // erster Durchlauf: nur merken
 // fertig geladen: hat geladen, laedt nicht mehr, haengt noch am Kabel
 if(alt.charging==='ON' && s.charging==='OFF' && s.plugged==='ON'){
   melden(__T('🔌 Laden beendet'), __T('Dein Auto ist bei ') + Math.round(s.soc||0) + __T(' % — Kabel kann raus.'));
 }
 // Auto war verriegelt und ist es ploetzlich nicht mehr
 if(alt.locked==='ON' && s.locked==='OFF'){
   melden('🔓 Auto ist offen', 'Es war eben noch verriegelt.');
 }
}
async function load(){
 if(LOAD_BUSY)return;LOAD_BUSY=true;
 const refresh=document.getElementById('refreshbtn');if(refresh){refresh.disabled=true;refresh.textContent='…';}
 const started=performance.now();
 try{
 const response=await fetch('/data?sichtbar='+(document.hidden?0:1),{cache:'no-store'});
 if(!response.ok)throw Error('HTTP '+response.status);
 const s=await response.json();LAST_STATE=s;window.__QUELLE__=s.quelle||'';LAST_OK=Date.now();DATA_TS=s.daten_alter_s!=null?Date.now()-s.daten_alter_s*1000:0;LAST_LATENCY=Math.round(performance.now()-started);
 document.getElementById('taktbtn').style.display=s.panoptes_an?'':'none';if(s.panoptes_an&&s.abfrage)taktFuellen(s.abfrage);freshness();
 document.getElementById('dot').className='dot'+(s.online==='ON'?'':' off');
 document.getElementById('onl').textContent=s.online==='ON'?'ONLINE':'SCHLÄFT';
 const e=document.getElementById('err');
 if(s._err){e.style.display='block';e.textContent='⚠️ '+s._err;}else{e.style.display='none';}
 let soc=parseFloat(s.soc); if(isNaN(soc))soc=0;
 document.getElementById('soc').textContent=s.soc!=null?Math.round(s.soc):'–';
 document.getElementById('arc').style.strokeDashoffset=C-(C*soc/100);
 document.getElementById('range').textContent=nv(s.real_range_km);
 document.getElementById('bydrange').textContent=s.range_km!=null?Math.round(s.range_km):'–';
 document.getElementById('odo').textContent=s.odometer!=null?Math.round(s.odometer).toLocaleString('de'):'–';
 document.getElementById('tout').textContent=nv(s.temp_out);
 document.getElementById('cons').textContent=s.consumption_avg!=null?(Math.round(s.consumption_avg*10)/10):'–';
 document.getElementById('tyre').textContent=s.tyre_fl!=null?Math.round(s.tyre_fl):'–';
 // ehrlich statt blossem Strich: was fehlt, und warum
 document.getElementById('conshint').style.display=s.consumption_avg==null?'block':'none';
 document.getElementById('rangehint').style.display=(s.real_range_km==null&&s.soc!=null)?'block':'none';
 // Reifen-Ampel — nur wenn der Nutzer einen Sollwert eingetragen hat
 const tm=document.getElementById('tyremsg');
 if(!s.reifen&&s.tyre_fl==null&&s.soc!=null){tm.style.display='block';tm.style.color='var(--mut)';tm.textContent=__T('liefert diese Datenquelle nicht');}
 else if(s.reifen){tm.style.color='';tm.style.display='block';tm.textContent=s.reifen.text;
  tm.style.color = s.reifen.stufe==='rot' ? '#FF8A6B' : (s.reifen.stufe==='gelb' ? '#FFC266' : '#B5F23D');
  document.getElementById('tyrebox').style.borderColor =
    s.reifen.stufe==='rot' ? 'rgba(255,120,90,.55)' : (s.reifen.stufe==='gelb' ? 'rgba(255,176,32,.45)' : 'var(--line)');
 } else {tm.style.display='none';}
 // Laeuft die Klima? Das Auto meldet nur AN/AUS (kein "heizt gerade") -> beide Pills markieren
 const an=(s.klima_on==='ON');
 document.querySelector('.pill.heat').classList.toggle('on',an);
 document.querySelector('.pill.cool').classList.toggle('on',an);
 document.querySelector('.pill.batt').classList.toggle('on',s.battery_heat==='ON');
 if(s._msg&&!document.getElementById('msg').dataset.hold)document.getElementById('msg').textContent=s._msg;
 if(s.geheim_warnung&&!document.getElementById('geheimwarn')){const w=document.createElement('div');w.id='geheimwarn';
  w.style.cssText='margin:10px 0;padding:10px 14px;border:1px solid #6b5a2a;border-radius:12px;font-size:13px;color:#ffdca8';
  w.textContent='🔐 '+__T(s.geheim_warnung);const z=document.getElementById('overview');if(z)z.parentNode.insertBefore(w,z);}
 yn('s_lock',s.locked==='ON','Ja','Nein');
 yn('s_door',s.doors_open!=='ON','zu','OFFEN',true);
 yn('s_win',s.windows_open!=='ON','zu','OFFEN',true);
 yn('s_plug',s.plugged==='ON','Ja','Nein');
 yn('s_charge',s.charging==='ON','Ja','Nein');
 document.getElementById('s_gear').textContent=nv(s.gear);document.getElementById('s_gear').className='cm';
 // Eigenes Foto? Sonst gezeichnete Silhouette + Hinweis, dass man sein Auto einsetzen kann.
 const car=document.getElementById('car'), pk=s.photo||('sil:'+(s.silhouette||'klein'));
 const mit3d=!s.photo&&AUTO3D.ok!==false;
 if(mit3d&&AUTO3D.ok===null)auto3d(car,s);
 if(!mit3d&&car.dataset.p!==pk){car.dataset.p=pk;
  const model=esc(s.model||'Elektrofahrzeug');
  const caption='<div class=vehicle-caption><strong>'+model+'</strong><span>'+__T('Rechtlich neutrale Silhouette')+'</span></div>';
  if(s.photo){car.innerHTML='<div class=wrap><img src="'+esc(s.photo)+'" alt="'+model+'">'+caption+'</div>';}
  else{car.innerHTML='<div class=wrap>'+(SIL[s.silhouette]||SIL.klein)+caption+
   (AUTO3D.ok===false&&!AUTO3D.still?'<div class=hint style="opacity:.85">⚠️ '+__T('3D-Modell nicht geladen')+
    (AUTO3D.grund?': '+esc(AUTO3D.grund):'')+' <button type=button onclick="auto3dNochmal()">↻ '+__T('Erneut versuchen')+'</button></div>':'')+
   '<div class=hint><button type=button onclick="chooseCarPhoto()">📷 '+__T('Eigenes Autofoto hinzufügen')+'</button></div></div>';}}
 if(s.lan_url){document.getElementById('lanhint').style.display='block';
  document.getElementById('lanurl').textContent=s.lan_url;}
 // Lade-Ansicht: nur wenn das Kabel dran ist
 const angesteckt = (s.plugged==='ON' || s.charging==='ON');
 document.getElementById('ladebox').style.display = angesteckt ? 'block' : 'none';
 if(angesteckt){
  const kw = (s.charge_power!=null) ? Math.abs(s.charge_power) : null;
  document.getElementById('l_kw').textContent = kw!=null ? (Math.round(kw*10)/10).toString().replace('.',',') : '–';
  // grob einordnen, was da passiert — hilft mehr als die nackte Zahl
  let art = __T('angesteckt, lädt nicht');
  if(s.charging==='ON'){
   art = kw==null ? __T('lädt') : (kw>=50 ? __T('Schnellladen') : (kw>=7 ? __T('Wallbox-Tempo') : __T('langsam (Steckdose?)')));
  }
  document.getElementById('l_art').textContent = art;
  document.getElementById('l_rest').textContent =
    (s.charging==='ON' && s.charge_remaining) ? s.charge_remaining : '–';
  if(s.price_now!=null){
   document.getElementById('l_preisbox').style.display='';
   document.getElementById('l_preis').textContent=s.price_now.toFixed(2).replace('.',',');
  }
 }
 // Nur die Knöpfe zeigen, die der Nutzer angehakt hat (und die das Auto kann)
 const F=s.features||{};
 const zeig=(id,an)=>{const e=document.getElementById(id); if(e) e.style.display=an?'':'none';};
 if(Object.keys(F).length){
  document.querySelectorAll('.pill.heat,.pill.cool').forEach(e=>e.style.display=F.klima?'':'none');
  zeig('p_batt',F.batt); zeig('p_find',F.find); zeig('p_lock',F.lock);
  zeig('seatbox',F.seat); zeig('ventbox',F.seatvent);
  const ex=document.getElementById('extras');
  if(ex) ex.style.display=(F.find||F.lock)?'':'none';
 }
 // Update-Hinweis (nur wenn angehakt UND es wirklich was Neues gibt)
 if(s.update){document.getElementById('updbar').style.display='block';
  document.getElementById('updver').textContent=s.update.version;
  document.getElementById('updwas').textContent=s.update.was_neu||'';
  document.getElementById('updlink').href=s.update.url;}
 // PV aus Home Assistant
 if(s.pv_watt!=null||s.pv_err){
  document.getElementById('pvbox').style.display='block';
  if(s.pv_watt!=null){document.getElementById('pvw').textContent=s.pv_watt.toLocaleString('de');
   document.getElementById('pvsrc').textContent=s.pv_name||'';}
  const pe=document.getElementById('pverr');
  if(s.pv_err){pe.style.display='block';pe.textContent='⚠️ '+s.pv_err;}else{pe.style.display='none';}
 }
 // Ladesaeulen
 if(s.chargers&&s.chargers.length){
  document.getElementById('chgbox').style.display='block';
  document.getElementById('chgsrc').textContent=s.charger_source||'OpenStreetMap';
  const k=JSON.stringify(s.chargers), box=document.getElementById('chglist');
  if(box.dataset.k!==k){box.dataset.k=k;
   box.innerHTML=s.chargers.map(c=>{
    const d=[c.operator,c.sockets,(c.kw?c.kw+' kW':''),(c.n?c.n+'x':''),(c.eur_kwh?'€ '+Number(c.eur_kwh).toFixed(2).replace('.',',')+'/kWh':'')].filter(Boolean).join(' · ');
    return '<div class=chg><div><div class=nm>'+
      '<a href="https://www.openstreetmap.org/?mlat='+c.lat+'&mlon='+c.lon+'#map=17/'+c.lat+'/'+c.lon+'" target="_blank" rel="noopener">'+
      esc(c.name)+'</a></div>'+(d?'<div class=sub>'+esc(d)+'</div>':'')+'</div><div class=km>'+c.km+' km</div></div>';
   }).join('');}
 }
 const pl=document.getElementById('panoptes-link');if(pl)pl.style.display=s.panoptes_an?'inline-block':'none';
 // Routenplaner
 document.getElementById('routesect').style.display=(s.planer&&s.planer.an)?'block':'none';
 document.getElementById('navroute').style.display=(s.planer&&s.planer.an)?'':'none';
 if(s.planer&&s.planer.an){rSocVomAuto(s);
  document.getElementById('planerbox').style.display='block';
  routeLaden();
  const p=s.planer, t=[], vor=ts=>Math.max(0,Math.round((Date.now()/1000-ts)/60));
  if(p.soc!=null) t.push(__T('Ladestand an den Planer gemeldet: ')+p.soc+' % ('+__T('vor ')+vor(p.soc_t)+' min)');
  if(p.panoptes) t.push(__T('Panoptes im Auto meldet Ladestand und Verbrauch selbst.'));
  if(p.fahrten) t.push(__T('Verbrauch aus ')+p.fahrten+__T(' Fahrt(en) gelernt, Faktor ')+(p.fahrt_letzte?p.fahrt_letzte.faktor:'–'));
  if(p.fehler) t.push('⚠️ '+p.fehler);
  document.getElementById('planerstat').textContent=t.length?t.join(' · '):__T('Verbunden. Der Ladestand wird gemeldet, sobald das Auto wach ist.');
 }
 // Waechter
 if(s.sentry_on){
  document.getElementById('sentrybox').style.display='block';
  const e=document.getElementById('s_err');
  if(s.sentry_err){e.style.display='block';e.textContent='⚠️ '+s.sentry_err;}else{e.style.display='none';}
  if(s.sentry_img){const im=document.getElementById('s_img');im.style.display='block';
   if(im.dataset.f!==s.sentry_file){im.dataset.f=s.sentry_file;im.src='/sentry.jpg?t='+Date.now();}
   document.getElementById('s_time').textContent=s.sentry_time||'';}
 }
 // Strompreis
 if(s.price_bars&&s.price_bars.length){
  document.getElementById('pricebox').style.display='block';
  document.getElementById('p_now').textContent=s.price_now!=null?s.price_now.toFixed(2).replace('.',','):'–';
  document.getElementById('p_cheap').textContent=s.price_cheap_ct.toFixed(2).replace('.',',');
  document.getElementById('p_cheapt').textContent=s.price_cheap_time;
  document.getElementById('p_max').textContent=s.price_max_ct.toFixed(2).replace('.',',');
  document.getElementById('p_zone').textContent=s.price_zone||'–';
  document.getElementById('p_src').textContent=s.price_src||'–';
  // CC-BY-Lizenz der Datenquelle sichtbar machen (Namensnennung ist Pflicht)
  document.getElementById('p_lic').textContent=s.price_lic?(' · '+s.price_lic):'';
  const key=JSON.stringify(s.price_bars), box=document.getElementById('bars');
  if(box.dataset.k!==key){box.dataset.k=key;
   const mx=Math.max(...s.price_bars.map(b=>Math.abs(b.ct)),0.1);
   box.innerHTML=s.price_bars.map(b=>{
    const h=Math.max(3,Math.round(Math.abs(b.ct)/mx*72));
    const cls='bar'+(b.now?' now':'')+(b.cheap&&!b.now?' cheap':'');
    const tag=(b.now||b.cheap)?'<span class=t>'+b.ct.toFixed(0)+'</span>':'';
    return '<div class="'+cls+'" title="'+b.h+__T(' Uhr: ')+b.ct.toFixed(2)+' ct/kWh">'+tag+
           '<i style="height:'+h+'px"></i><b>'+b.h+'</b></div>';}).join('');}
 }
 zeichneKarte(s);
 meldeWenn(s);
}catch(ex){
 const e=document.getElementById('err');e.style.display='block';e.textContent='⚠️ Aktualisierung fehlgeschlagen: '+ex.message;
}finally{
 LOAD_BUSY=false;if(refresh){refresh.disabled=false;refresh.textContent='↻';}schedulePoll();
}}
function manualRefresh(){clearTimeout(POLL_TIMER);
 fetch('/jetzt',{method:'POST'}).catch(function(){}).then(function(){setTimeout(load,1500);});}
function zusperren(){
 if(confirm('Auto wirklich zusperren?')) cmd('lock');}
function battUm(){ // an/aus je nach aktuellem Zustand des Autos
 const an=document.querySelector('.pill.batt').classList.contains('on');
 cmd(an?'batt_off':'batt_on');}
async function cmd(a){
 const m=document.getElementById('msg');m.dataset.hold=1;m.textContent='⏳ Sende …';
 const controls=[...document.querySelectorAll('.pill')];controls.forEach(e=>e.classList.add('busy'));
 try{
  const response=await fetch('/cmd?a='+encodeURIComponent(a),{method:'POST'});
  const data=await response.json();if(!response.ok||!data.ok)throw Error(data.error||'Befehl abgelehnt');
  m.textContent='✓ Befehl angenommen · Fahrzeugstatus wird aktualisiert';
 }catch(ex){m.textContent='⚠️ '+ex.message;}
 finally{controls.forEach(e=>e.classList.remove('busy'));}
 setTimeout(()=>{m.dataset.hold='';manualRefresh();},2200);}
document.addEventListener('visibilitychange',()=>{if(!document.hidden){clearTimeout(POLL_TIMER);load();}else clearTimeout(POLL_TIMER);});
setInterval(freshness,5000);glockeMalen();load();
</script></body></html>"""


def _reifen_urteil(st):
    """Bewertet den Reifendruck gegen den vom Nutzer eingetragenen Sollwert.
    Kein Sollwert -> kein Urteil (lieber nichts sagen als Falsches).
    Ich kann den Sollwert NICHT erraten: er haengt an Reifengroesse und Beladung
    und steht im Tuerrahmen des Autos."""
    soll = _CFG.get("tyre_target")
    if not soll:
        return None
    try:
        soll = float(soll)
    except Exception:
        return None
    werte = [st.get(k) for k in ("tyre_fl", "tyre_fr", "tyre_rl", "tyre_rr")]
    werte = [float(w) for w in werte if isinstance(w, (int, float)) and w > 50]
    if not werte:
        return None
    tief = min(werte)
    abw = (tief - soll) / soll * 100.0
    if abw < -20:
        return {"stufe": "rot", "text": "Deutlich zu wenig Druck (%.0f kPa statt %.0f) — bitte bald prüfen." % (tief, soll)}
    if abw < -10:
        return {"stufe": "gelb", "text": "Etwas wenig Druck (%.0f kPa statt %.0f) — beim nächsten Tanken nachfüllen." % (tief, soll)}
    if abw > 15:
        return {"stufe": "gelb", "text": "Reichlich viel Druck (%.0f kPa statt %.0f)." % (tief, soll)}
    return {"stufe": "gruen", "text": "Druck passt (%.0f–%.0f kPa)." % (min(werte), max(werte))}


# ---------------------------------------------------------------- Update-Hinweis (optional)
VERSION_URL = "https://byd.serveone.at/ev-cockpit/version.json"


def _ver_tupel(v):
    """'1.10' > '1.9' — als Text verglichen waere '1.10' kleiner. Darum in Zahlen zerlegen."""
    try:
        return tuple(int(x) for x in str(v).strip().split("."))
    except Exception:
        return (0,)


def _update_loop():
    """Fragt EINE statische Datei ab und vergleicht LOKAL. Tut nichts ohne Haekchen.
    Der Server erfaehrt dabei nicht, welche Version hier laeuft."""
    import urllib.request
    while True:
        try:
            if _CFG.get("update_check"):
                req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "EV-Cockpit"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    d = json.loads(r.read().decode())
                neu = d.get("version")
                if neu and _ver_tupel(neu) > _ver_tupel(VERSION):
                    _STATE["update"] = {"version": neu,
                                        "was_neu": (d.get("was_neu") or "")[:220],
                                        "url": d.get("url") or "https://byd.serveone.at/ev-cockpit/"}
                else:
                    _STATE.pop("update", None)      # schon aktuell -> Hinweis wieder weg
        except Exception:
            pass                                    # kein Netz? egal, das Cockpit laeuft weiter
        time.sleep(86400)                           # hoechstens einmal am Tag


# ---------------------------------------------------------------- PV aus Home Assistant (optional)
def _ha_get(url, token, pfad, timeout=10):
    """Liest aus HAs REST-API. NUR lesend."""
    import urllib.request
    u = url.rstrip("/") + pfad
    req = urllib.request.Request(u, headers={"Authorization": "Bearer " + token,
                                             "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _ha_power_entities(url, token):
    """Fuer den Auswahl-Dialog: alle Sensoren, die nach Leistung aussehen.
    Filter wie HA selbst: device_class=power ODER Einheit W/kW."""
    out = []
    for e in _ha_get(url, token, "/api/states", 20):
        a = e.get("attributes") or {}
        if a.get("device_class") == "power" or a.get("unit_of_measurement") in ("W", "kW"):
            out.append({"id": e.get("entity_id"),
                        "name": a.get("friendly_name") or e.get("entity_id"),
                        "state": e.get("state"),
                        "unit": a.get("unit_of_measurement") or ""})
    out.sort(key=lambda x: x["name"].lower())
    return out


def _pv_loop():
    """Holt die PV-Leistung aus HA. Tut nichts ohne Haekchen."""
    while True:
        try:
            if _CFG.get("pv") and _CFG.get("pv_url") and _CFG.get("pv_token") and _CFG.get("pv_entity"):
                d = _ha_get(_CFG["pv_url"], _CFG["pv_token"], "/api/states/" + _CFG["pv_entity"])
                roh = d.get("state")
                a = d.get("attributes") or {}
                if roh not in ("unknown", "unavailable", None, ""):
                    w = float(roh)
                    if (a.get("unit_of_measurement") or "").lower() == "kw":
                        w *= 1000                      # immer in Watt rechnen
                    _STATE["pv_watt"] = round(w)
                    _STATE["pv_name"] = a.get("friendly_name") or _CFG["pv_entity"]
                    _STATE["pv_err"] = ""
                else:
                    _STATE["pv_err"] = "Sensor meldet '%s' — liefert dein HA gerade Werte?" % roh
        except Exception as e:
            m = str(e)
            if "401" in m or "403" in m:
                m = "Token abgelehnt — in HA neu erzeugen (Profil → Sicherheit)."
            elif "404" in m:
                m = "Sensor nicht gefunden — im Assistenten neu auswählen."
            _STATE["pv_err"] = m[:110]
        time.sleep(60)


# ---------------------------------------------------------------- Home Assistant (optional)
# Nur aktiv, wenn im Assistenten angehakt. Sonst wird kein MQTT angefasst.
HA_SENSORS = {
    "odometer":        ("Kilometerstand", "km", "distance", "mdi:counter", "total_increasing"),
    "soc":             ("Ladezustand", "%", "battery", "mdi:battery", "measurement"),
    "real_range_km":   ("Echte Reichweite", "km", "distance", "mdi:map-marker-distance", "measurement"),
    "range_km":        ("Reichweite (BYD)", "km", "distance", "mdi:map-marker-distance", "measurement"),
    "consumption_avg": ("Verbrauch Schnitt", "kWh/100km", None, "mdi:lightning-bolt-outline", "measurement"),
    "charge_power":    ("Ladeleistung", "kW", "power", "mdi:ev-station", "measurement"),
    "temp_out":        ("Außentemperatur", "°C", "temperature", "mdi:thermometer", "measurement"),
    "tyre_fl":         ("Reifen VL", "kPa", "pressure", "mdi:car-tire-alert", "measurement"),
    "tyre_fr":         ("Reifen VR", "kPa", "pressure", "mdi:car-tire-alert", "measurement"),
    "tyre_rl":         ("Reifen HL", "kPa", "pressure", "mdi:car-tire-alert", "measurement"),
    "tyre_rr":         ("Reifen HR", "kPa", "pressure", "mdi:car-tire-alert", "measurement"),
    "gear":            ("Gang", None, None, "mdi:car-shift-pattern", None),
}
HA_BINARY = {
    "locked":       ("Verriegelt", "lock", "mdi:lock"),
    "online":       ("Online", "connectivity", "mdi:car-connected"),
    "charging":     ("Lädt", "battery_charging", "mdi:battery-charging"),
    "plugged":      ("Angesteckt", "plug", "mdi:power-plug"),
    "doors_open":   ("Türen offen", "door", "mdi:car-door"),
    "windows_open": ("Fenster offen", "window", "mdi:window-open"),
    "klima_on":     ("Klima läuft", "running", "mdi:air-conditioner"),
    "battery_heat": ("Batterie heizt", "heat", "mdi:car-battery"),
}
_HA = {"cli": None, "ok": False, "err": ""}


def _ha_ids():
    """Eindeutig pro Fahrzeug — sonst kollidieren zwei Autos im selben HA."""
    v = (_CFG.get("vin") or "byd")[-6:].lower()
    return v, "evcockpit/%s" % v


def _ha_client(cid):
    import paho.mqtt.client as mqtt
    try:                                    # paho 2.x
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=cid)
    except AttributeError:                  # paho 1.x kennt CallbackAPIVersion nicht
        return mqtt.Client(client_id=cid)


def _ha_discovery(cli):
    v, base = _ha_ids()
    dev = {"identifiers": ["evcockpit_%s" % v],
           "name": _CFG.get("model") or "BYD",
           "manufacturer": "BYD", "model": _CFG.get("model") or "",
           "sw_version": "EV-Cockpit %s" % VERSION}
    st, avail = base + "/state", base + "/availability"
    for k, (name, unit, dc, icon, sc) in HA_SENSORS.items():
        c = {"name": name, "unique_id": "evc_%s_%s" % (v, k), "state_topic": st,
             "value_template": "{{ value_json.%s }}" % k, "availability_topic": avail,
             "icon": icon, "device": dev}
        if unit: c["unit_of_measurement"] = unit
        if dc: c["device_class"] = dc
        if sc: c["state_class"] = sc
        cli.publish("homeassistant/sensor/evc_%s_%s/config" % (v, k), json.dumps(c), retain=True)
    for k, (name, dc, icon) in HA_BINARY.items():
        c = {"name": name, "unique_id": "evc_%s_%s" % (v, k), "state_topic": st,
             "value_template": "{{ value_json.%s }}" % k, "payload_on": "ON", "payload_off": "OFF",
             "availability_topic": avail, "device_class": dc, "icon": icon, "device": dev}
        cli.publish("homeassistant/binary_sensor/evc_%s_%s/config" % (v, k), json.dumps(c), retain=True)
    trk = {"name": "Standort", "unique_id": "evc_%s_loc" % v, "json_attributes_topic": st,
           "state_topic": base + "/tracker", "source_type": "gps",
           "availability_topic": avail, "device": dev}
    cli.publish("homeassistant/device_tracker/evc_%s_loc/config" % v, json.dumps(trk), retain=True)
    # Zwei Knoepfe statt Thermostat: das Auto hat KEINEN Innentemp-Fuehler, ein
    # HA-Thermostat braucht aber current_temperature. Waere also eine Luege.
    for key, name, icon in (("heat", "🔥 Heizen", "mdi:fire"),
                            ("cool", "❄️ Kühlen", "mdi:snowflake"),
                            ("off", "⏹️ Klima aus", "mdi:air-conditioner-off"),
                            ("batt_on", "🔋 Batterie vorheizen", "mdi:car-battery"),
                            ("batt_off", "🔋 Batterie-Heizung aus", "mdi:battery-off")):
        c = {"name": name, "unique_id": "evc_%s_%s" % (v, key), "command_topic": base + "/cmd/" + key,
             "icon": icon, "availability_topic": avail, "device": dev}
        cli.publish("homeassistant/button/evc_%s_%s/config" % (v, key), json.dumps(c), retain=True)


def _ha_on_connect(cli, u, f, rc):
    v, base = _ha_ids()
    _HA["ok"] = (rc == 0)
    if rc != 0:
        _HA["err"] = "Broker weist ab (Code %s) — Benutzer/Passwort?" % rc
        return
    _HA["err"] = ""
    _ha_discovery(cli)
    cli.publish(base + "/availability", "online", retain=True)
    for k in ("heat", "cool", "off", "batt_on", "batt_off"):
        cli.subscribe(base + "/cmd/" + k)


def _ha_on_msg(cli, u, m):
    a = m.topic.rsplit("/", 1)[-1]
    if a in ("heat", "cool", "off", "batt_on", "batt_off"):
        _run_cmd(a)                       # derselbe Weg wie die Knoepfe im Cockpit


def _ha_loop():
    """Haelt die Verbindung zum HA-Broker. Tut nichts ohne Haekchen."""
    while True:
        try:
            if not (_CFG.get("ha") and _CFG.get("ha_host")):
                time.sleep(10); continue
            if _HA["cli"] is None:
                v, base = _ha_ids()
                c = _ha_client("evcockpit_" + v)
                c.on_connect = _ha_on_connect
                c.on_message = _ha_on_msg
                if _CFG.get("ha_user"):
                    c.username_pw_set(_CFG["ha_user"], _CFG.get("ha_pass") or "")
                c.will_set(base + "/availability", "offline", retain=True)
                c.connect(_CFG["ha_host"], int(_CFG.get("ha_port") or 1883), 60)
                c.loop_start()
                _HA["cli"] = c
        except Exception as e:
            _HA["ok"] = False
            _HA["err"] = str(e)[:110]
            _HA["cli"] = None
            time.sleep(30)
        time.sleep(10)


def _ha_publish(st):
    """Wird nach jedem erfolgreichen Abruf aufgerufen."""
    try:
        if not (_CFG.get("ha") and _HA["cli"] and _HA["ok"]):
            return
        v, base = _ha_ids()
        _HA["cli"].publish(base + "/state", json.dumps(st), retain=True)
        _HA["cli"].publish(base + "/availability", "online", retain=True)
        if st.get("latitude"):
            _HA["cli"].publish(base + "/tracker", "not_home", retain=True)
    except Exception:
        pass


def _ha_test(cfg):
    """Test-Knopf im Assistenten: einmal verbinden, sofort wieder trennen."""
    c = _ha_client("evcockpit_test")
    if cfg.get("ha_user"):
        c.username_pw_set(cfg["ha_user"], cfg.get("ha_pass") or "")
    c.connect(cfg["ha_host"], int(cfg.get("ha_port") or 1883), 10)
    c.disconnect()
    return True


# ---------------------------------------------------------------- Webserver

def _same_origin_request(headers):
    """Reject browser cross-origin POSTs while keeping local CLI clients usable."""
    fetch_site = (headers.get("Sec-Fetch-Site") or "").lower()
    if fetch_site and fetch_site not in ("same-origin", "none"):
        return False
    origin = headers.get("Origin")
    if not origin:
        return True
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and parsed.netloc.lower() == (headers.get("Host") or "").lower()

ENERGY_PANEL = r'''<style>
.energy-shell{margin:28px auto;max-width:1160px;padding:22px;background:#0A2238;border:1px solid #1d4152;border-radius:20px;color:#EAF6F8;
 font:15px/1.5 Inter,"Segoe UI Variable",Segoe UI,sans-serif;scroll-margin-top:84px}
.energy-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;flex-wrap:wrap}.energy-head h2{margin:0;font-size:22px}
.energy-head p{margin:5px 0 0;color:#A9C7CE}.energy-form{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 10px}
.energy-form input,.energy-form button{min-height:42px;padding:10px 12px;border-radius:10px;border:1px solid #1d4152;background:#0f2c40;color:#EAF6F8}
.energy-form input{min-width:210px}.energy-form input[type=number]{min-width:90px;width:100px}.energy-form button{cursor:pointer;font-weight:700}
.energy-form button.primary{background:#5FD6E6;border-color:#5FD6E6}.energy-form button:hover{border-color:#5FD6E6}
.energy-auto{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:18px 0 8px}.energy-auto button{min-height:48px;padding:0 18px;border:0;border-radius:12px;background:#5FD6E6;color:white;font-weight:800;cursor:pointer}
.energy-auto button:disabled{opacity:.6;cursor:wait}.energy-auto span{color:#A9C7CE;font-size:12px}.energy-advanced{margin:10px 0;color:#A9C7CE;font-size:12px}
.energy-advanced summary{cursor:pointer;width:max-content}.energy-placeholder{grid-column:1/-1;padding:20px;border:1px dashed #1d4152;border-radius:14px;color:#A9C7CE;background:#0F1728}
.energy-message{margin:10px 0 14px;color:#A9C7CE;font-size:12px}.lp-ctl{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px;margin:-4px 0 6px}.lp-ctl button,.lp-ctl select{border:1px solid rgba(160,230,240,.22);background:rgba(255,255,255,.04);color:#EAF6F8;border-radius:999px;padding:7px 13px;font-size:12.5px;font-weight:600;cursor:pointer}.lp-ctl .lp-on{background:#B5F23D;color:#1d2a00;border-color:#B5F23D}.lp-ctl .lp-off{color:#A9C7CE;font-weight:500}.energy-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:10px}
.energy-card{background:#0f2c40;border:1px solid #1d4152;border-radius:14px;padding:14px;min-width:0}.energy-card .ek{color:#A9C7CE;font-size:10px;
 letter-spacing:1.2px;text-transform:uppercase;font-weight:800}.energy-card .ev{font-size:22px;font-weight:750;margin-top:5px;overflow-wrap:anywhere}
.energy-card .es{color:#A9C7CE;font-size:12px;margin-top:5px}.vehicle-select{width:100%;display:grid;grid-template-columns:96px minmax(0,1fr) auto;
 grid-column:span 2;align-items:center;gap:12px;text-align:left;background:#0f2c40;border:1px solid #1d4152;color:#EAF6F8;border-radius:14px;padding:12px;cursor:pointer}
.vehicle-select:hover{border-color:#5FD6E6;background:#202B42}.vehicle-select.active{border-color:#43c9db;box-shadow:inset 3px 0 #43c9db}
.vehicle-art{height:52px;display:flex;align-items:center;justify-content:center;border-radius:10px;background:#0A2238}.vehicle-art svg{width:88px;height:44px}
.vehicle-copy{min-width:0}.vehicle-copy strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px}.vehicle-copy small{display:block;color:#A9C7CE;margin-top:3px;font-weight:500}
.vehicle-soc{font:750 19px/1 Inter,"Segoe UI Variable",Segoe UI,sans-serif;color:#EAF6F8;white-space:nowrap}.vehicle-legal{color:#A9C7CE;font-size:11px;margin:8px 2px 0}
.energy-sub{margin:22px 0 9px;font-size:11px;letter-spacing:1.5px;color:#A9C7CE}.energy-discovery{margin-top:12px;color:#A9C7CE;font-size:12px}
@media(max-width:600px){.energy-shell{margin:20px 14px;padding:16px}.energy-form input{width:100%}.energy-form button{flex:1}.vehicle-select{grid-template-columns:76px minmax(0,1fr) auto}.vehicle-art svg{width:70px}}
</style><section id="energy-panel" class="energy-shell">
<div class="energy-head"><div><h2>⚡ Energie &amp; Ladepunkte</h2>
<p>Überblick für Wallboxen, PV, Speicher und Fahrzeuge via evcc (nur lesend; Steuern kommt nach dem Praxistest).</p></div><span id="evcc-health" class="chip">NICHT VERBUNDEN</span></div>
<div class="energy-auto"><button id="evcc-discover">⌕ &nbsp;Geräte automatisch finden</button><span>Kein IP-Wissen nötig</span></div>
<details class="energy-advanced"><summary>Manuell verbinden (Experten)</summary><div class="energy-form"><input id="evcc-host" inputmode="decimal" placeholder="evcc-IP · 192.168.1.20" aria-label="evcc IP-Adresse">
<input id="evcc-port" type="number" value="7070" min="1" max="65535" aria-label="evcc Port">
<button id="evcc-connect" class="primary">Verbinden</button></div></details>
<div id="evcc-message" class="energy-message">Optional – noch nicht verbunden</div>
<div id="evcc-values" class="energy-grid"><div class="energy-placeholder">☀️ Solar wird automatisch angezeigt, sobald evcc oder Home Assistant Werte liefert.</div></div>
<h3 class="energy-sub">FAHRZEUGE &amp; LADEPUNKTE</h3><div id="evcc-points" class="energy-grid"></div>
<div class="vehicle-legal">Fahrzeugformen sind neutrale Illustrationen, keine Herstellerlogos oder exakten Modellabbildungen.</div>
<div id="evcc-discovery" class="energy-discovery"></div>
</section>
<script>
(function(){
 const el=id=>document.getElementById(id), h=el('evcc-host'),p=el('evcc-port');
 h.value=localStorage.getItem('evc_evcc_host')||'';
 p.value=localStorage.getItem('evc_evcc_port')||'7070';
 const card=(name,value,sub='')=>'<div class="energy-card"><div class="ek">'+escapeHtml(__T(name))+'</div><div class="ev">'+value+'</div>'+(sub?'<div class="es">'+sub+'</div>':'')+'</div>';
 const kw=v=>typeof v==='number'&&Number.isFinite(v)?(v/1000).toLocaleString('de-DE',{maximumFractionDigits:2})+' kW':'–';
 const escapeHtml=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const vehicleKind=v=>{const s=[v.icon,v.brand,v.model,v.title].filter(Boolean).join(' ').toLowerCase();
  if(/\bvan\b|bus|buzz|transporter|multivan/.test(s))return'van';
  if(/kombi|wagon|estate|avant|variant|tourer|shooting/.test(s))return'kombi';
  if(/suv|crossover|atto|tang|seal u|q[4-8]|id[. -]?[45]|enyaq|ariya|ix/.test(s))return'suv';
  if(/limo|sedan|saloon|seal|han|a[468]|id[. -]?7|model [3s]/.test(s))return'limo';return'klein';};
 const vehicleGlyph=v=>{const kind=vehicleKind(v), paths={
  klein:'M8 34 11 24c2-5 7-8 15-9l15-2 10-10h26c7 0 11 3 15 10l15 3c7 2 9 7 9 18Z',
  limo:'M7 34 10 25c2-5 7-8 15-9l18-2L56 4h26c7 0 12 3 17 10l17 3c7 2 9 7 9 17Z',
  kombi:'M7 34 10 24c2-5 7-8 15-9l16-2L50 4h43c7 0 11 4 15 11l9 2c7 2 9 7 9 17Z',
  suv:'M7 35 9 20c1-6 7-10 15-11l16-2 11-7h45c7 0 12 5 15 15l10 3c7 2 9 7 9 17Z',
  van:'M7 35 9 12C10 5 15 1 23 1h67c8 0 13 4 17 13l11 5c6 2 8 7 8 16Z'};
  return'<svg viewBox="0 0 134 46" role="img" aria-label="'+escapeHtml(kind)+'"><path d="'+paths[kind]+'" fill="#5FD6E6"/><circle cx="31" cy="35" r="9" fill="#071a2b"/><circle cx="31" cy="35" r="5" fill="#A9C7CE"/><circle cx="104" cy="35" r="9" fill="#071a2b"/><circle cx="104" cy="35" r="5" fill="#A9C7CE"/></svg>';};
 const brandLabel=v=>escapeHtml(v.brand||([v.title,v.model].join(' ').match(/\b(BYD|Audi|VW|Volkswagen|Tesla|BMW|Mercedes|Skoda|Renault|Kia|Hyundai|Volvo|Cupra|Porsche)\b/i)||[])[0]||'EV');
 const kindLabel=k=>__T({klein:'Kompakt',limo:'Limousine',kombi:'Kombi',suv:'SUV',van:'Van'}[k]||'Kompakt');
 let busy=false,timer=null,last=null;
 const schedule=()=>{clearTimeout(timer);timer=setTimeout(refresh,document.hidden?45000:(last&&last.loadpoints&&last.loadpoints.some(x=>x.charging)?7000:15000));};
 async function refresh(){
  if(!h.value||busy)return;busy=true;el('evcc-connect').disabled=true;
  try{
   const started=performance.now();
   const response=await fetch('/energy/state?host='+encodeURIComponent(h.value)+'&port='+encodeURIComponent(p.value),{cache:'no-store'});
   const d=await response.json();if(!response.ok)throw Error(d.error||'API error');last=d;
   const site=d.site||{};
   const gridSub=typeof site.grid_w==='number'?(site.grid_w>30?'Netzbezug':site.grid_w < -30?'Einspeisung':'nahezu ausgeglichen'):'kein Messwert';
   const batterySub=typeof site.battery_w==='number'?(site.battery_w>30?'entlädt':site.battery_w < -30?'lädt':'bereit'):'kein Messwert';
   el('evcc-values').innerHTML=card('PV-Erzeugung',kw(site.pv_w),'aktuelle Leistung')+
    card('Netz',kw(site.grid_w),gridSub)+card('Speicher',kw(site.battery_w),batterySub+(typeof site.battery_soc==='number'?' · '+site.battery_soc.toFixed(0)+' %':''))+
    card('Hausverbrauch',kw(site.home_w),'ohne Ladepunkte')+
    (typeof site.tariff_grid==='number'?card('Netzpreis',(site.tariff_grid*100).toLocaleString('de-DE',{maximumFractionDigits:2})+' ct/kWh',
     typeof site.tariff_feed_in==='number'?'Einspeisung '+(site.tariff_feed_in*100).toLocaleString('de-DE',{maximumFractionDigits:2})+' ct/kWh':'aktueller Tarif'):'')+
    (typeof site.green_share_home==='number'?card('Grünstromanteil',(site.green_share_home*100).toFixed(0)+' %','aktueller Hausverbrauch'):'');
   const vehicles=d.profiles||d.vehicles||[];
   const selected=localStorage.getItem('evc_selected_vehicle')||'';
   const vehicleCards=vehicles.map(v=>{const kind=vehicleKind(v);return'<button type="button" class="vehicle-select '+(selected===v.id?'active':'')+'" data-vehicle="'+escapeHtml(v.id)+'"><span class="vehicle-art">'+vehicleGlyph(v)+'</span><span class="vehicle-copy"><strong>'+escapeHtml(v.title)+'</strong><small>'+brandLabel(v)+' · '+escapeHtml(kindLabel(kind))+'</small></span><span class="vehicle-soc">'+(typeof v.soc==='number'?escapeHtml(Math.round(v.soc))+' %':'–')+'</span></button>';}).join('');
   const chosen=vehicles.find(v=>v.id===selected)||vehicles[0];
   const details=chosen?card('Fahrzeug · '+escapeHtml(chosen.title),
    typeof chosen.soc==='number'?escapeHtml(chosen.soc)+' %':'–',
    (typeof chosen.range_km==='number'?escapeHtml(chosen.range_km)+' km · ':'')+
    escapeHtml(chosen.loadpoint||'kein Ladepunkt')+' · '+kw(chosen.charge_power_w)+' · '+
    (chosen.charging?'lädt':chosen.connected?'angeschlossen':'nicht angeschlossen')):'';

   STEUERN_MOEGLICH=!!d.steuern_moeglich;
   const points=(d.loadpoints||[]).map((x,i)=>card('Ladepunkt · '+escapeHtml(x.title||x.name||i+1),kw(x.chargePower),
    (x.charging?'lädt':x.connected?'Fahrzeug verbunden':'frei')+(x.mode?' · Modus '+escapeHtml(x.mode):'')+
    (typeof x.phasesActive==='number'?' · '+x.phasesActive+' Phase(n)':'')+
    (typeof x.sessionSolarPercentage==='number'?' · '+x.sessionSolarPercentage.toFixed(0)+' % Solar':'')+
    (typeof x.chargedEnergy==='number'?' · '+(x.chargedEnergy/1000).toFixed(1)+' kWh':'')+
    (typeof x.effectiveLimitSoc==='number'?' · Ziel '+x.effectiveLimitSoc+' %':''))+steuerung(x,i,d.steuern_erlaubt||[])).join('');
   el('evcc-points').innerHTML=vehicleCards+details+points||'Noch keine Fahrzeuge oder Ladepunkte in evcc konfiguriert';
   el('evcc-points').querySelectorAll('[data-lp]').forEach(b=>b.addEventListener('click',()=>lpAktion(b.dataset)));
   el('evcc-points').querySelectorAll('select[data-lpziel]').forEach(s=>s.addEventListener('change',()=>
    lpAktion({lp:s.dataset.lpziel,titel:s.dataset.titel,ziel:s.value})));
   el('evcc-points').querySelectorAll('[data-vehicle]').forEach(button=>button.addEventListener('click',()=>{
    localStorage.setItem('evc_selected_vehicle',button.getAttribute('data-vehicle'));refresh();
   }));
   el('evcc-message').textContent='Aktuell · '+new Date().toLocaleTimeString()+' · '+Math.round(performance.now()-started)+' ms · '+
    ((d.steuern_erlaubt||[]).length?__T('Steuern für freigeschaltete Ladepunkte'):__T('nur lesend'));
   el('evcc-health').textContent='VERBUNDEN';el('evcc-health').style.color='#B5F23D';
  }catch(e){el('evcc-message').textContent='evcc: '+e.message;el('evcc-health').textContent='FEHLER';el('evcc-health').style.color='#FF8A6B';}
  finally{busy=false;el('evcc-connect').disabled=false;schedule();}
 }
 // Steuern: nur Modus und Ziel-Ladestand, nur ueber evcc, je Ladepunkt freizuschalten (Standard aus)
 const MODI=[['off','Aus'],['now','Sofort'],['minpv','Min+PV'],['pv','PV']];
 let STEUERN_MOEGLICH=false;
 function steuerung(x,i,frei){if(!STEUERN_MOEGLICH)return '<div class="lp-ctl"><span class="lp-off" style="border:0;padding:4px 0">⚙ '+
   escapeHtml(__T('Wallbox steuern kommt nach dem Praxistest'))+'</span></div>';
  const t=String(x.title||x.name||''),key=(i+1)+':'+t.slice(0,60),an=frei.includes(key),
   a='data-titel="'+escapeHtml(t)+'"';
  if(!an) return '<div class="lp-ctl"><button type="button" class="lp-off" data-lp="'+(i+1)+'" '+a+' data-tun="erlauben">⚙ '+
   escapeHtml(__T('Steuern erlauben'))+'</button></div>';
  const ziele=[50,60,70,80,90,100];
  return '<div class="lp-ctl">'+MODI.map(([m,n])=>'<button type="button" class="'+(x.mode===m||(m==='pv'&&x.mode==='smart')?'lp-on':'')+'" data-lp="'+(i+1)+'" '+a+
   ' data-modus="'+m+'">'+escapeHtml(__T(n))+'</button>').join('')+
   '<select data-lpziel="'+(i+1)+'" '+a+' aria-label="'+escapeHtml(__T('Ziel-Ladestand'))+'">'+
   ziele.map(z=>'<option value="'+z+'"'+(x.limitSoc===z?' selected':'')+'>'+escapeHtml(__T('Ziel'))+' '+z+' %</option>').join('')+
   (typeof x.limitSoc==='number'&&!ziele.includes(x.limitSoc)?'<option selected value="'+x.limitSoc+'">'+x.limitSoc+' %</option>':'')+
   '</select><button type="button" class="lp-off" data-lp="'+(i+1)+'" '+a+' data-tun="sperren">'+escapeHtml(__T('Steuern aus'))+'</button></div>';}
 async function lpAktion(ds){const m=el('evcc-message');
  try{
   if(ds.tun){const an=ds.tun==='erlauben';
    if(an&&!confirm(__T('Steuern für diesen Ladepunkt erlauben? Das Cockpit darf dann über evcc den Lademodus und den Ziel-Ladestand ändern. Mehr nicht.')))return;
    await fetch('/energy/steuern-erlauben',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lp:+ds.lp,titel:ds.titel,an})});
    return refresh();}
   m.textContent='⏳ '+__T('Sende an evcc …');
   const b={host:h.value,port:+p.value||7070,lp:+ds.lp,titel:ds.titel};
   if(ds.ziel)b.limit_soc=+ds.ziel;else b.mode=ds.modus;
   const r=await (await fetch('/energy/steuern',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})).json();
   m.textContent=r.ok?('✅ '+__T('evcc hat übernommen')+(r.mode?' · '+__T('Modus')+' '+r.mode:'')+(typeof r.limit_soc==='number'?' · '+__T('Ziel')+' '+r.limit_soc+' %':''))
    :('⚠️ '+(r.error||__T('evcc hat die Änderung nicht übernommen')+' ('+(r.mode||'?')+', '+(r.limit_soc??'?')+' %)'));
   setTimeout(refresh,1500);
  }catch(e){m.textContent='⚠️ '+e;}}
 el('evcc-connect').onclick=()=>{localStorage.setItem('evc_evcc_host',h.value);localStorage.setItem('evc_evcc_port',p.value);refresh();};
 el('evcc-discover').onclick=async()=>{
  const button=el('evcc-discover');button.disabled=true;button.textContent='⌛ '+__T('Suche im Heimnetz …');el('evcc-discovery').textContent='Das dauert normalerweise nur wenige Sekunden.';
  try{
   const r=await fetch('/energy/discover',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
   const d=await r.json();if(!r.ok)throw Error(d.error||'Fehler');
   const devices=d.found||[],evcc=devices.find(x=>String(x.vendor).toLowerCase()==='evcc');
   if(evcc){h.value=evcc.ip;p.value=evcc.port||7070;localStorage.setItem('evc_evcc_host',h.value);localStorage.setItem('evc_evcc_port',p.value);el('evcc-discovery').textContent='✓ Energiezentrale gefunden und verbunden';refresh();}
   else{el('evcc-discovery').textContent=devices.length?('✓ Gefunden: '+devices.map(x=>x.vendor).join(', ')+' · Für die gemeinsame Energieanzeige bitte evcc verwenden.'):'Keine unterstützte Energiezentrale gefunden. Solar kann alternativ in den Einstellungen über Home Assistant verbunden werden.';}
  }catch(e){el('evcc-discovery').textContent='Automatische Suche nicht möglich: '+e.message;}
  finally{button.disabled=false;button.textContent='⌕  '+__T('Geräte automatisch finden');}
 };
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();else schedule();});if(h.value)refresh();
})();
</script>'''


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype="text/html; charset=utf-8", code=200):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _wizard(self):
        opts = "".join('<option value="%s">%s</option>' % (c, c) for c in COUNTRIES)
        tzs = "".join('<option value="%s">%s</option>' % (t, t) for t in TIMEZONES)
        mods = "".join('<option value="%s">%s</option>' % (m, m) for m in MODELS)
        # Bestehende Einstellungen vorausfuellen, damit man spaeter z.B. nur ein Foto
        # nachreichen kann, ohne alles neu zu tippen. Passwort wird NICHT ausgeliefert.
        vor = {k: _CFG.get(k) for k in ("username", "country_code", "time_zone", "vin", "model",
                                        "battery_kwh", "battery_quelle", "battery_schaetzung", "battery_nenn", "tyre_target", "lan", "count_optin", "show_price",
                                        "poll_min", "sentry", "car_adb", "show_chargers", "charger_url", "update_check", "features",
                                        "planer", "planer_fahrzeug", "planer_fahrten", "karte", "modell3d", "kartenquelle",
                                        "panoptes", "panoptes_url",
                                        "ha", "ha_host", "ha_port", "ha_user",
                                        "pv", "pv_url", "pv_entity",
                                        "datenquelle", "ha_src_url", "ha_src_map")}
        vor["has_pw"] = bool(_CFG.get("password"))
        vor["has_ha_src_token"] = bool(_CFG.get("ha_src_token"))
        vor["has_charger_token"] = bool(_CFG.get("charger_token"))
        vor["has_planer_token"] = bool(_CFG.get("planer_token"))
        vor["planer_geraet"] = str(_CFG.get("planer_token") or "").startswith("g:")
        vor["has_panoptes_jwt"] = bool(_CFG.get("panoptes_jwt"))
        vor["disclaimer_ok"] = _CFG.get("disclaimer_version") == DISCLAIMER_VERSION
        vor["has_panoptes_code"] = bool(_CFG.get("panoptes_code"))
        vor["has_photo"] = PHOTO_FILE.exists()
        vor["vin_known"] = _CFG.get("vin") or ""
        html = (WIZARD.replace("__COUNTRIES__", opts).replace("__TZ__", tzs)
                .replace("__MODELS__", mods).replace("__KWHMAP__", json.dumps(MODELS))
                .replace("__VOR__", json.dumps(vor, ensure_ascii=False)))
        self._send(_i18n(html))

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p in THREE_DATEIEN:
            # three.js fuer das 3D-Auto aus dem Paket (MIT-Lizenz, Version 0.160.0, gegen npm geprueft)
            f = STATIC_DIR / p[len("/static/"):]
            return self._send(f.read_bytes(), THREE_DATEIEN[p]) if f.exists() else self._send(b"", "text/plain", 404)
        if p.startswith("/static/"):
            # Leaflet aus dem Paket ausliefern — bewusst kein CDN, damit niemand Drittes
            # mitbekommt, dass/wann du dein Auto anschaust.
            name = os.path.basename(p)
            f = STATIC_DIR / name
            if p.startswith("/static/fonts/") and re.fullmatch(r"(sora|manrope)-[4-7]00\.woff2", name):
                ff = STATIC_DIR / "fonts" / name
                if ff.exists():
                    return self._send(ff.read_bytes(), "font/woff2")
            if f.exists() and name in ("leaflet.js", "leaflet.css", "maplibre-gl.js", "maplibre-gl.css",
                                       "pmtiles.js", "leaflet-maplibre-gl.js", "panoptes-karte-1.1.0.js"):
                self._send(f.read_bytes(),
                           "text/css" if name.endswith(".css") else "application/javascript")
            else:
                self._send(b"", "text/plain", 404)
        elif p == "/modell3d/info":
            # Gleiche 3D-Modelle wie Panoptes (Manifest auf byd.serveone.at/tiles/models/), mit Pflicht-Namensnennung
            try:
                import modell3d
                mid = modell3d.modell_id(_CFG.get("model"))
                if _CFG.get("modell3d") is not True or not mid:       # nur mit Einwilligung (Regel 2)
                    return self._send(json.dumps({"verfuegbar": False, "still": True}), "application/json")
                try:
                    mani = _MANIFEST.get()
                except Exception as e:
                    print("3D-Modell: Verzeichnis nicht erreichbar:", type(e).__name__, e)
                    return self._send(json.dumps({"verfuegbar": False, "grund": "Modell-Verzeichnis nicht erreichbar (%s)"
                                                  % type(e).__name__}), "application/json")
                m = modell3d.eintrag(mani, mid)
                if not m:
                    return self._send(json.dumps({"verfuegbar": False, "grund": "Modell „%s“ ist gerade nicht verfügbar" % mid}),
                                      "application/json")
                d = modell3d.info(m, mani.get("paintPresets") or [])
                d["farbe"] = _CFG.get("lackfarbe") or ""
                self._send(json.dumps(d), "application/json")
            except Exception as e:
                print("3D-Modell: Fehler:", type(e).__name__, e)
                self._send(json.dumps({"verfuegbar": False, "grund": type(e).__name__}), "application/json")
        elif p == "/modell3d/datei":
            try:
                import modell3d
                m = modell3d.eintrag(_MANIFEST.get(), modell3d.modell_id(_CFG.get("model")))
                if not m or _CFG.get("modell3d") is not True:
                    raise LookupError
                self._send(Path(modell3d.datei(m, str(MODELL_DIR))).read_bytes(), "model/gltf-binary")
            except Exception as e:
                print("3D-Modell: Datei nicht geladen:", type(e).__name__, e)
                self._send(("Modell-Datei nicht geladen (%s)" % type(e).__name__).encode("utf-8"), "text/plain", 404)
        elif p == "/panoptes":
            self._send(_i18n(PANOPTES_SEITE))
        elif p == "/panoptes/einstellungen":
            # Alle Panoptes-Einstellungen, generisch aus dem Schema des Kerns (nur mit Kopplung)
            pv = _panoptes_verbindung()
            if pv is None:
                return self._send(json.dumps({"gekoppelt": False}), "application/json")
            try:
                from panoptes_source import einstellungen_lesen
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                d = einstellungen_lesen(pv, (q.get("sprache") or ["de"])[0])
                self._send(json.dumps(dict(d, gekoppelt=True)), "application/json")
            except Exception as e:
                from panoptes_source import KopplungAbgelaufen
                msg = ("Kopplung abgelaufen — in Panoptes „Gerät koppeln“ wählen und den neuen Code unter "
                       "Einstellungen → Datenquelle eintragen" if isinstance(e, KopplungAbgelaufen)
                       else "Panoptes im Auto nicht erreichbar (%s)" % type(e).__name__)
                self._send(json.dumps({"gekoppelt": True, "fehler": msg}), "application/json")
        elif p == "/about":
            self._send(_i18n(ABOUT.replace("__VERSION__", VERSION)))
        elif p == "/local/capabilities":
            self._send(json.dumps(_local_capabilities()), "application/json")
        elif p == "/sentry.jpg":
            try:
                self._send((CFG_DIR / "sentry.jpg").read_bytes(), "image/jpeg")
            except Exception:
                self._send(b"", "image/jpeg", 404)
        elif p == "/photo":
            try:
                self._send(PHOTO_FILE.read_bytes(), "image/jpeg")
            except Exception:
                self._send(b"", "image/jpeg", 404)
        elif p == "/vehicles/profiles":
            try:
                from vehicle_profiles import read_profiles, combine_profiles
                saved = read_profiles(CFG_DIR / "vehicles.json")
                if _CFG.get("vin") and not any(x["source"] == "byd" for x in saved):
                    saved.insert(0, {"id": "legacy_byd", "title": _CFG.get("model") or "BYD",
                                     "brand": "BYD", "source": "byd", "external_id": ""})
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                external = []
                if q.get("host"):
                    from evcc_backend import get_evcc_state
                    external = get_evcc_state(q["host"][0], int(q.get("port", ["7070"])[0]))["vehicles"]
                legacy = {**_STATE, "_features": _CFG.get("features") or {}}
                self._send(json.dumps({"vehicles": combine_profiles(saved, external, legacy)}), "application/json")
            except Exception as e:
                self._send(json.dumps({"error": str(e)[:160]}), "application/json", 400)
        elif p == "/energy/state":
            try:
                from evcc_backend import get_evcc_state
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                result = get_evcc_state(q["host"][0], int(q.get("port", ["7070"])[0]))
                from vehicle_profiles import read_profiles, combine_profiles
                saved = read_profiles(CFG_DIR / "vehicles.json")
                if _CFG.get("vin") and not any(x["source"] == "byd" for x in saved):
                    saved.insert(0, {"id": "legacy_byd", "title": _CFG.get("model") or "BYD",
                                     "brand": "BYD", "source": "byd", "external_id": ""})
                legacy = {**_STATE, "_features": _CFG.get("features") or {}}
                result["profiles"] = combine_profiles(saved, result["vehicles"], legacy)
                from evcc_backend import STEUERN_FREIGEGEBEN
                result["steuern_moeglich"] = bool(STEUERN_FREIGEGEBEN)
                result["steuern_erlaubt"] = list(_CFG.get("evcc_steuern") or []) if STEUERN_FREIGEGEBEN else []
                self._send(json.dumps(result), "application/json")
            except Exception as e:
                self._send(json.dumps({"error": str(e)[:160]}), "application/json", 400)
        elif p == "/karten":
            # Meine Ladekarten: Tarifliste (oeffentlich, 1 h zwischengespeichert) + eigene Auswahl beim Planer
            try:
                from planer_bridge import tarife, meine_karten
                if time.time() - _TARIFE["t"] > 3600 or not _TARIFE["d"]:
                    _TARIFE.update(t=time.time(), d=tarife())
                an = bool(_CFG.get("planer") and _CFG.get("planer_token"))
                meine, fehler = None, ""
                if an:
                    try:
                        meine = meine_karten(_CFG["planer_token"])
                    except Exception as e:
                        an, fehler = False, ("Planer-Link ungültig oder abgelaufen — bitte in den Einstellungen neu eintragen"
                                             if "401" in str(e) else "Planer nicht erreichbar (%s)" % type(e).__name__)
                if meine is not None and meine != _CFG.get("planer_karten"):
                    _CFG["planer_karten"] = meine
                    save_cfg(_CFG)
                self._send(json.dumps({"an": an, "tarife": _TARIFE["d"], "meine": meine, "fehler": fehler}),
                           "application/json")
            except Exception as e:
                self._send(json.dumps({"an": False, "fehler": "Planer nicht erreichbar (%s)" % type(e).__name__}),
                           "application/json")
        elif p == "/planer/route":
            # Bereitliegende Route + Rueckmeldung aus dem Auto (liest nur, Schluessel bleibt hier)
            try:
                if not (_CFG.get("planer") and _CFG.get("planer_token")):
                    return self._send(json.dumps({"an": False}), "application/json")
                jetzt = time.time()
                if jetzt - _ROUTE["t"] > 30:
                    from planer_bridge import route_kurz
                    _ROUTE.update(t=jetzt, d=route_kurz(_CFG["planer_token"], _planer_kennung()), fehler="")
                self._send(json.dumps({"an": True, "route": _ROUTE["d"], "fehler": _ROUTE["fehler"]}), "application/json")
            except Exception as e:
                _ROUTE.update(t=time.time(), fehler="Planer nicht erreichbar (%s)" % type(e).__name__)
                self._send(json.dumps({"an": True, "route": _ROUTE["d"], "fehler": _ROUTE["fehler"]}), "application/json")
        elif p == "/planer/oeffnen":
            from planer_bridge import oeffnen_url
            self.send_response(302)
            self.send_header("Location", oeffnen_url(_CFG.get("planer_token") or ""))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif p == "/data":
            if "sichtbar=1" in (urllib.parse.urlparse(self.path).query or ""):
                _TAKT["sichtbar_ts"] = time.time()
            d = dict(_STATE)
            d["abfrage"] = abfrage_status()
            if _STATE.get("_poll_ts"):
                d["daten_alter_s"] = max(0, int(time.time() - _STATE["_poll_ts"]))
            # Entfernungen IMMER aus der aktuellen Position rechnen — sonst zeigt die Liste
            # nach dem Losfahren noch die Entfernungen vom alten Standort.
            _la, _lo = _STATE.get("latitude"), _STATE.get("longitude")
            if _la and _lo and d.get("chargers"):
                _f = []
                for _c in d["chargers"]:
                    _c = dict(_c)
                    _c["km"] = round(_dist_km(_la, _lo, _c["lat"], _c["lon"]), 1)
                    _f.append(_c)
                d["chargers"] = sorted(_f, key=lambda x: x["km"])
            d["photo"] = _CFG.get("photo") or ""
            import geheim
            d["geheim_warnung"] = geheim.WARNUNG              # Rueckfall ohne Schluesselbund: ehrlich sagen
            d["model"] = _CFG.get("model") or "Elektrofahrzeug"
            d["reifen"] = _reifen_urteil(_STATE)
            d["features"] = _CFG.get("features") or {}
            # Kein eigenes Foto -> welche Silhouette passt zum Modell?
            if not d["photo"]:
                d["silhouette"] = BODY_TYPE.get(_CFG.get("model") or "", "klein")
            d["lan_url"] = ("http://%s:%d" % (lan_ip(), WEBPORT)) if _CFG.get("lan") else ""
            d["sentry_on"] = bool(_CFG.get("sentry"))
            d["panoptes_an"] = _panoptes_gekoppelt()
            d["planer"] = dict(_PLANER.status if _PLANER else {},
                               an=bool(_CFG.get("planer") and _CFG.get("planer_token")))
            if _MSG["text"] and time.time() - _MSG["ts"] < 120:
                d["_msg"] = _MSG["text"]
            self._send(json.dumps(d), "application/json")
        elif p == "/setup" or not _CFG.get("vin"):
            self._wizard()
        else:
            stil = KARTE_STIL if _kartenquelle() == "community" else ""       # nur mit Einwilligung (Regel 2)
            einw = {"fragen": _CFG.get("einwilligung_stand") != EINWILLIGUNG_STAND, "kartenquelle": _kartenquelle(),
                    "modell3d": _CFG.get("modell3d") is True}
            self._send(_i18n(COCKPIT.replace("__KARTENSTIL__", stil).replace("__EINWILLIGUNG__", json.dumps(einw))
                             .replace("<!--ENERGIE-PANEL-->", ENERGY_PANEL)))

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if not _same_origin_request(self.headers):
            return self._send(json.dumps({"error": "Cross-origin request blocked"}), "application/json", 403)
        try:
            ln = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(json.dumps({"error": "Invalid Content-Length"}), "application/json", 400)
        if ln < 0 or ln > 2 * 1024 * 1024:
            return self._send(json.dumps({"error": "Request body too large"}), "application/json", 413)
        raw = self.rfile.read(ln).decode("utf-8") if ln else "{}"
        if u.path == "/jetzt":
            nutzer_aktion()
            return self._send(json.dumps({"ok": True}), "application/json")
        if u.path == "/abfrage":
            try:
                c = json.loads(raw or "{}")
                for feld, key in (("geparkt", "abfrage_geparkt"), ("fahrt", "abfrage_fahrt")):
                    if feld in c:
                        v = int(c[feld])
                        if v not in ABFRAGE_WAHL:
                            raise ValueError("Ungültiger Takt")
                        _CFG[key] = v
                save_cfg(_CFG)
                nutzer_aktion()
                return self._send(json.dumps({"ok": True, "abfrage": abfrage_status()}), "application/json")
            except Exception as e:
                return self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json", 400)
        if u.path in ("/energy/steuern-erlauben", "/energy/steuern"):
            # Wallbox steuern NUR ueber evcc und NUR fuer Ladepunkte, die der Nutzer ausdruecklich
            # freigeschaltet hat (Standard aus). evcc kuemmert sich um Phasen, Stromgrenzen, Schutz.
            try:
                from evcc_backend import STEUERN_FREIGEGEBEN
                if not STEUERN_FREIGEGEBEN:          # 1.6: fest aus bis zum Praxistest - nichts geht an evcc
                    raise PermissionError("Wallbox steuern kommt nach dem Praxistest")
                b = json.loads(raw)
                lp = int(b.get("lp"))
                schluessel = "%d:%s" % (lp, str(b.get("titel") or "")[:60])
                frei = list(_CFG.get("evcc_steuern") or [])
                if u.path == "/energy/steuern-erlauben":
                    frei = [x for x in frei if x != schluessel] + ([schluessel] if b.get("an") else [])
                    _CFG["evcc_steuern"] = frei
                    save_cfg(_CFG)
                    return self._send(json.dumps({"ok": True, "steuern_erlaubt": frei}), "application/json")
                if schluessel not in frei:
                    raise ValueError("Steuern ist für diesen Ladepunkt nicht freigeschaltet")
                from evcc_backend import set_loadpoint
                ziel = b.get("limit_soc")
                r = set_loadpoint(str(b.get("host") or ""), int(b.get("port") or 7070), lp,
                                  mode=b.get("mode"), limit_soc=int(ziel) if ziel is not None else None)
                self._send(json.dumps(r), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
        elif u.path in ("/route/plan", "/route/orte", "/route/an-auto"):
            # Route-Reiter: Schluessel bleibt hier; Koordinaten nur im Body, nie im Log (Regel 2: nur auf Klick)
            try:
                if not (_CFG.get("planer") and _CFG.get("planer_token")):
                    raise ValueError("Erst mit dem Routenplaner verbinden (Einstellungen → Extras)")
                import route_planer as rp
                tok, w = _CFG["planer_token"], json.loads(raw or "{}")
                if u.path == "/route/orte":
                    return self._send(json.dumps({"ok": True, "orte": rp.orte(tok, w.get("q"))}), "application/json")
                if u.path == "/route/plan":
                    pos = (_STATE.get("latitude"), _STATE.get("longitude")) if _STATE.get("latitude") else None
                    body = rp.anfrage_body(w, pos, _STATE.get("soc"), _planer_profil(tok), _planer_kennung())
                    k = rp.planen(tok, body)
                    _RPLAN.clear()
                    _RPLAN.update(k=k, start=body["start"], ziel=body["ziel"], fahrzeug=body["fahrzeug"],
                                  start_name=(str(w.get("start_name") or "") if w.get("start") else "Mein Auto")[:80],
                                  ziel_name=str(w.get("ziel_name") or "")[:80], t=time.time())
                    return self._send(json.dumps({"ok": True, "route": k}), "application/json")
                if not _RPLAN.get("k") or time.time() - _RPLAN["t"] > 3600:
                    raise ValueError("Bitte zuerst eine Route berechnen")
                plan = rp.fuer_auto(_RPLAN["k"], _RPLAN["start"], _RPLAN["ziel"], _RPLAN["start_name"],
                                    _RPLAN["ziel_name"], _RPLAN["fahrzeug"])
                d = rp.an_auto(tok, plan, _planer_kennung())
                _ROUTE["t"] = 0
                self._send(json.dumps({"ok": True, "gueltig_bis": d.get("gueltig_bis")}), "application/json")
            except ValueError as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": "Routenplaner nicht erreichbar (%s)" % type(e).__name__}),
                           "application/json")
        elif u.path == "/karten":
            try:
                if not (_CFG.get("planer") and _CFG.get("planer_token")):
                    raise ValueError("Erst mit dem Routenplaner verbinden (Einstellungen → Extras)")
                from planer_bridge import setze_karten
                meine = setze_karten(_CFG["planer_token"], json.loads(raw).get("karten") or [])
                _CFG["planer_karten"] = meine
                save_cfg(_CFG)
                self._send(json.dumps({"ok": True, "meine": meine}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
        elif u.path == "/modell3d/farbe":
            try:
                hexf = str(json.loads(raw).get("farbe") or "")
                if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hexf):
                    raise ValueError("Farbe als #RRGGBB")
                _CFG["lackfarbe"] = hexf.upper()
                save_cfg(_CFG)
                self._send(json.dumps({"ok": True, "farbe": _CFG["lackfarbe"]}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:120]}), "application/json")
        elif u.path == "/panoptes/einstellungen":
            # Speichern: nur geaenderte, erlaubte Felder (nurLesendExtern NIE), dann zuruecklesen.
            pv = _panoptes_verbindung()
            try:
                if pv is None:
                    raise ValueError("Panoptes ist nicht gekoppelt")
                import einstellungen
                from panoptes_source import einstellungen_lesen, einstellungen_schreiben
                b = json.loads(raw)
                sprache = b.get("sprache") or "de"
                stand = einstellungen_lesen(pv, sprache)
                body, lokal = einstellungen.vorbereiten(stand["schema"], stand["werte"], b.get("werte") or {},
                                                        b.get("bestaetigt") or [])
                antwort = {"ok": not lokal, "fehler": dict(lokal), "gespeichert": {}}
                if body["werte"]:
                    if b.get("etag") and b["etag"] != (stand["werte"] or {}).get("etag"):
                        antwort = {"ok": False, "grund": "veraltet", "fehler": dict(lokal), "gespeichert": {}}
                    else:
                        r = einstellungen_schreiben(pv, body)
                        if r.get("_status") == 409:
                            antwort = {"ok": False, "grund": "veraltet", "fehler": dict(lokal), "gespeichert": {}}
                        else:
                            antwort = {"ok": bool(r.get("ok")) and not lokal, "gespeichert": r.get("gespeichert") or {},
                                       "fehler": dict(lokal, **(r.get("fehler") or {}))}
                antwort["neu"] = einstellungen_lesen(pv, sprache)        # zuruecklesen
                self._send(json.dumps(antwort), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "grund": str(e)[:160]}), "application/json")
        elif u.path == "/live/umkreis":
            # Live-Belegung fuer die Community-Karte: nur mit Haekchen "Ladesaeulen" und Community-Karte.
            # Der Planer bekommt nur den auf ~5 km gerundeten Kartenmittelpunkt, per POST (kein Log).
            leer = json.dumps({"stationen": [], "live_quellen": []})
            if not _CFG.get("show_chargers") or _kartenquelle() != "community":
                return self._send(leer, "application/json")
            try:
                d = _LIVE.abfrage(json.loads(raw), karten=_CFG.get("planer_karten") or ())
                self._send(json.dumps(d), "application/json")
            except Exception:
                self._send(leer, "application/json")
        elif u.path == "/energy/discover":
            try:
                from device_hub import automatic_lan_network, discover
                payload = json.loads(raw)
                network = payload.get("cidr") or automatic_lan_network()
                found = discover(network)
                self._send(json.dumps({"found": [{k: v for k, v in item.items() if k != "data"} for item in found]}), "application/json")
            except Exception as e:
                self._send(json.dumps({"error": str(e)[:160]}), "application/json", 400)
        elif u.path == "/photo/upload":
            try:
                import base64
                photo = json.loads(raw).get("photo", "")
                if not photo.startswith("data:image/jpeg;base64,"):
                    raise ValueError("Bitte eine normale Bilddatei auswählen")
                content = base64.b64decode(photo.split(",", 1)[1], validate=True)
                if not 100 <= len(content) <= 1_500_000 or not content.startswith(b"\xff\xd8\xff"):
                    raise ValueError("Das Foto ist ungültig oder zu groß")
                CFG_DIR.mkdir(parents=True, exist_ok=True)
                tmp = PHOTO_FILE.with_suffix(".tmp")
                tmp.write_bytes(content)
                os.replace(tmp, PHOTO_FILE)
                _CFG["photo"] = "/photo"
                save_cfg(_CFG)
                self._send(json.dumps({"ok": True}), "application/json")
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:140]}), "application/json", 400)
        elif u.path == "/vehicles/profiles":
            try:
                from vehicle_profiles import write_profiles
                payload = json.loads(raw)
                profiles = write_profiles(CFG_DIR / "vehicles.json", payload["profiles"])
                self._send(json.dumps({"ok": True, "profiles": profiles}), "application/json")
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as e:
                self._send(json.dumps({"error": str(e)[:160]}), "application/json", 400)
        elif u.path == "/detect":
            try:
                vs = asyncio.run(_fetch_vehicles(json.loads(raw)))
                if not vs:
                    self._send(json.dumps({"ok": False, "error": "Keine Fahrzeuge gefunden — stimmen Login/Land?"}),
                               "application/json")
                else:
                    self._send(json.dumps({"ok": True, "vehicles": vs}), "application/json")
            except Exception as e:
                blocked = _auth_failure(e)
                if blocked:
                    _STATE["_auth_blocked"] = True
                self._send(json.dumps({"ok": False, "error": _friendly(e),
                                       "auth_blocked": blocked}), "application/json")
        elif u.path == "/pv_entities":
            try:
                c = json.loads(raw)
                lst = _ha_power_entities(c["pv_url"], c["pv_token"])
                self._send(json.dumps({"ok": True, "entities": lst}), "application/json")
            except Exception as e:
                m = str(e)
                if "401" in m or "403" in m:
                    m = "Token abgelehnt — stimmt er? (HA: Profil → Sicherheit → Token erstellen)"
                elif "refused" in m.lower() or "timed out" in m.lower():
                    m = "Kein Kontakt zu Home Assistant — Adresse richtig? (z.B. http://192.168.0.10:8123)"
                self._send(json.dumps({"ok": False, "error": m[:140]}), "application/json")
        elif u.path == "/caps":
            try:
                c = json.loads(raw)
                lst = asyncio.run(_fetch_caps(c, c["vin"]))
                self._send(json.dumps({"ok": True, "features": lst}), "application/json")
            except Exception as e:
                blocked = _auth_failure(e)
                if blocked:
                    _STATE["_auth_blocked"] = True
                self._send(json.dumps({"ok": False, "error": _friendly(e),
                                       "auth_blocked": blocked}), "application/json")
        elif u.path == "/ha_test":
            try:
                _ha_test(json.loads(raw))
                self._send(json.dumps({"ok": True}), "application/json")
            except Exception as e:
                m = str(e)
                if "refused" in m.lower() or "111" in m:
                    m = "Keine Verbindung — Adresse/Port richtig? Läuft der Broker (Mosquitto-Add-on)?"
                elif "not authorised" in m.lower() or "auth" in m.lower() or "5" == m.strip():
                    m = "Broker weist ab — Benutzer/Passwort prüfen."
                self._send(json.dumps({"ok": False, "error": m[:130]}), "application/json")
        elif u.path == "/haquelle/vorschlag":
            # Assistent: Sensoren in Home Assistant finden und passende vorschlagen (nur lesen)
            try:
                import ha_quelle
                b = json.loads(raw)
                url = (b.get("url") or "").strip() or _CFG.get("ha_src_url", "")
                token = (b.get("token") or "").strip() or _CFG.get("ha_src_token", "")
                if not (url and token):
                    raise ValueError("Bitte Adresse und Zugriffs-Token eintragen")
                v = ha_quelle.vorschlag(ha_quelle.hole_states(url, token))
                gesp = _CFG.get("ha_src_map") or {}
                for f, x in v.items():
                    if gesp.get(f) and any(k["id"] == gesp[f] for k in x["kandidaten"]):
                        x["wahl"] = gesp[f]          # beim Aendern die eigene Wahl behalten
                self._send(json.dumps({"ok": True, "felder": v}), "application/json")
            except urllib.error.HTTPError as e:
                self._send(json.dumps({"ok": False, "error": "Home Assistant lehnt ab (%s) — Token prüfen" % e.code}),
                           "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": ("Home Assistant nicht erreichbar: %s" % e)[:160]}),
                           "application/json")
        elif u.path == "/einwilligung":
            # Regel 2: Kartenquelle und 3D-Modell ausdruecklich waehlen (einmaliger Hinweis bzw. direkt in der Karte)
            try:
                c = json.loads(raw or "{}")
                if "kartenquelle" in c:
                    if c["kartenquelle"] not in ("keine", "osm", "community"):
                        raise ValueError("unbekannte Kartenquelle")
                    _CFG["kartenquelle"] = c["kartenquelle"]
                    _CFG["karte"] = "community" if c["kartenquelle"] == "community" else "osm"
                if "modell3d" in c:
                    _CFG["modell3d"] = c["modell3d"] is True
                _CFG["einwilligung_stand"] = EINWILLIGUNG_STAND
                save_cfg(_CFG)
                self._send(json.dumps({"ok": True}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:120]}), "application/json")
        elif u.path == "/panoptes/anfrage":
            # Kopplung per Anfrage (KOPPLUNG_ANFRAGE.md v1.1): Pruefzahl zeigen, erlaubt wird in Telegram/Web/Display
            try:
                import panoptes_source as ps
                c = json.loads(raw or "{}")
                url = (c.get("url") or _CFG.get("panoptes_url") or "").strip().rstrip("/")
                if not url.startswith(("http://", "https://")):
                    raise ValueError("Adresse bitte mit http:// oder https:// angeben (z. B. http://100.x.x.x:8180)")
                pz, geraet = ps.neue_pruefzahl(), ps.geraetename()
                try:
                    r = ps.kopplung_anfrage(url, geraet, pz)
                except Exception as e:
                    raise ValueError("Panoptes unter dieser Adresse nicht erreichbar (%s). Auto an, Adresse richtig?" % type(e).__name__)
                if not r["ok"]:
                    raise ValueError(_KOPPLUNG_GRUND.get(r["grund"], "Panoptes lehnt die Anfrage ab (%s)" % r["grund"]))
                _PAN_ANFRAGE.update(url=url, id=r["id"], bis=time.time() + 130)
                self._send(json.dumps({"ok": True, "pruefzahl": pz, "geraet": geraet, "webseite": url + "/system.html"}),
                           "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:220]}), "application/json")
        elif u.path == "/panoptes/anfrage/status":
            try:
                import panoptes_source as ps
                if not _PAN_ANFRAGE.get("id"):
                    raise ValueError("Keine offene Anfrage. Bitte „Mit Panoptes verbinden“ drücken.")
                try:
                    r = ps.kopplung_status(_PAN_ANFRAGE["url"], _PAN_ANFRAGE["id"])
                except Exception:
                    r = {"status": "wartet"}               # kurz nicht erreichbar: weiter warten bis zum Ablauf
                st = r["status"]
                if st == "wartet" and time.time() > _PAN_ANFRAGE["bis"]:
                    st = "abgelaufen"
                if st == "erlaubt":
                    url = _PAN_ANFRAGE["url"]
                    _PAN_ANFRAGE.update(id="")
                    _PAN_TEST.update(url=url, jwt=r["jwt"], verbraucht=True, kopplung_id=r.get("kopplungId", ""))
                    soc = None
                    try:
                        from panoptes_source import Panoptes
                        soc = (Panoptes(url, "", r["jwt"]).lies() or {}).get("soc")
                    except Exception:
                        pass
                    return self._send(json.dumps({"ok": True, "status": "erlaubt", "soc": soc, "url": url}), "application/json")
                if st != "wartet":
                    _PAN_ANFRAGE.update(id="")
                    raise ValueError(_KOPPLUNG_STATUS.get(st, _KOPPLUNG_STATUS["fehler"]))
                self._send(json.dumps({"ok": True, "status": "wartet"}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "status": "fehler", "error": str(e)[:220]}), "application/json")
        elif u.path == "/planer/verbinden":
            # Mit dem Routenplaner verbinden ohne Abtippen (API §6): Code + Link, Mensch erlaubt auf /ev/verbinden
            try:
                import planer_bridge as pb
                import panoptes_source as ps
                try:
                    r = pb.geraet_start(ps.geraetename())
                except Exception as e:
                    raise ValueError("Routenplaner nicht erreichbar (%s). Später nochmal versuchen." % type(e).__name__)
                _PLANER_NEU.update(poll=r["pollId"], token="", bis=time.time() + r["ablauf_s"])
                self._send(json.dumps({"ok": True, "code": r["code"], "link": r["link"], "ablauf_s": r["ablauf_s"]}),
                           "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:220]}), "application/json")
        elif u.path == "/planer/verbinden/status":
            try:
                import planer_bridge as pb
                if not _PLANER_NEU.get("poll"):
                    raise ValueError("Keine offene Verbindung. Bitte „Mit Routenplaner verbinden“ drücken.")
                try:
                    r = pb.geraet_abholen(_PLANER_NEU["poll"])
                except Exception:
                    r = {"status": "wartet"}
                st = "wartet" if r["status"] == "fehler" else r["status"]
                if st == "wartet" and time.time() > _PLANER_NEU["bis"]:
                    st = "abgelaufen"
                if st == "erlaubt":
                    _PLANER_NEU.update(poll="", token=r["token"])
                    return self._send(json.dumps({"ok": True, "status": "erlaubt"}), "application/json")
                if st != "wartet":
                    _PLANER_NEU.update(poll="")
                    raise ValueError({"abgelehnt": "Auf dem Routenplaner abgelehnt.",
                                      "abgelaufen": "Nicht rechtzeitig bestätigt (10 Minuten). Bitte nochmal verbinden."}
                                     .get(st, "Unerwartete Antwort vom Routenplaner. Bitte nochmal verbinden."))
                self._send(json.dumps({"ok": True, "status": "wartet"}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "status": "fehler", "error": str(e)[:220]}), "application/json")
        elif u.path == "/panoptes/test":
            try:
                from panoptes_source import Panoptes
                c = json.loads(raw or "{}")
                url = (c.get("url") or _CFG.get("panoptes_url") or "").strip()
                code = (c.get("code") or _CFG.get("panoptes_code") or "").strip()
                from panoptes_source import aus_kopplungslink
                lk = aus_kopplungslink(code)
                if lk:
                    url, code = lk
                if not url.startswith(("http://", "https://")):
                    raise ValueError("Adresse bitte mit http:// oder https:// angeben")
                pt = Panoptes(url, code, "" if code else _CFG.get("panoptes_jwt", ""))
                st = pt.lies()
                if not st:
                    if pt.letzter_fehler == "kopplung_abgelaufen":
                        raise ValueError("Kopplung abgelaufen — in Panoptes „Gerät koppeln“ wählen und den neuen Code eintragen")
                    raise ValueError("Keine Antwort mit Daten — Auto an? Adresse und Kopplungs-Code (10 min gültig, einmal verwendbar) richtig?")
                _PAN_TEST.update(url=url, jwt=pt.jwt, verbraucht=pt.code_verbraucht, kopplung_id="")
                self._send(json.dumps({"ok": True, "soc": st.get("soc"), "url": url}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
        elif u.path == "/planer/fahrzeuge":
            try:
                import planer_bridge as pb
                c = json.loads(raw or "{}")
                tok = pb.token_aus_link(c.get("link", "")) or _PLANER_NEU.get("token") or _CFG.get("planer_token", "")
                if not tok:
                    raise ValueError("Bitte zuerst „Mit Routenplaner verbinden“")
                if not pb.pruefe_token(tok):
                    raise ValueError("Der Planer kennt diesen Link nicht - bitte den persönlichen Link aus der E-Mail nehmen")
                liste = pb.fahrzeuge(tok)
                vorschlag = pb.passendes_profil(liste, c.get("model") or _CFG.get("model"),
                                                float(c.get("battery_kwh") or _CFG.get("battery_kwh") or 0))
                self._send(json.dumps({"ok": True, "fahrzeuge": liste, "vorschlag": vorschlag}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
        elif u.path == "/save":
            try:
                c = json.loads(raw)
                quelle = c.get("datenquelle") or "byd"
                if quelle not in ("byd", "ha", "panoptes"):
                    raise ValueError("Unbekannte Datenquelle")
                c["datenquelle"] = quelle
                if quelle != "byd" and not c.get("vin"):
                    # Ohne BYD-Konto keine VIN: lokale Zufallskennung (nie eine echte VIN)
                    alt = str(_CFG.get("vin") or "")
                    c["vin"] = alt if alt.startswith("lokal-") else "lokal-" + uuid.uuid4().hex[:10]
                if not c.get("vin"):
                    raise ValueError("VIN fehlt")
                if not c.get("ha_src_token") and _CFG.get("ha_src_token"):
                    c["ha_src_token"] = _CFG["ha_src_token"]
                if quelle == "ha":
                    if not (c.get("ha_src_url") and c.get("ha_src_token")):
                        raise ValueError("Für Home Assistant bitte Adresse und Zugriffs-Token eintragen")
                    if not (c.get("ha_src_map") or {}).get("soc"):
                        raise ValueError("Bitte in Home Assistant den Sensor für den Ladestand auswählen")
                if quelle == "panoptes":
                    c["panoptes"] = True
                # Passwortfeld leer gelassen -> gespeichertes Passwort behalten
                if not c.get("password") and _CFG.get("password"):
                    c["password"] = _CFG["password"]
                if not c.get("control_pin") and _CFG.get("control_pin"):
                    c["control_pin"] = _CFG["control_pin"]
                if not c.get("ha_pass") and _CFG.get("ha_pass"):
                    c["ha_pass"] = _CFG["ha_pass"]
                if not c.get("pv_token") and _CFG.get("pv_token"):
                    c["pv_token"] = _CFG["pv_token"]
                if not c.get("charger_token") and _CFG.get("charger_token"):
                    c["charger_token"] = _CFG["charger_token"]
                if not c.get("panoptes_code") and _CFG.get("panoptes_code"):
                    c["panoptes_code"] = _CFG["panoptes_code"]
                if c.get("panoptes_url") == _CFG.get("panoptes_url") and _CFG.get("panoptes_jwt") \
                        and c.get("panoptes_code") == _CFG.get("panoptes_code"):
                    c["panoptes_jwt"] = _CFG["panoptes_jwt"]
                if c.get("panoptes_url") == _CFG.get("panoptes_url"):
                    for k in ("panoptes_kopplung_id", "panoptes_erneuert"):
                        if _CFG.get(k):
                            c[k] = _CFG[k]
                if c.get("panoptes_url") and c.get("panoptes_url").rstrip("/") == _PAN_TEST.get("url", "").rstrip("/") \
                        and _PAN_TEST.get("jwt"):
                    c["panoptes_jwt"] = _PAN_TEST["jwt"]          # beim Test bzw. per erlaubter Anfrage gekoppelt
                    c["panoptes_erneuert"] = time.time()
                    if _PAN_TEST.get("kopplung_id"):
                        c["panoptes_kopplung_id"] = _PAN_TEST["kopplung_id"]   # zum Widerrufen
                    if _PAN_TEST.get("verbraucht"):
                        c["panoptes_code"] = ""                    # einmal verwendbar - nicht aufheben
                if c.get("panoptes") and not (c.get("panoptes_url") and (c.get("panoptes_code") or c.get("panoptes_jwt"))):
                    raise ValueError("Für Panoptes bitte zuerst „Mit Panoptes verbinden“ (oder unter „Erweitert“ den Kopplungs-Code)")
                from planer_bridge import token_aus_link
                link = c.pop("planer_link", "") or ""
                c["planer_token"] = token_aus_link(link) or _PLANER_NEU.get("token") or ("" if link else _CFG.get("planer_token", ""))
                if c.get("planer") and not c["planer_token"]:
                    raise ValueError("Bitte zuerst „Mit Routenplaner verbinden“ (oder unter „Erweitert“ den persönlichen Link)")
                if c.get("kartenquelle") not in ("keine", "osm", "community"):
                    c["kartenquelle"] = "keine"
                c["einwilligung_stand"] = EINWILLIGUNG_STAND          # im Assistenten ausdruecklich gewaehlt
                # Hinweise (Haftung) im ersten Schritt bestaetigt: Version + Zeitpunkt merken
                if c.pop("disclaimer_ok", None) is not True:
                    raise ValueError("Bitte im ersten Schritt die Hinweise bestätigen")
                c["disclaimer_version"] = DISCLAIMER_VERSION
                c["disclaimer_zeit"] = (_CFG.get("disclaimer_zeit") if _CFG.get("disclaimer_version") == DISCLAIMER_VERSION
                                        else None) or time.time()
                # Foto als Datei ablegen (nicht in die config.json quetschen)
                pd = c.pop("photo_data", "") or ""
                if pd.startswith("data:image"):
                    import base64
                    CFG_DIR.mkdir(parents=True, exist_ok=True)
                    PHOTO_FILE.write_bytes(base64.b64decode(pd.split(",", 1)[1]))
                    c["photo"] = "/photo"
                elif PHOTO_FILE.exists():
                    c["photo"] = "/photo"          # vorhandenes Foto behalten
                # Zufalls-ID nur anlegen, wenn wirklich mitgezaehlt werden soll
                if c.get("count_optin"):
                    c["install_id"] = _CFG.get("install_id") or uuid.uuid4().hex[:16]
                else:
                    c.pop("install_id", None)      # Haekchen weg -> ID weg ...
                    if _CFG.get("install_id"):
                        c["_ping_loeschen"] = _CFG["install_id"]   # ... und beim Server loeschen lassen
                if _CFG.get("_ping_loeschen") and not c.get("_ping_loeschen"):
                    c["_ping_loeschen"] = _CFG["_ping_loeschen"]
                # Planer-Kennung des Autos bleibt dieselbe, sonst saehe der Planer nach jedem Speichern
                # ein "neues" Auto. Nur bei anderem Fahrzeug (VIN) eine neue.
                if _CFG.get("planer_auto") and c.get("vin") == _CFG.get("vin"):
                    c["planer_auto"] = _CFG["planer_auto"]
                for k in ABFRAGE_STD:                 # im Cockpit eingestellt, nicht im Assistenten
                    if k in _CFG and k not in c:
                        c[k] = _CFG[k]
                # Akku-kWh: von Hand eingetippt -> bleibt; unveraendert -> Herkunft behalten; sonst Listenwert
                if c.pop("battery_kwh_hand", False):
                    c["battery_quelle"] = "manuell"
                elif abs(float(c.get("battery_kwh") or 0) - float(_CFG.get("battery_kwh") or 0)) < 0.05 \
                        and _CFG.get("battery_quelle"):
                    for k in ("battery_quelle", "battery_schaetzung", "battery_nenn"):
                        if _CFG.get(k) is not None:
                            c[k] = _CFG[k]
                else:
                    c.pop("battery_quelle", None)
                c.pop("auth_blocked", None)       # bewusstes Speichern erlaubt genau einen neuen Versuch
                save_cfg(c)
                load_cfg()
                _STATE.clear()
                threading.Thread(target=ping_optin, daemon=True).start()
                self._send(json.dumps({"ok": True}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
        elif u.path == "/cmd":
            nutzer_aktion()
            a = (urllib.parse.parse_qs(u.query).get("a") or [""])[0]
            if a in ERLAUBTE_BEFEHLE and a not in NIE:     # Aufsperren gibt es nie (Alfred, 21.10.)
                _run_cmd(a)
                self._send(json.dumps({"ok": True}), "application/json")
            else:
                self._send(json.dumps({"ok": False}), "application/json")
        elif u.path == "/logout":
            # Abmelden: Zugangsdaten und Fahrzeugdaten vom Rechner loeschen.
            try:
                for f in (CFG_FILE, CACHE_FILE, PHOTO_FILE):
                    if f.exists():
                        f.unlink()
                _CFG.clear()
                _STATE.clear()
                self._send(json.dumps({"ok": True}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:120]}), "application/json")
        else:
            self._send(json.dumps({"ok": False}), "application/json", 404)


def main():
    global BIND
    load_cfg()
    # Haekchen "auch im Heimnetz" aus dem Assistenten; ENV schlaegt alles (fuer NAS/Profis)
    if not os.environ.get("EVCOCKPIT_BIND"):
        BIND = "0.0.0.0" if _CFG.get("lan") else "127.0.0.1"
    threading.Thread(target=_poller, daemon=True).start()
    threading.Thread(target=ping_optin, daemon=True).start()   # tut nichts ohne Einwilligung
    threading.Thread(target=_price_loop, daemon=True).start()  # tut nichts ohne Haekchen
    threading.Thread(target=_sentry_loop, daemon=True).start() # tut nichts ohne Haekchen
    threading.Thread(target=_charger_loop, daemon=True).start()# tut nichts ohne Haekchen
    threading.Thread(target=_ha_loop, daemon=True).start()     # tut nichts ohne Haekchen
    threading.Thread(target=_pv_loop, daemon=True).start()     # tut nichts ohne Haekchen
    threading.Thread(target=_update_loop, daemon=True).start() # tut nichts ohne Haekchen
    threading.Thread(target=_planer_loop, daemon=True).start() # tut nichts ohne Haekchen
    local = "http://127.0.0.1:%d/" % WEBPORT
    print("=" * 60, flush=True)
    print("  EV-Cockpit laeuft:   " + local, flush=True)
    if BIND == "0.0.0.0":
        print("  Tablet/Handy im WLAN: http://%s:%d/" % (lan_ip(), WEBPORT), flush=True)
    print("  Alle Daten bleiben auf DIESEM Rechner.", flush=True)
    if not _CFG.get("vin"):
        print("  -> Der Browser oeffnet sich, der Assistent fuehrt dich durch.", flush=True)
    print("  Beenden: dieses Fenster schliessen (oder Strg+C)", flush=True)
    print("=" * 60, flush=True)
    try:
        import webbrowser
        webbrowser.open(local)
    except Exception:
        pass
    ThreadingHTTPServer((BIND, WEBPORT), H).serve_forever()


if __name__ == "__main__":
    main()
