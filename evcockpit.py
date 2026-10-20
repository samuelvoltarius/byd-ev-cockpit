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
import asyncio, json, os, threading, time, urllib.parse, uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = "1.3"
PING_URL = "https://byd.serveone.at/ev-cockpit/ping"   # NUR bei ausdruecklicher Einwilligung


def ping_optin():
    """Anonyme Nutzungszaehlung — AUSSCHLIESSLICH wenn der Nutzer sie im Assistenten
    aktiv angehakt hat. Standard ist AUS. Sendet genau drei Felder, sonst nichts:
    zufaellige Installations-ID (kein Personenbezug), Version, Automodell.
    Faellt still aus, wenn kein Netz — blockiert das Cockpit nie."""
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
STATIC_DIR = Path(__file__).resolve().parent / "static"   # Leaflet liegt hier (kein CDN!)


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


# ---------------------------------------------------------------- Konfig
def load_cfg():
    global _CFG
    try:
        _CFG = json.loads(CFG_FILE.read_text("utf-8"))
    except Exception:
        _CFG = {}
    return _CFG


def save_cfg(c):
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps(c, indent=1, ensure_ascii=False), "utf-8")
    try:
        os.chmod(CFG_FILE, 0o600)      # nur der eigene Benutzer darf lesen
    except Exception:
        pass


def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text("utf-8"))
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
    if "6024" in m or "1008" in m or "nicht abgeschlossen" in m:
        return ("BYD ist beschäftigt. Läuft deine BYD-App mit DEMSELBEN Account? "
                "Bitte einen zweiten Account als Zusatznutzer verwenden.")
    if any(x in m.lower() for x in ("password", "auth", "login", "credential")):
        return "Login abgelehnt — E-Mail, Passwort oder Land stimmen nicht (⚙︎ → neu einrichten)."
    if "not supported" in m or "1001" in m:
        return "BYD liefert für diese VIN gerade keine Daten (oft nur kurz — es versucht's weiter)."
    return m[:150]


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
                _ha_publish(st)          # tut nichts ohne Haekchen
            except Exception as e:
                _STATE["_err"] = _friendly(e)
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


def _fetch_chargers(lat, lon, radius_m=10000):
    """Ladesaeulen aus OpenStreetMap (Overpass). Kein Schluessel, keine Anmeldung.
    BEWUSST OHNE PREISE: es gibt keine verlaessliche freie Preisquelle — falsche Preise
    waeren schlimmer als gar keine. Daten sind Community-gepflegt, also ohne Gewaehr."""
    import urllib.request
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
                    if c:
                        _STATE["chargers"] = c
                        _STATE["_chg_ts"] = time.time()
                        letzte = (la, lo)
        except Exception:
            pass                       # Ladesaeulen sind nie wichtig genug fuer eine Fehlermeldung
        # Noch nichts gefunden (z.B. Overpass ueberlastet)? Bald nochmal statt 10 min stumm.
        time.sleep(600 if _STATE.get("chargers") else 60)


# ---------------------------------------------------------------- Waechter-Kamera (optional, Bastler)
SENT_GLOB = "/storage/*/Overdrive/surveillance"      # Glob ueber alle Sticks -> Stick-Wechsel egal


def _adb(args, timeout=30):
    import subprocess
    return subprocess.run(["adb", "-s", _CFG.get("car_adb", "")] + args,
                          capture_output=True, timeout=timeout)


def _sentry_loop():
    """Holt die neueste Auslöse-Aufnahme des Overdrive-Wächters per adb vom USB-Stick im Auto.
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
            r = _adb(["shell", "ls -t %s/event_*.jpg 2>/dev/null | head -1" % SENT_GLOB], timeout=20)
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
_I18N = json.loads(r'''{"BYD ist beschäftigt. Läuft deine BYD-App mit DEMSELBEN Account? Bitte einen zweiten Account als Zusatznutzer verwenden.": "BYD is busy. Is your BYD app running with the SAME account? Please use a second account as an additional user.", "Login abgelehnt — E-Mail, Passwort oder Land stimmen nicht (⚙︎ → neu einrichten).": "Login rejected — email, password or country are wrong (⚙︎ → set up again).", "BYD liefert für diese VIN gerade keine Daten (oft nur kurz — es versucht's weiter).": "BYD isn't returning any data for this VIN right now (often only briefly — it keeps trying).", "pybyd fehlt — bitte einmal installieren: pip install pybyd (%s)": "pybyd is missing — please install it once: pip install pybyd (%s)", "adb ist auf diesem Rechner nicht installiert — ohne adb kann die Wächter-Kamera nicht ausgelesen werden.": "adb is not installed on this computer — without adb the guardian camera can't be read out.", "Auto per adb nicht erreichbar oder keine Aufnahmen gefunden (Adresse richtig? Auto wach? Stick drin?)": "Car not reachable via adb or no recordings found (address correct? car awake? stick plugged in?)", "🔥 Heizen": "🔥 Heat", "❄️ Kühlen": "❄️ Cool", "⏹️ Klima aus": "⏹️ Climate off", "🔋 Batterie vorheizen": "🔋 Preheat battery", "🔋 Batterie-Heizung aus": "🔋 Battery heating off", "🔍 Auto finden": "🔍 Find car", "🔒 Zusperren": "🔒 Lock", "💺 Sitzheizung aus": "💺 Seat heating off", "💺 Sitzheizung Stufe 1": "💺 Seat heating level 1", "💺 Sitzheizung Stufe 2": "💺 Seat heating level 2", "💨 Belüftung aus": "💨 Ventilation off", "💨 Belüftung Stufe 1": "💨 Ventilation level 1", "💨 Belüftung Stufe 2": "💨 Ventilation level 2", "Befehl": "Command", "wird gesendet …": "is being sent …", "angekommen — das Auto braucht ein paar Sekunden": "arrived — the car needs a few seconds", "BYD hat den Befehl nicht bestätigt. Kurz warten und nochmal — wenn es öfter passiert, bitte melden (das ist nicht normal).": "BYD didn't confirm the command. Wait a moment and try again — if it happens more often, please report it (that's not normal).", "BYD ist beschäftigt — läuft deine BYD-App mit DEMSELBEN Account? Dafür der Zweit-Account.": "BYD is busy — is your BYD app running with the SAME account? That's what the second account is for.", "Deutlich zu wenig Druck (%.0f kPa statt %.0f) — bitte bald prüfen.": "Significantly too little pressure (%.0f kPa instead of %.0f) — please check soon.", "Etwas wenig Druck (%.0f kPa statt %.0f) — beim nächsten Tanken nachfüllen.": "A little low on pressure (%.0f kPa instead of %.0f) — top it up at your next stop.", "Reichlich viel Druck (%.0f kPa statt %.0f).": "Quite a lot of pressure (%.0f kPa instead of %.0f).", "Druck passt (%.0f–%.0f kPa).": "Pressure is fine (%.0f–%.0f kPa).", "Sensor meldet '%s' — liefert dein HA gerade Werte?": "Sensor reports '%s' — is your HA delivering values right now?", "Token abgelehnt — in HA neu erzeugen (Profil → Sicherheit).": "Token rejected — regenerate it in HA (Profile → Security).", "Sensor nicht gefunden — im Assistenten neu auswählen.": "Sensor not found — select it again in the wizard.", "Kilometerstand": "Odometer", "Ladezustand": "Charge level", "Echte Reichweite": "Real range", "Reichweite (BYD)": "Range (BYD)", "Verbrauch Schnitt": "Average consumption", "Ladeleistung": "Charging power", "Außentemperatur": "Outside temperature", "Reifen VL": "Tyre FL", "Reifen VR": "Tyre FR", "Reifen HL": "Tyre RL", "Reifen HR": "Tyre RR", "Gang": "Gear", "Verriegelt": "Locked", "Lädt": "Charging", "Angesteckt": "Plugged in", "Türen offen": "Doors open", "Fenster offen": "Windows open", "Klima läuft": "Climate running", "Batterie heizt": "Battery heating", "Standort": "Location", "Broker weist ab (Code %s) — Benutzer/Passwort?": "Broker refuses (code %s) — username/password?", "Keine Fahrzeuge gefunden — stimmen Login/Land?": "No vehicles found — are login/country correct?", "Login abgelehnt — E-Mail/Passwort/Land prüfen": "Login rejected — check email/password/country", "Token abgelehnt — stimmt er? (HA: Profil → Sicherheit → Token erstellen)": "Token rejected — is it correct? (HA: Profile → Security → Create token)", "Kein Kontakt zu Home Assistant — Adresse richtig? (z.B. http://192.168.0.10:8123)": "No contact with Home Assistant — is the address correct? (e.g. http://192.168.0.10:8123)", "Keine Verbindung — Adresse/Port richtig? Läuft der Broker (Mosquitto-Add-on)?": "No connection — are address/port correct? Is the broker running (Mosquitto add-on)?", "Broker weist ab — Benutzer/Passwort prüfen.": "Broker refuses — check username/password.", "VIN fehlt": "VIN missing", "EV-Cockpit laeuft:": "EV-Cockpit is running:", "Tablet/Handy im WLAN:": "Tablet/phone on Wi-Fi:", "Alle Daten bleiben auf DIESEM Rechner.": "All data stays on THIS computer.", "-> Der Browser oeffnet sich, der Assistent fuehrt dich durch.": "-> The browser opens, the wizard guides you through it.", "Beenden: dieses Fenster schliessen (oder Strg+C)": "To quit: close this window (or Ctrl+C)", "EV-Cockpit — Über & Rechtliches": "EV-Cockpit — About & Legal", "← zurück zum Cockpit": "← back to the cockpit", "Was das ist": "What this is", "Ein": "A", "freies Werkzeug für die BYD-Community": "free tool for the BYD community", ". Es zeigt dir die Daten deines eigenen Autos auf deinem eigenen Rechner — ohne Umweg über fremde Server. Gebaut aus Freude an der Sache und im Sinne des Rechts auf Reparatur. Kostenlos, für niemanden ein Geschäft.": ". It shows you your own car's data on your own computer — without a detour via someone else's servers. Built out of love for the thing and in the spirit of the right to repair. Free, a business for no one.", "Impressum": "Legal notice", "Salzburg, Österreich": "Salzburg, Austria", "E-Mail:": "Email:", "Vollständiges Impressum:": "Full legal notice:", "⚠️ Haftungsausschluss — bitte lesen": "⚠️ Disclaimer — please read", "Keine Verbindung zu BYD.": "No connection to BYD.", "Dies ist": "This is", "kein offizielles Produkt": "not an official product", "der BYD Auto Co. Ltd. und steht in keinerlei Verbindung zu BYD. „BYD\" ist eine Marke ihrer jeweiligen Inhaber und wird hier nur genannt, um die Kompatibilität zu beschreiben.": "of BYD Auto Co. Ltd. and has no connection to BYD whatsoever. \"BYD\" is a trademark of its respective owners and is named here only to describe compatibility.", "Nutzung auf eigene Gefahr.": "Use at your own risk.", "Diese Software wird kostenlos und": "This software is provided free of charge and", "ohne jede Gewähr": "without any warranty", "bereitgestellt — ohne Zusicherung von Funktion, Richtigkeit oder Verfügbarkeit. Sie": "— with no assurance of function, accuracy or availability. It", "steuert ein echtes Fahrzeug": "controls a real vehicle", "(z.B. die Klimaanlage). Für Schäden jeder Art, Datenverlust oder Folgen aus der Nutzung wird": "(e.g. the air conditioning).", "keine Haftung": "No liability", "übernommen, soweit gesetzlich zulässig.": "is accepted for damage of any kind, data loss or consequences of use, as far as legally permissible.", "BYDs Nutzungsbedingungen.": "BYD's terms of use.", "Der Zugriff auf die BYD-Cloud über eine fremde Anwendung kann den Nutzungsbedingungen von BYD widersprechen. Im ungünstigsten Fall kann BYD einen Account einschränken oder sperren.": "Accessing the BYD cloud through a third-party application may conflict with BYD's terms of use. In the worst case, BYD can restrict or block an account.", "Das entscheidest du selbst und trägst es selbst.": "You decide that yourself and carry it yourself.", "Zweiter Account.": "Second account.", "Die BYD-Cloud erlaubt pro Account nur eine aktive Sitzung. Nutze einen zweiten Account als Zusatznutzer — sonst stört dieses Werkzeug deine eigene BYD-App.": "The BYD cloud allows only one active session per account. Use a second account as an additional user — otherwise this tool disturbs your own BYD app.", "🔒 Datenschutz": "🔒 Privacy", "Deine Daten bleiben auf diesem Rechner.": "Your data stays on this computer.", "Zugangsdaten und Fahrzeugdaten werden ausschließlich lokal gespeichert (": "Access credentials and vehicle data are stored exclusively locally (", "). Die einzige Gegenstelle im Normalbetrieb ist die": "). The only remote endpoint in normal operation is the", "BYD-Cloud selbst": "BYD cloud itself", "— also der Dienst, dessen Daten du abrufst.": "— that is, the service whose data you're retrieving.", "Zwei freiwillige Ausnahmen": "Two voluntary exceptions", ", beide": ", both", "standardmäßig aus": "off by default", "und im Assistenten anhakbar:": "and checkable in the wizard:", "Strompreis": "Electricity price", "— dein Rechner fragt aWATTar bzw. energy-charts.info nach den Börsenpreisen deines Landes. Übertragen wird dabei nur die Anfrage selbst (die Gegenstelle sieht deine IP, wie bei jedem Webseitenbesuch) —": "— your computer asks aWATTar or energy-charts.info for your country's exchange prices. Only the request itself is transmitted (the remote endpoint sees your IP, as with any website visit) —", "keine Fahrzeugdaten": "no vehicle data", "Nutzungszählung": "Usage counting", "Nur wenn du sie im Assistenten aktiv anhakst, sendet das Programm einmal am Tag genau das hier:": "Only if you actively check it in the wizard does the program send exactly this once a day:", "{ \"id\": \"zufällige Installations-ID\", \"version\": \"__VERSION__\", \"model\": \"dein Automodell\" }": "{ \"id\": \"random installation ID\", \"version\": \"__VERSION__\", \"model\": \"your car model\" }", "Kein Name, keine E-Mail, keine VIN, kein Standort, keine Fahrdaten. Die ID ist eine Zufallszahl ohne Personenbezug. Häkchen jederzeit im Assistenten abschaltbar.": "No name, no email, no VIN, no location, no driving data. The ID is a random number with no personal reference. The checkbox can be switched off in the wizard at any time.", "Quelloffen": "Open source", "Du sollst uns nicht glauben müssen —": "You shouldn't have to take our word for it —", "schau nach": "check for yourself", ". Der gesamte Quelltext liegt offen; die Datei, die du gestartet hast, ist lesbarer Python-Code.": ". The entire source code is open; the file you started is readable Python code.", "EV-Cockpit — Einrichtung": "EV-Cockpit — Setup", "EV-Cockpit einrichten": "Set up EV-Cockpit", "Dein Auto, dein Rechner, deine Daten.": "Your car, your computer, your data.", "Wichtig": "Important", "BYD-Zugang": "BYD access", "Dein Auto": "Your car", "Aussehen": "Appearance", "⚠️ Bitte lies das hier — es ist der wichtigste Punkt": "⚠️ Please read this — it's the most important point", "Die BYD-Cloud erlaubt pro Konto nur": "The BYD cloud allows only", "eine": "one", "aktive Verbindung. Wenn du hier": "active connection per account. If you enter", "dasselbe Konto": "the same account", "einträgst wie in deiner BYD-App am Handy,": "here as in your BYD app on your phone,", "stören sich beide gegenseitig": "the two interfere with each other", "— mal spinnt das Cockpit, mal die App (Fehler 6024).": "— sometimes the cockpit acts up, sometimes the app (error 6024).", "So machst du es richtig:": "Here's how to do it right:", "In der BYD-App ein": "In the BYD app, create a", "zweites Konto": "second account", "anlegen (andere E-Mail-Adresse)": "(a different email address)", "Dieses zweite Konto im Auto als": "Grant this second account access in the car as an", "„Zusatznutzer\"": "\"additional user\"", "freigeben": "", "Hier gleich das": "Enter the", "zweite": "second", "Konto eintragen — nicht dein Haupt-Konto": "account here — not your main account", "Dann laufen App und Cockpit friedlich nebeneinander.": "Then the app and cockpit run peacefully side by side.", "Zugangsdaten und Fahrzeugdaten werden nur lokal gespeichert. Dieses Programm sendet": "Access credentials and vehicle data are stored only locally. This program sends", "nichts": "nothing", "an den Entwickler — es spricht nur mit der BYD-Cloud selbst. Nachlesbar: die Datei": "to the developer — it talks only to the BYD cloud itself. You can check: the file", "ist normaler, lesbarer Text.": "is normal, readable text.", "Verstanden — ich verwende ein zweites BYD-Konto": "Understood — I'm using a second BYD account", "Oder: mir ist bewusst, dass es sonst mit meiner BYD-App kollidieren kann.": "Or: I'm aware that it can otherwise collide with my BYD app.", "Weiter →": "Next →", "E-Mail deines BYD-Kontos": "Email of your BYD account", "(das zweite!)": "(the second one!)", "Passwort": "Password", "Steuer-PIN (6-stellig — dieselbe wie in der BYD-App)": "Control PIN (6 digits — the same as in the BYD app)", "z.B. 123456": "e.g. 123456", "Land": "Country", "Zeitzone": "Time zone", "🔍 Meine Fahrzeuge abrufen": "🔍 Fetch my vehicles", "Beim Abrufen meldet sich dein Rechner einmal bei BYD an — so wie deine Handy-App auch. Klappt es nicht, stimmt meistens das": "When fetching, your computer logs in to BYD once — just like your phone app does. If it doesn't work, it's usually the", "nicht.": "that's wrong.", "← Zurück": "← Back", "Dein Fahrzeug": "Your vehicle", "— erst Fahrzeuge abrufen —": "— fetch vehicles first —", "Modell (setzt die Akkugröße)": "Model (sets the battery size)", "Akku nutzbar in kWh —": "Usable battery in kWh —", "bitte prüfen": "please check", "Reifendruck-Sollwert (kPa, optional)": "Tyre pressure target (kPa, optional)", "z.B. 250": "e.g. 250", "🔎 Was kann mein Auto?": "🔎 What can my car do?", "Dein Auto hat uns gesagt, was es kann.": "Your car told us what it can do.", "Hak an, was du im Cockpit haben willst": "Check what you want in the cockpit", "— den Rest siehst du gar nicht erst.": "— you won't even see the rest.", "Ausgegraute Zeilen kann dein Auto nicht — die liegen nicht an uns.": "Greyed-out rows are things your car can't do — that's not on us.", "Aufsperren bieten wir bewusst nicht an": "We deliberately don't offer unlocking", ", auch wenn dein Auto es könnte: Ein Knopf im Browser, der dein Auto öffnet, wäre ein Einbruchswerkzeug für jeden, der an deinen Rechner kommt. Zusperren ist dagegen harmlos.": ", even if your car could do it: a button in the browser that opens your car would be a burglary tool for anyone who gets to your computer. Locking, on the other hand, is harmless.", "Der": "The", "Reifendruck-Sollwert": "tyre pressure target", "steht bei dir im": "is in your", "Türrahmen der Fahrertür": "driver's door frame", "(oft in bar: 2,5 bar = 250 kPa). Trägst du ihn ein, warnt dich das Cockpit bei zu wenig Druck. Lässt du das Feld leer, zeigt es den Druck nur an —": "(often in bar: 2.5 bar = 250 kPa). If you enter it, the cockpit warns you when pressure is too low. If you leave the field empty, it only shows the pressure —", "ich rate den Wert bewusst nicht": "I deliberately don't guess the value", ", er hängt an deiner Reifengröße und Beladung.": ", it depends on your tyre size and load.", "Diese Zahl braucht nur die": "This number is only needed for the", "ehrliche Reichweiten-Rechnung": "honest range calculation", ". Steht in deinen Fahrzeugpapieren oder im Prospekt. Stimmt sie nicht genau, ist das halb so wild — die Reichweite wird dann nur etwas ungenauer.": ". It's in your vehicle documents or the brochure. If it's not exactly right, no big deal — the range just gets a bit less accurate.", "Foto deines Autos (optional)": "Photo of your car (optional)", "Am schönsten ist ein Foto von": "A photo of", "deinem eigenen": "your own", "Auto — freigestellt vor hellem Hintergrund wirkt es am besten. Bleibt natürlich auch nur auf diesem Rechner. Kannst du auch später noch nachreichen.": "car looks nicest — cut out against a light background works best. It stays on this computer too, of course. You can also add it later.", "Wie oft soll beim Auto nachgefragt werden?": "How often should the car be polled?", "alle 2 Minuten — sehr frisch, viele Abfragen": "every 2 minutes — very fresh, many requests", "alle 5 Minuten — empfohlen": "every 5 minutes — recommended", "alle 10 Minuten — sparsam": "every 10 minutes — economical", "alle 15 Minuten": "every 15 minutes", "alle 30 Minuten — sehr sparsam": "every 30 minutes — very economical", "🔔 Bescheid geben, wenn das Laden fertig ist": "🔔 Notify me when charging is finished", "Im Cockpit gibt es oben rechts eine": "In the cockpit there's a", "Glocke": "bell", "— einmal draufklicken, dann meldet dir dein Browser, wenn das Auto fertig geladen hat (und wenn es plötzlich offen ist).": "at the top right — click it once, then your browser notifies you when the car has finished charging (and when it's suddenly open).", "Nichts zu konfigurieren:": "Nothing to configure:", "Die Meldung entsteht": "The notification is created", "in deinem Browser": "in your browser", "— kein Telegram, kein Konto, es verlässt nichts deinen Rechner.": "— no Telegram, no account, nothing leaves your computer.", "Ehrliche Grenze:": "Honest limitation:", "Es meldet nur, solange die Cockpit-Seite offen ist (ein Hintergrund-Tab reicht). Browser zu = keine Meldung.": "It only notifies while the cockpit page is open (a background tab is enough). Browser closed = no notification.", "Gilt, solange das Auto": "Applies as long as the car is", "aktiv": "active", "ist. Steht es länger, fragt das Cockpit nur alle 15 Minuten — das schont die 12V-Batterie. Während der Fahrt fragt es automatisch öfter.": ". If it stands for longer, the cockpit only polls every 15 minutes — that spares the 12V battery. While driving it automatically polls more often.", "Fürs Vorklimatisieren spielt das keine Rolle": "For preconditioning this doesn't matter", "— das geht jederzeit, auch beim geparkten Auto.": "— that works anytime, even with the car parked.", "Alles hier ist freiwillig.": "Everything here is optional.", "Lass ruhig alles aus — das Cockpit funktioniert komplett ohne. Du kannst jederzeit zurückkommen und etwas dazuschalten.": "Feel free to leave everything off — the cockpit works completely without it. You can come back anytime and switch something on.", "💶 Strompreis anzeigen — „wann ist Laden am billigsten?\"": "💶 Show electricity price — \"when is charging cheapest?\"", "Zeigt den": "Shows your country's", "Börsen-Strompreis": "exchange electricity price", "deines Landes als Stundenbalken mit der günstigsten Stunde. Quelle: aWATTar (AT/DE) bzw. energy-charts.info (Fraunhofer ISE), kostenlos, ohne Konto.": "as hourly bars with the cheapest hour. Source: aWATTar (AT/DE) or energy-charts.info (Fraunhofer ISE), free, no account.", "Ehrlich:": "Honestly:", "Das ist der": "This is the", "Börsenpreis": "exchange price", "nicht": "not", "was auf deiner Rechnung steht (Netz, Steuern, Aufschläge fehlen). Nur mit einem": "what's on your bill (grid fees, taxes, surcharges are missing). Only with an", "Börsentarif": "exchange tariff", "(Tibber, aWATTar, smartENERGY) ist das dein echter Verlauf. Bei Fixtarif bloß interessant.": "(Tibber, aWATTar, smartENERGY) is this your real curve. With a fixed tariff it's just interesting.", "Dein Rechner fragt dann diese Preisseite ab (die sieht deine IP, wie bei jedem Webseitenbesuch) —": "Your computer then queries this price page (which sees your IP, as with any website visit) —", "🔌 Ladesäulen in der Nähe anzeigen": "🔌 Show charging stations nearby", "Öffentliche Ladestationen rund um den": "Public charging stations around your", "aktuellen Standort deines Autos": "car's current location", "— Betreiber, Entfernung, Steckertyp. Quelle:": "— operator, distance, connector type. Source:", ", kein Konto.": ", no account.", "Ehrlich: keine Preise.": "Honestly: no prices.", "Es gibt keine verlässliche freie Quelle für aktuelle Ladepreise — falsche Preise wären schlimmer als gar keine. Auch die Standorte pflegen Freiwillige: meist gut, aber ohne Gewähr. E-Bike-Ladepunkte filtern wir raus.": "There's no reliable free source for current charging prices — wrong prices would be worse than none. The locations are also maintained by volunteers: usually good, but without guarantee. We filter out e-bike charging points.", "📱 Auch auf Tablet/Handy im Heimnetz öffnen": "📱 Also open on tablet/phone in the home network", "Ohne Haken ist das Cockpit": "Without the checkmark, the cockpit is reachable", "nur auf diesem Rechner": "only on this computer", "erreichbar — die sicherste Einstellung. Mit Haken erreichst du es auch vom Küchen-Tablet im eigenen WLAN; die Adresse zeigt dir das Cockpit dann unten an. Nur im eigenen, vertrauenswürdigen Netz aktivieren: das Cockpit kann die Klimaanlage deines Autos steuern.": "— the safest setting. With the checkmark you can also reach it from the kitchen tablet on your own Wi-Fi; the cockpit then shows you the address below. Only enable it on your own, trusted network: the cockpit can control your car's air conditioning.", "🏠 Ans Home Assistant senden": "🏠 Send to Home Assistant", "Du nutzt": "Using", "? Dann schickt das Cockpit dein Auto dorthin — es taucht": "? Then the cockpit sends your car there — it", "von selbst auf": "shows up on its own", ", mit allen Werten und den Klima-Knöpfen. Kein YAML, nichts konfigurieren. Praktisch, wenn du dort schon deine PV-Anlage oder Wallbox hast: dann siehst du alles auf einem Bild.": ", with all values and the climate buttons. No YAML, nothing to configure. Handy if you already have your PV system or wallbox there: then you see everything in one picture.", "Voraussetzung:": "Requirement:", "ein MQTT-Broker (bei HA meist das": "an MQTT broker (with HA usually the", "-Add-on, einmal installieren).": "add-on, install it once).", "Tipp:": "Tip:", "Am besten läuft dieses Programm dann auf dem Gerät, auf dem auch HA läuft (Raspberry, NAS, Mini-PC) — dann hat HA rund um die Uhr Daten. Dafür gibt es das Linux-Paket und eine Autostart-Anleitung in der LIESMICH.": "It's best to run this program on the device that also runs HA (Raspberry, NAS, mini PC) — then HA has data around the clock. There's a Linux package and an autostart guide for that in the README.", "MQTT-Broker (Adresse)": "MQTT broker (address)", "z.B. 192.168.0.10": "e.g. 192.168.0.10", "Benutzer (falls nötig)": "User (if needed)", "leer lassen wenn keiner": "leave empty if none", "leer lassen wenn keins": "leave empty if none", "🔌 Verbindung testen": "🔌 Test connection", "☀️ PV-Leistung aus Home Assistant holen": "☀️ Get PV power from Home Assistant", "Du hast eine": "You have a", "PV-Anlage": "PV system", "und sie ist in Home Assistant eingebunden? Dann zeigt das Cockpit deine": "and it's integrated into Home Assistant? Then the cockpit shows your", "aktuelle Solar-Leistung": "current solar power", "direkt neben Ladestand und Strompreis — du siehst auf einen Blick, ob du gerade": "right next to the charge level and electricity price — you see at a glance whether you're charging", "mit eigener Sonne": "with your own sun", "lädst oder teuer aus dem Netz.": "right now or expensively from the grid.", "Warum das so gut geht:": "Why this works so well:", "Wir reden nicht mit deinem Wechselrichter —": "We don't talk to your inverter —", "Home Assistant hat das schon erledigt": "Home Assistant has already done that", ". Egal ob Fronius, SMA, Huawei, SolarEdge oder Kostal: in HA ist es einfach ein Sensor mit einem Wert in Watt. Den holen wir uns, sonst nichts.": ". Whether Fronius, SMA, Huawei, SolarEdge or Kostal: in HA it's simply a sensor with a value in watts. That's what we fetch, nothing else.", "Wir zeigen, was": "We show what", "dein HA": "your HA", "sagt. Stimmt der Wert dort nicht, stimmt er hier auch nicht. Es wird": "says. If the value is wrong there, it's wrong here too. It's", "nur gelesen": "read only", "— wir schreiben nie etwas in dein HA.": "— we never write anything to your HA.", "Adresse deines Home Assistant": "Address of your Home Assistant", "z.B. http://192.168.0.10:8123": "e.g. http://192.168.0.10:8123", "Zugriffs-Token": "Access token", "(in HA: unten links auf deinen Namen → Sicherheit → ganz unten „Long-Lived Access Token\" → Token erstellen)": "(in HA: bottom left on your name → Security → at the very bottom \"Long-Lived Access Token\" → create token)", "den langen Text hier einfügen": "paste the long text here", "🔍 Meine Sensoren laden": "🔍 Load my sensors", "Welcher Sensor ist deine PV-Leistung?": "Which sensor is your PV power?", "Meist heißt er „PV Leistung\", „Solar Power\" o.ä. Nimm den, der die": "It's usually called \"PV Leistung\", \"Solar Power\" or similar. Take the one that shows the", "aktuelle Erzeugung in Watt": "current generation in watts", "zeigt.": ".", "🎥 Wächter-Kamera einbinden": "🎥 Integrate guardian camera", "— nur für Bastler": "— for tinkerers only", "Zeigt die letzte": "Shows the latest", "Auslöse-Aufnahme": "triggered recording", "der 360°-Kameras.": "from the 360° cameras.", "Braucht alles davon:": "Needs all of this:", "auf diesem Rechner (ist": "on this computer (is", "im Paket dabei),": "included in the package),", "kabelloses adb am Auto": "wireless adb on the car", "freigeschaltet,": "enabled,", "Overdrive-App": "Overdrive app", "USB-Stick": "USB stick", "im Auto.": "in the car.", "Sagt dir das nichts?": "Doesn't ring a bell?", "Haken weglassen": "Leave the checkmark off", "— alles andere geht trotzdem.": "— everything else still works.", "adb-Adresse des Autos (z.B. 192.168.0.50:5555)": "adb address of the car (e.g. 192.168.0.50:5555)", "🔔 Auf neue Versionen hinweisen": "🔔 Notify about new versions", "Das Cockpit schaut dann": "The cockpit then checks", "einmal am Tag": "once a day", "nach, ob es eine neuere Version gibt, und zeigt dir oben einen kleinen Hinweis. Nützlich für Fehlerbehebungen — du musst sonst selbst mitbekommen, wenn etwas repariert wurde.": "whether there's a newer version and shows you a small note at the top. Useful for bug fixes — otherwise you'd have to notice yourself when something was repaired.", "Wie das ohne Datenabfluss geht:": "How this works without data leaving:", "Dein Rechner lädt nur eine kleine Textdatei mit der neuesten Versionsnummer und": "Your computer only downloads a small text file with the latest version number and", "vergleicht sie selbst": "compares it itself", ". Der Server erfährt dabei": ". The server doesn't even", "nicht einmal, welche Version du hast": "learn which version you have", "— es wird nichts über dich gesendet, kein Ident, kein Modell, keine Fahrzeugdaten.": "— nothing about you is sent, no ident, no model, no vehicle data.", "Beim Abholen sieht der Server – wie bei jedem Webseitenbesuch – deine IP. Wir schreiben sie nirgends auf. Ohne Haken passiert gar nichts.": "When fetching, the server sees – as with any website visit – your IP. We don't record it anywhere. Without the checkmark, nothing happens at all.", "📊 Anonym mitzählen, dass ich das Tool nutze": "📊 Anonymously count that I use the tool", "Damit der Entwickler sieht, ob sich die Arbeit lohnt.": "So the developer can see whether the work is worth it.", "Einmal am Tag wird genau das gesendet — und sonst nichts:": "Once a day exactly this is sent — and nothing else:", "{ \"id\": \"zufällige Nummer\", \"version\": \"1.0\", \"model\": \"dein Modell\" }": "{ \"id\": \"random number\", \"version\": \"1.0\", \"model\": \"your model\" }", "Kein Name, keine E-Mail, keine VIN, kein Standort, keine Fahrdaten. Ohne Haken sendet das Programm": "No name, no email, no VIN, no location, no driving data. Without the checkmark, the program sends", "gar nichts": "nothing at all", "an den Entwickler.": "to the developer.", "✅ Fertig — Cockpit starten": "✅ Done — start cockpit", "ABMELDEN": "LOG OUT", "Löscht deine BYD-Zugangsdaten, die gespeicherten Fahrzeugdaten und dein Foto": "Deletes your BYD access credentials, the stored vehicle data and your photo", "von diesem Rechner": "from this computer", ". Dein BYD-Konto selbst bleibt unangetastet.": ". Your BYD account itself remains untouched.", "🚪 Abmelden & Daten löschen": "🚪 Log out & delete data", "Impressum · Haftungsausschluss · Datenschutz": "Legal notice · Disclaimer · Privacy", "Bevor es losgeht": "Before we start", "Ein Punkt ist wirklich wichtig — bitte kurz lesen.": "One point is really important — please read it briefly.", "Dein BYD-Zugang": "Your BYD access", "Damit holt dein Rechner die Daten direkt von BYD.": "With this, your computer fetches the data directly from BYD.", "Welches Fahrzeug, und wie groß ist der Akku?": "Which vehicle, and how big is the battery?", "Dein Cockpit": "Your cockpit", "Ein Foto und wie oft nachgefragt wird.": "A photo and how often it's polled.", "Alles freiwillig — lass ruhig alles aus.": "All optional — feel free to leave everything off.", "⚠️ Bitte zuerst „Meine Fahrzeuge abrufen\" drücken.": "⚠️ Please press \"Fetch my vehicles\" first.", "ℹ️ Deine Auswahl ist gespeichert. Erneut abfragen, um sie zu ändern.": "ℹ️ Your selection is saved. Query again to change it.", "(gespeichert)": "(saved)", "••••••• (gespeichert — leer lassen zum Behalten)": "••••••• (saved — leave empty to keep)", "Aktuelles Foto — neues wählen zum Ersetzen": "Current photo — choose a new one to replace it", "ℹ️ Deine Einstellungen sind vorausgefüllt. Ändere, was du willst, und speichere.": "ℹ️ Your settings are pre-filled. Change what you want and save.", "Wirklich abmelden? Zugangsdaten, Fahrzeugdaten und Foto werden von diesem Rechner gelöscht.": "Really log out? Access credentials, vehicle data and photo will be deleted from this computer.", "⏳ Lösche …": "⏳ Deleting …", "✅ Abgemeldet. Alles gelöscht.": "✅ Logged out. Everything deleted.", "⚠️ Bitte zuerst in Schritt 2 die Fahrzeuge abrufen.": "⚠️ Please fetch the vehicles in step 2 first.", "⏳ Frage dein Auto …": "⏳ Asking your car …", "Dein Auto kann das nicht.": "Your car can't do that.", "✅ Dein Auto kann": "✅ Your car can", "von": "of", "Dingen.": "things.", "⚠️ Bitte Adresse und Token eintragen.": "⚠️ Please enter address and token.", "⏳ Frage dein Home Assistant …": "⏳ Asking your Home Assistant …", "Leistungs-Sensoren gefunden — wähl deinen PV-Sensor aus.": "power sensors found — choose your PV sensor.", "⚠️ Bitte zuerst die Broker-Adresse eintragen.": "⚠️ Please enter the broker address first.", "⏳ Verbinde …": "⏳ Connecting …", "✅ Broker erreicht — dein Auto erscheint gleich in Home Assistant.": "✅ Broker reached — your car will appear in Home Assistant shortly.", "⏳ Melde mich bei BYD an …": "⏳ Logging in to BYD …", "Fahrzeug(e) gefunden — weiter unten mit Weiter": "vehicle(s) found — continue below with Next", "⚠️ Fehler:": "⚠️ Error:", "⚠️ Bitte erst Fahrzeuge abrufen und eins auswählen": "⚠️ Please fetch vehicles first and select one", "⏳ Speichere …": "⏳ Saving …", "✅ Gespeichert — Cockpit startet …": "✅ Saved — cockpit is starting …", "Für den Tablet-Zugriff das Programm einmal neu starten.": "For tablet access, restart the program once.", "ist da.": "is here.", "Ansehen →": "View →", "Benachrichtigen, wenn das Laden fertig ist": "Notify when charging is finished", "AKKU": "BATTERY", "REICHWEITE (ECHT)": "RANGE (REAL)", "BYD sagt:": "BYD says:", "Kein Foto hinterlegt": "No photo set", "⚙︎ → Foto-URL": "⚙︎ → Photo URL", "KILOMETERSTAND": "ODOMETER", "AUSSEN": "OUTSIDE", "VERBRAUCH Ø": "CONSUMPTION Ø", "REIFEN": "TYRES", "DEINE PV-ANLAGE": "YOUR PV SYSTEM", "ERZEUGT GERADE": "GENERATING NOW", "Quelle: dein Home Assistant": "Source: your Home Assistant", "KLIMA": "CLIMATE", "🔥  Heizen": "🔥  Heat", "❄  Kühlen": "❄  Cool", "◼  Aus": "◼  Off", "🔋  Batterie vorheizen": "🔋  Preheat battery", "🔍  Auto finden": "🔍  Find car", "🔒  Zusperren": "🔒  Lock", "SITZE (FAHRER + BEIFAHRER)": "SEATS (DRIVER + PASSENGER)", "💺  Aus": "💺  Off", "💺  Stufe 1": "💺  Level 1", "💺  Stufe 2": "💺  Level 2", "💨  Belüftung aus": "💨  Ventilation off", "💨  Stufe 1": "💨  Level 1", "💨  Stufe 2": "💨  Level 2", "Heizen zielt auf 26 °C, Kühlen auf 19 °C.": "Heating targets 26 °C, cooling 19 °C.", "Batterie vorheizen": "Preheating the battery", "hilft im Winter vor dem Schnellladen — eine warme Batterie lädt deutlich schneller. Das geht auch bei geparktem Auto.": "helps in winter before fast charging — a warm battery charges much faster. This also works with the car parked.", "LADEN": "CHARGING", "LEISTUNG": "POWER", "FERTIG IN": "DONE IN", "laut Auto": "per the car", "STROM GERADE": "ELECTRICITY NOW", "Börse, ohne Netz & Steuern": "Exchange, without grid & taxes", "Türen": "Doors", "Fenster": "Windows", "STROMPREIS (BÖRSE)": "ELECTRICITY PRICE (EXCHANGE)", "JETZT": "NOW", "GÜNSTIGSTE STUNDE": "CHEAPEST HOUR", "um": "at", "Uhr": "", "TEUERSTE": "MOST EXPENSIVE", "Börsenpreis ohne Netz & Steuern — dein Rechnungspreis nur bei einem Börsentarif.": "Exchange price without grid & taxes — your bill price only with an exchange tariff.", "Quelle:": "Source:", "WÄCHTER-KAMERA": "GUARDIAN CAMERA", "LETZTE AUFNAHME": "LAST RECORDING", "Wächter-Aufnahme": "Guardian recording", "LADESÄULEN IN DER NÄHE": "CHARGING STATIONS NEARBY", "Daten: © OpenStreetMap-Mitwirkende (ODbL) · von Freiwilligen gepflegt, ohne Gewähr ·": "Data: © OpenStreetMap contributors (ODbL) · maintained by volunteers, without guarantee ·", "bewusst ohne Preisangaben": "deliberately without price information", "STANDORT": "LOCATION", "🔵 dein Auto · 🟢 Ladesäulen (anklickbar) — Karte © OpenStreetMap-Mitwirkende": "🔵 your car · 🟢 charging stations (clickable) — map © OpenStreetMap contributors", "📱 Auf Tablet/Handy im selben WLAN erreichbar unter": "📱 Reachable on tablet/phone on the same Wi-Fi at", "📷 Eigenes Foto deines Autos einsetzen": "📷 Use your own car's photo", "km entfernt": "km away", "Meldet, wenn das Laden fertig ist (nur solange diese Seite offen ist)": "Notifies when charging is finished (only while this page is open)", "Dein Browser kann keine Benachrichtigungen.": "Your browser can't do notifications.", "Benachrichtigungen an": "Notifications on", "Du bekommst Bescheid, wenn das Laden fertig ist.": "You'll be notified when charging is finished.", "Dein Browser hat Benachrichtigungen für diese Seite blockiert. Du kannst das im Schloss-Symbol neben der Adresse wieder erlauben.": "Your browser has blocked notifications for this page. You can allow it again via the lock icon next to the address.", "🔌 Laden beendet": "🔌 Charging finished", "Dein Auto ist bei": "Your car is at", "% — Kabel kann raus.": "% — you can unplug the cable.", "🔓 Auto ist offen": "🔓 Car is open", "Es war eben noch verriegelt.": "It was locked just a moment ago.", "SCHLÄFT": "SLEEPING", "Ja": "Yes", "Nein": "No", "zu": "closed", "OFFEN": "OPEN", "angesteckt, lädt nicht": "plugged in, not charging", "lädt": "charging", "Schnellladen": "Fast charging", "Wallbox-Tempo": "Wallbox speed", "langsam (Steckdose?)": "slow (household socket?)", "Uhr:": "h:", "⏳ Sende …": "⏳ Sending …", "⚠️ Dienst weg": "⚠️ Service gone", "Auto wirklich zusperren?": "Really lock the car?", "Projekt & Kontakt": "Project & contact", "Freies, nicht-kommerzielles Community-Projekt, quelloffen auf GitHub:": "Free, non-commercial community project, open source on GitHub:", "Fragen oder Fehler? Bitte als Issue melden:": "Questions or bugs? Please report as an issue:", "— Nur wenn du sie im Assistenten aktiv anhakst, sendet das Programm einmal am Tag genau das hier:": "— Only if you actively check it in the wizard does the program send exactly this once a day:", "zufällige Installations-ID": "random installation ID", "dein Automodell": "your car model"}''')
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
    var b=document.createElement('button');
    b.textContent=(LANG==='en')?'🌐 DE':'🌐 EN';
    b.setAttribute('aria-label',LANG==='en'?'Auf Deutsch umschalten':'Switch to English');
    b.style.cssText='position:fixed;right:12px;bottom:12px;z-index:9999;padding:7px 12px;border-radius:20px;border:1px solid rgba(120,165,235,.35);background:rgba(12,20,34,.85);color:#cfe0f5;font:600 13px system-ui,sans-serif;cursor:pointer;-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)';
    b.onclick=function(){try{localStorage.setItem('evc_lang',LANG==='en'?'de':'en');}catch(e){}location.reload();};
    document.body.appendChild(b);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
</script>'''
def _i18n(h):
    h = h.replace('<head><meta charset=utf-8>', '<head><meta charset=utf-8>' + I18N_HEAD, 1)
    return h.replace('</body>', I18N_BODY + '</body>', 1) if '</body>' in h else h + I18N_BODY

ABOUT = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Über &amp; Rechtliches</title>
<style>
:root{--blue:#3aa0ff;--txt:#eef4fb;--mut:#8ea3bd;--line:rgba(120,165,235,.18)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1100px 700px at 50% -8%,#12213f,#0a1120 55%,#05080f);
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
</div></body></html>"""


# ---------------------------------------------------------------- Assistent (HTML)
WIZARD = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Einrichtung</title>
<style>
:root{--blue:#3aa0ff;--cyan:#37e6ff;--txt:#eef4fb;--mut:#8ea3bd;--line:rgba(120,165,235,.18)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1100px 700px at 50% -8%,#12213f,#0a1120 55%,#05080f);
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
.dot2.on i{background:linear-gradient(135deg,#3aa0ff,#37e6ff);color:#04101f;border-color:transparent;font-weight:700}
.dot2.on b{color:var(--txt)}
.dot2.done i{background:rgba(91,227,163,.25);border-color:rgba(91,227,163,.5);color:#5be3a3}
.card{background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:1px solid var(--line);
 border-radius:18px;padding:20px;margin-bottom:14px}
.warn{background:rgba(255,176,32,.10);border:1px solid rgba(255,176,32,.45);border-radius:16px;padding:16px 18px;margin-bottom:14px}
.warn b{color:#ffb020}
.ok{background:rgba(91,227,163,.08);border:1px solid rgba(91,227,163,.35);border-radius:16px;padding:14px 16px;margin-bottom:14px;font-size:14px}
label{display:block;color:var(--mut);font-size:12px;letter-spacing:1px;margin:12px 0 5px}
input,select{width:100%;padding:12px 13px;border-radius:11px;border:1px solid var(--line);
 background:rgba(255,255,255,.05);color:var(--txt);font-size:15px}
select{background-color:#16233c;color:#eef4fb}
select option{background-color:#16233c;color:#eef4fb}
input::placeholder{color:#6f83a0}
input[type=file]{padding:9px;background:rgba(255,255,255,.05)}
input[type=file]::file-selector-button{background:rgba(58,160,255,.18);color:#cfe6ff;border:1px solid var(--line);
 border-radius:8px;padding:7px 12px;margin-right:10px;cursor:pointer}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:560px){.row{grid-template-columns:1fr}.dot2 b{display:none}}
button{padding:13px 22px;border:0;border-radius:26px;background:linear-gradient(90deg,#3aa0ff,#37e6ff);
 color:#04101f;font-weight:700;font-size:15px;cursor:pointer}
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
 <div class=dot2 data-d=2><i>2</i><b>BYD-Zugang</b></div>
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
 </div>
 <div class=ok>
  🔒 <b>Deine Daten bleiben auf diesem Rechner.</b> Zugangsdaten und Fahrzeugdaten werden nur lokal
  gespeichert. Dieses Programm sendet <b>nichts</b> an den Entwickler — es spricht nur mit der
  BYD-Cloud selbst. Nachlesbar: die Datei <code>evcockpit.py</code> ist normaler, lesbarer Text.
 </div>
 <div class=chk>
  <input type=checkbox id=ack onchange="document.getElementById('n1').disabled=!this.checked">
  <div><div class=h>Verstanden — ich verwende ein zweites BYD-Konto</div>
   <small>Oder: mir ist bewusst, dass es sonst mit meiner BYD-App kollidieren kann.</small></div>
 </div>
 <div class=nav><span></span><button id=n1 disabled onclick="go(2)">Weiter →</button></div>
</div>

<!-- ============ 2: BYD-ZUGANG ============ -->
<div class=pan data-p=2>
 <div class=card>
  <label>E-Mail deines BYD-Kontos <span style="color:#ffb020">(das zweite!)</span></label>
  <input id=username placeholder="name@beispiel.at" autocomplete=off>
  <label>Passwort</label>
  <input id=password type=password placeholder="Passwort" autocomplete=off>
  <label>Steuer-PIN (6-stellig — dieselbe wie in der BYD-App)</label>
  <input id=pin placeholder="z.B. 123456" maxlength=6 autocomplete=off>
  <div class=row>
   <div><label>Land</label><select id=country>__COUNTRIES__</select></div>
   <div><label>Zeitzone</label><select id=tz>__TZ__</select></div>
  </div>
  <div style="margin-top:16px"><button class=sec onclick="detect()">🔍 Meine Fahrzeuge abrufen</button></div>
  <div class=msg id=dmsg></div>
 </div>
 <small>Beim Abrufen meldet sich dein Rechner einmal bei BYD an — so wie deine Handy-App auch.
 Klappt es nicht, stimmt meistens das <b>Land</b> nicht.</small>
 <div class=nav><button class=sec onclick="go(1)">← Zurück</button>
  <button id=n2 disabled onclick="go(3)">Weiter →</button></div>
</div>

<!-- ============ 3: DEIN AUTO ============ -->
<div class=pan data-p=3>
 <div class=card>
  <label>Dein Fahrzeug</label>
  <select id=vin><option value="">— erst Fahrzeuge abrufen —</option></select>
  <label>Modell (setzt die Akkugröße)</label>
  <select id=model onchange="setkwh()">__MODELS__</select>
  <div class=row>
   <div><label>Akku nutzbar in kWh — <b>bitte prüfen</b></label><input id=kwh value="43.2"></div>
   <div><label>Reifendruck-Sollwert (kPa, optional)</label><input id=tyretarget placeholder="z.B. 250"></div>
  </div>
  <div style="margin-top:18px"><button class=sec onclick="capsLaden()">🔎 Was kann mein Auto?</button></div>
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
    <small>Zeigt den <b>Börsen-Strompreis</b> deines Landes als Stundenbalken mit der günstigsten
    Stunde. Quelle: aWATTar (AT/DE) bzw. energy-charts.info (Fraunhofer ISE), kostenlos, ohne Konto.<br>
    <b>Ehrlich:</b> Das ist der <b>Börsenpreis</b>, <b>nicht</b> was auf deiner Rechnung steht (Netz,
    Steuern, Aufschläge fehlen). Nur mit einem <b>Börsentarif</b> (Tibber, aWATTar, smartENERGY) ist
    das dein echter Verlauf. Bei Fixtarif bloß interessant.<br>
    Dein Rechner fragt dann diese Preisseite ab (die sieht deine IP, wie bei jedem Webseitenbesuch)
    — <b>keine Fahrzeugdaten</b>.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=chargers>
   <div><div class=h>🔌 Ladesäulen in der Nähe anzeigen</div>
    <small>Öffentliche Ladestationen rund um den <b>aktuellen Standort deines Autos</b> — Betreiber,
    Entfernung, Steckertyp. Quelle: <b>OpenStreetMap</b>, kein Konto.<br>
    <b>Ehrlich: keine Preise.</b> Es gibt keine verlässliche freie Quelle für aktuelle Ladepreise —
    falsche Preise wären schlimmer als gar keine. Auch die Standorte pflegen Freiwillige: meist gut,
    aber ohne Gewähr. E-Bike-Ladepunkte filtern wir raus.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=lan>
   <div><div class=h>📱 Auch auf Tablet/Handy im Heimnetz öffnen</div>
    <small>Ohne Haken ist das Cockpit <b>nur auf diesem Rechner</b> erreichbar — die sicherste
    Einstellung. Mit Haken erreichst du es auch vom Küchen-Tablet im eigenen WLAN; die Adresse zeigt
    dir das Cockpit dann unten an. Nur im eigenen, vertrauenswürdigen Netz aktivieren: das Cockpit
    kann die Klimaanlage deines Autos steuern.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=ha onchange="document.getElementById('harow').style.display=this.checked?'block':'none'">
   <div><div class=h>🏠 Ans Home Assistant senden</div>
    <small>Du nutzt <b>Home Assistant</b>? Dann schickt das Cockpit dein Auto dorthin — es taucht
    <b>von selbst auf</b>, mit allen Werten und den Klima-Knöpfen. Kein YAML, nichts konfigurieren.
    Praktisch, wenn du dort schon deine PV-Anlage oder Wallbox hast: dann siehst du alles auf einem Bild.<br>
    <b>Voraussetzung:</b> ein MQTT-Broker (bei HA meist das <b>Mosquitto</b>-Add-on, einmal installieren).<br>
    <b>Tipp:</b> Am besten läuft dieses Programm dann auf dem Gerät, auf dem auch HA läuft
    (Raspberry, NAS, Mini-PC) — dann hat HA rund um die Uhr Daten. Dafür gibt es das
    Linux-Paket und eine Autostart-Anleitung in der LIESMICH.</small></div>
  </div>
  <div id=harow style="display:none;margin-top:8px">
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
    <small>Du hast eine <b>PV-Anlage</b> und sie ist in Home Assistant eingebunden? Dann zeigt das
    Cockpit deine <b>aktuelle Solar-Leistung</b> direkt neben Ladestand und Strompreis — du siehst
    auf einen Blick, ob du gerade <b>mit eigener Sonne</b> lädst oder teuer aus dem Netz.<br>
    <b>Warum das so gut geht:</b> Wir reden nicht mit deinem Wechselrichter — <b>Home Assistant hat
    das schon erledigt</b>. Egal ob Fronius, SMA, Huawei, SolarEdge oder Kostal: in HA ist es einfach
    ein Sensor mit einem Wert in Watt. Den holen wir uns, sonst nichts.<br>
    <b>Ehrlich:</b> Wir zeigen, was <b>dein HA</b> sagt. Stimmt der Wert dort nicht, stimmt er hier
    auch nicht. Es wird <b>nur gelesen</b> — wir schreiben nie etwas in dein HA.</small></div>
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
   <div><div class=h>🎥 Wächter-Kamera einbinden <small style="display:inline;color:#ffb020">— nur für Bastler</small></div>
    <small>Zeigt die letzte <b>Auslöse-Aufnahme</b> der 360°-Kameras. <b>Braucht alles davon:</b>
    <b>adb</b> auf diesem Rechner (ist <b>nicht</b> im Paket dabei), <b>kabelloses adb am Auto</b>
    freigeschaltet, <b>Overdrive-App</b> + <b>USB-Stick</b> im Auto.<br>
    Sagt dir das nichts? <b>Haken weglassen</b> — alles andere geht trotzdem.</small></div>
  </div>
  <div id=adbrow style="display:none;margin-top:8px">
   <label>adb-Adresse des Autos (z.B. 192.168.0.50:5555)</label>
   <input id=caradb placeholder="IP:Port">
  </div>

  <div class=chk>
   <input type=checkbox id=upd>
   <div><div class=h>🔔 Auf neue Versionen hinweisen</div>
    <small>Das Cockpit schaut dann <b>einmal am Tag</b> nach, ob es eine neuere Version gibt, und zeigt
    dir oben einen kleinen Hinweis. Nützlich für Fehlerbehebungen — du musst sonst selbst mitbekommen,
    wenn etwas repariert wurde.<br>
    <b>Wie das ohne Datenabfluss geht:</b> Dein Rechner lädt nur eine kleine Textdatei mit der neuesten
    Versionsnummer und <b>vergleicht sie selbst</b>. Der Server erfährt dabei <b>nicht einmal, welche
    Version du hast</b> — es wird nichts über dich gesendet, kein Ident, kein Modell, keine Fahrzeugdaten.<br>
    <b>Ehrlich:</b> Beim Abholen sieht der Server – wie bei jedem Webseitenbesuch – deine IP. Wir schreiben
    sie nirgends auf. Ohne Haken passiert gar nichts.</small></div>
  </div>

  <div class=chk>
   <input type=checkbox id=count>
   <div><div class=h>📊 Anonym mitzählen, dass ich das Tool nutze</div>
    <small>Damit der Entwickler sieht, ob sich die Arbeit lohnt. <b>Einmal am Tag wird genau das
    gesendet — und sonst nichts:</b>
    <div style="background:rgba(0,0,0,.3);border-radius:8px;padding:9px;margin:7px 0;font-family:ui-monospace,monospace;font-size:12px;color:#cfe6ff">
    { "id": "zufällige Nummer", "version": "1.0", "model": "dein Modell" }</div>
    Kein Name, keine E-Mail, keine VIN, kein Standort, keine Fahrdaten. Ohne Haken sendet das
    Programm <b>gar nichts</b> an den Entwickler.</small></div>
  </div>
 </div>

 <div class=nav><button class=sec onclick="go(4)">← Zurück</button>
  <button onclick="save()">✅ Fertig — Cockpit starten</button></div>
 <div class=msg id=smsg></div>

 <div class=card id=logoutbox style="display:none;margin-top:18px">
  <div style="color:var(--mut);font-size:12px;letter-spacing:1px;margin-bottom:8px">ABMELDEN</div>
  <small>Löscht deine BYD-Zugangsdaten, die gespeicherten Fahrzeugdaten und dein Foto
  <b>von diesem Rechner</b>. Dein BYD-Konto selbst bleibt unangetastet.</small>
  <div style="margin-top:12px"><button class=sec style="border-color:rgba(255,120,90,.5);color:#ff9d84"
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
 2:['Dein BYD-Zugang','Damit holt dein Rechner die Daten direkt von BYD.'],
 3:['Dein Auto','Welches Fahrzeug, und wie groß ist der Akku?'],
 4:['Dein Cockpit','Ein Foto und wie oft nachgefragt wird.'],
 5:['Extras','Alles freiwillig — lass ruhig alles aus.']};
function go(n){
 if(n===3&&!document.getElementById('vin').value){
  document.getElementById('dmsg').textContent='⚠️ Bitte zuerst „Meine Fahrzeuge abrufen" drücken.';return;}
 SCHRITT=n;
 document.querySelectorAll('.pan').forEach(p=>p.classList.toggle('on',+p.dataset.p===n));
 document.querySelectorAll('.dot2').forEach(d=>{const k=+d.dataset.d;
  d.classList.toggle('on',k===n); d.classList.toggle('done',k<n);
  d.querySelector('i').textContent = k<n ? '✓' : k;});
 document.getElementById('wtitle').textContent=TITEL[n][0];
 document.getElementById('wsub').textContent=TITEL[n][1];
 window.scrollTo({top:0,behavior:'smooth'});
}
function setkwh(){document.getElementById('kwh').value=KWH[document.getElementById('model').value]||60;}
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
 if(VOR.tyre_target) document.getElementById('tyretarget').value=VOR.tyre_target;
 if(VOR.features){document.getElementById('capsmsg').textContent=
   'ℹ️ Deine Auswahl ist gespeichert. Erneut abfragen, um sie zu ändern.';}
 if(VOR.poll_min) document.getElementById('poll').value=String(VOR.poll_min);
 document.getElementById('lan').checked=!!VOR.lan;
 document.getElementById('count').checked=!!VOR.count_optin;
 document.getElementById('upd').checked=!!VOR.update_check;
 document.getElementById('price').checked=!!VOR.show_price;
 document.getElementById('chargers').checked=!!VOR.show_chargers;
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
   '<img src="/photo?t='+Date.now()+'" style="max-height:130px;border-radius:12px;border:1px solid rgba(120,165,235,.18)"><br><small>Aktuelles Foto — neues wählen zum Ersetzen</small>';
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
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
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
 try{const r=await (await fetch('/detect',{method:'POST',body:JSON.stringify(body())})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  const s=document.getElementById('vin');s.innerHTML='';
  r.vehicles.forEach(v=>{const o=document.createElement('option');o.value=v.vin;o.textContent=(v.name?v.name+' — ':'')+v.vin;s.appendChild(o);});
  m.textContent='✅ '+r.vehicles.length+__T(' Fahrzeug(e) gefunden — weiter unten mit Weiter');
  document.getElementById('n2').disabled=false;
 }catch(e){m.textContent='⚠️ Fehler: '+e}}
let PHOTO='';
function pickphoto(inp){const f=inp.files[0];if(!f)return;
 const r=new FileReader();
 r.onload=e=>{const img=new Image();
  img.onload=()=>{ // auf max 1100px runterrechnen -> aus 4MB-Handyfoto werden ~200KB
   const mx=1100,sc=Math.min(1,mx/Math.max(img.width,img.height));
   const c=document.createElement('canvas');c.width=Math.round(img.width*sc);c.height=Math.round(img.height*sc);
   c.getContext('2d').drawImage(img,0,0,c.width,c.height);
   PHOTO=c.toDataURL('image/jpeg',0.86);
   document.getElementById('pprev').innerHTML='<img src="'+PHOTO+'" style="max-height:130px;border-radius:12px;border:1px solid rgba(120,165,235,.18)">';
  };img.src=e.target.result;};
 r.readAsDataURL(f);}
async function save(){const m=document.getElementById('smsg');
 const b=body(); b.vin=document.getElementById('vin').value; b.battery_kwh=parseFloat(document.getElementById('kwh').value);
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
 b.pv=document.getElementById('pv').checked;
 b.pv_url=document.getElementById('pvurl').value.trim();
 b.pv_token=document.getElementById('pvtoken').value.trim();
 b.pv_entity=document.getElementById('pventity').value;
 b.ha=document.getElementById('ha').checked;
 b.ha_host=document.getElementById('hahost').value.trim();
 b.ha_port=parseInt(document.getElementById('haport').value,10)||1883;
 b.ha_user=document.getElementById('hauser').value.trim();
 b.ha_pass=document.getElementById('hapass').value;
 b.sentry=document.getElementById('sentry').checked;
 b.car_adb=document.getElementById('caradb').value.trim();
 if(!b.vin){m.textContent='⚠️ Bitte erst Fahrzeuge abrufen und eins auswählen';return;}
 m.textContent='⏳ Speichere …';
 try{const r=await (await fetch('/save',{method:'POST',body:JSON.stringify(b)})).json();
  if(r.ok){m.innerHTML=b.lan?'✅ Gespeichert — Cockpit startet …<br><small>Für den Tablet-Zugriff das Programm einmal neu starten.</small>'
                            :'✅ Gespeichert — Cockpit startet …';
   setTimeout(()=>location.href='/',b.lan?3200:1600);}
  else m.textContent='⚠️ '+r.error;}catch(e){m.textContent='⚠️ '+e}}
setkwh(); vorfuellen();
</script></body></html>"""


# ---------------------------------------------------------------- Cockpit (HTML)
COCKPIT = r"""<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit</title>
<link rel=stylesheet href="/static/leaflet.css">
<style>
:root{--blue:#3aa0ff;--cyan:#37e6ff;--txt:#eef4fb;--mut:#8ea3bd;--line:rgba(120,165,235,.16)}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:radial-gradient(1100px 720px at 50% -8%,#12213f 0%,#0a1120 55%,#05080f 100%) fixed;
 color:var(--txt);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:22px}
.wrap{max-width:1040px;margin:0 auto}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.brand{color:var(--mut);letter-spacing:4px;font-weight:700;font-size:13px}
.on{color:var(--mut);font-size:12px;display:flex;align-items:center;gap:7px}
.dot{width:9px;height:9px;border-radius:50%;background:#35e6a0;box-shadow:0 0 10px #35e6a0}.dot.off{background:#5a6b7d;box-shadow:none}
.hero{display:grid;grid-template-columns:280px 1fr;gap:12px;align-items:center;margin:6px 0 16px}
.ring{position:relative;width:250px;height:250px;margin:0 auto}
svg.ring{transform:rotate(-90deg)}
.ring .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.ring .pct{font-size:64px;font-weight:300;line-height:1}.ring .pct small{font-size:22px;color:var(--mut)}
.ring .lbl{color:var(--mut);font-size:12px;letter-spacing:2px;margin-top:4px}
.range{text-align:center;margin-top:8px}.range b{font-size:28px;font-weight:300}.range b small{font-size:16px;color:var(--mut)}
.range .lbl{color:var(--mut);font-size:11px;letter-spacing:2px}
.car{display:flex;align-items:center;justify-content:center;min-height:250px}
.car img{max-width:100%;max-height:250px;filter:drop-shadow(0 24px 40px rgba(58,160,255,.35))}
.car svg{max-width:100%;max-height:210px;filter:drop-shadow(0 22px 38px rgba(58,160,255,.4))}
.car .hint{margin-top:12px;text-align:center}
.car .hint a{color:var(--mut);font-size:12px;text-decoration:none;border:1px solid var(--line);
 border-radius:20px;padding:7px 14px;display:inline-block;transition:.15s}
.car .hint a:hover{color:var(--txt);border-color:rgba(120,165,235,.4);background:rgba(255,255,255,.04)}
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
.pill.heat.on{background:rgba(255,90,70,.16);border-color:rgba(255,120,90,.55);color:#ff9d84;box-shadow:0 0 22px rgba(255,90,70,.25)}
.pill.batt.on{background:rgba(255,90,70,.16);border-color:rgba(255,120,90,.55);color:#ff9d84;box-shadow:0 0 22px rgba(255,90,70,.25)}
.pill.cool.on{background:rgba(58,160,255,.16);border-color:rgba(90,180,255,.55);color:#7cc4ff;box-shadow:0 0 22px rgba(58,160,255,.28)}
.msg{color:var(--mut);font-size:12.5px;min-height:18px;margin:8px 2px;text-align:center}
.chips{display:flex;gap:10px;flex-wrap:wrap}
.chip{border:1px solid var(--line);border-radius:16px;padding:8px 14px;font-size:13px;background:rgba(255,255,255,.03)}
.chip .cm{color:var(--mut)}.okc{color:#5be3a3}.no{color:#8ea3bd}.warnc{color:#ffb020}
.bars{display:flex;align-items:flex-end;gap:3px;height:110px;margin-top:12px;padding:12px 10px 0;
 background:linear-gradient(180deg,rgba(255,255,255,.05),rgba(255,255,255,.02));border:1px solid var(--line);border-radius:16px}
.bar{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;position:relative}
.bar i{display:block;width:100%;border-radius:4px 4px 0 0;background:rgba(120,165,235,.35);transition:.2s}
.bar.now i{background:linear-gradient(180deg,#37e6ff,#3aa0ff);box-shadow:0 0 12px rgba(58,160,255,.6)}
.bar.cheap i{background:linear-gradient(180deg,#5be3a3,#28c07d);box-shadow:0 0 12px rgba(91,227,163,.5)}
.bar b{font-size:9px;color:var(--mut);margin-top:4px;font-weight:400}
.bar.now b,.bar.cheap b{color:var(--txt);font-weight:700}
.bar span.t{position:absolute;top:-13px;font-size:9px;color:var(--mut);white-space:nowrap}
.chg{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 13px;
 border-bottom:1px solid rgba(120,165,235,.10)}
.chg:last-child{border-bottom:0}
.chg .nm{font-size:14px}.chg .sub{color:var(--mut);font-size:11.5px;margin-top:2px}
.chg .km{color:var(--cyan);font-size:15px;white-space:nowrap;font-weight:300}
.chg a{color:inherit;text-decoration:none}
.map{border:1px solid var(--line);border-radius:18px;overflow:hidden;height:340px;position:relative;z-index:0}
#lmap{width:100%;height:100%;background:#0a1120}
.leaflet-tile{filter:grayscale(.55) brightness(.72) contrast(1.06)}
.leaflet-container{background:#0a1120;font:inherit}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#16233c;color:#eef4fb}
.leaflet-popup-content{margin:11px 14px;font-size:13px;line-height:1.5}
.leaflet-popup-content b{color:#7cc4ff}
.leaflet-control-attribution{background:rgba(10,17,32,.8)!important;color:#8ea3bd!important;font-size:10px!important}
.leaflet-control-attribution a{color:#8ea3bd!important}
.leaflet-bar a{background:#16233c!important;color:#eef4fb!important;border-color:rgba(120,165,235,.2)!important}
.mk-car{width:22px;height:22px;border-radius:50%;background:linear-gradient(180deg,#37e6ff,#3aa0ff);
 border:2px solid #eef4fb;box-shadow:0 0 0 6px rgba(58,160,255,.28),0 0 16px rgba(58,160,255,.7)}
.mk-chg{width:18px;height:18px;border-radius:50%;background:#28c07d;border:2px solid #0a1120;
 box-shadow:0 0 10px rgba(91,227,163,.6);display:flex;align-items:center;justify-content:center;
 font-size:10px;color:#04101f;font-weight:700}

.err{background:rgba(255,90,70,.10);border:1px solid rgba(255,120,90,.4);border-radius:14px;padding:10px 14px;
 font-size:13px;color:#ff9d84;margin-bottom:12px;display:none}
a.cfg{color:var(--mut);font-size:12px;text-decoration:none}
.glocke{cursor:pointer;font-size:14px;user-select:none;opacity:.55;transition:.15s}
.glocke:hover{opacity:1}.glocke.an{opacity:1}
@media(max-width:640px){.hero{grid-template-columns:1fr}.car{min-height:170px}.car img{max-height:180px}}
</style></head><body><div class=wrap>
 <div id=updbar style="display:none;background:linear-gradient(90deg,rgba(58,160,255,.16),rgba(55,230,255,.10));
  border:1px solid rgba(90,180,255,.45);border-radius:14px;padding:11px 15px;margin-bottom:14px;font-size:13.5px">
  🔔 <b>Version <span id=updver></span> ist da.</b> <span id=updwas style="color:var(--mut)"></span>
  <a id=updlink href="#" target="_blank" rel="noopener" style="color:var(--blue);margin-left:6px">Ansehen →</a>
 </div>
 <div class=top><div class=brand>EV · COCKPIT</div>
  <div class=on><span id=dot class=dot></span><span id=onl>—</span>
   &nbsp;<span id=glocke class=glocke onclick="glockeUm()" title="Benachrichtigen, wenn das Laden fertig ist">🔕</span>
   &nbsp;<a class=cfg href="/setup">⚙︎</a></div></div>
 <div class=err id=err></div>
 <div class=hero>
  <div>
   <div class=ring><svg class=ring width=250 height=250 viewBox="0 0 250 250">
    <circle cx=125 cy=125 r=112 fill=none stroke="#16243f" stroke-width=14/>
    <circle id=arc cx=125 cy=125 r=112 fill=none stroke="url(#g)" stroke-width=14 stroke-linecap=round stroke-dasharray=703 stroke-dashoffset=703/>
    <defs><linearGradient id=g x1=0 y1=0 x2=1 y2=1><stop offset=0% stop-color="#3aa0ff"/><stop offset=100% stop-color="#37e6ff"/></linearGradient></defs>
   </svg><div class=val><div class=pct><span id=soc>–</span><small>%</small></div><div class=lbl>AKKU</div></div></div>
   <div class=range><b><span id=range>–</span><small> km</small></b><div class=lbl>REICHWEITE (ECHT)</div>
    <div class=lbl style="margin-top:3px">BYD sagt: <span id=bydrange>–</span> km</div></div>
  </div>
  <div class=car id=car><div class=ph>Kein Foto hinterlegt<br><small>⚙︎ → Foto-URL</small></div></div>
 </div>

 <div class=grid style="grid-template-columns:repeat(4,1fr)">
  <div class=tile><div class=k>KILOMETERSTAND</div><div class=v><span id=odo>–</span><small> km</small></div></div>
  <div class=tile><div class=k>AUSSEN</div><div class=v><span id=tout>–</span><small> °C</small></div></div>
  <div class=tile><div class=k>VERBRAUCH Ø</div><div class=v><span id=cons>–</span><small> kWh</small></div></div>
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
    <div id=pverr style="display:none;color:#ffb020;font-size:12px;margin-top:6px"></div>
   </div>
  </div>
 </div>

 <div class=sect>KLIMA</div>
 <div class=klima>
  <div class="pill heat" onclick="cmd('heat')">🔥&nbsp; Heizen</div>
  <div class="pill cool" onclick="cmd('cool')">❄&nbsp; Kühlen</div>
  <div class="pill" onclick="cmd('off')">◼&nbsp; Aus</div>
  <div class="pill batt" id=p_batt onclick="battUm()">🔋&nbsp; Batterie vorheizen</div>
 </div>
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
  <div class=sect>LADEN</div>
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
  <div class=sect>STROMPREIS (BÖRSE)</div>
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
   <div id=s_err style="display:none;color:#ffb020;font-size:12.5px;margin-top:8px"></div>
   <img id=s_img alt="Wächter-Aufnahme" style="display:none;width:100%;max-height:440px;object-fit:contain;
    background:#0a1120;border:1px solid var(--line);border-radius:14px;margin-top:10px">
  </div>
 </div>

 <div id=chgbox style="display:none">
  <div class=sect>LADESÄULEN IN DER NÄHE</div>
  <div class=tile style="padding:6px 4px"><div id=chglist></div></div>
  <div style="color:var(--mut);font-size:11.5px;margin:8px 2px 0">
   Daten: © OpenStreetMap-Mitwirkende (ODbL) · von Freiwilligen gepflegt, ohne Gewähr ·
   <b>bewusst ohne Preisangaben</b>
  </div>
 </div>

 <div class=sect>STANDORT</div>
 <div class=map><div id=lmap></div></div>
 <div style="color:var(--mut);font-size:11.5px;margin:8px 2px 0">
  🔵 dein Auto · 🟢 Ladesäulen (anklickbar) — Karte © OpenStreetMap-Mitwirkende
 </div>
 <div id=lanhint style="display:none;margin:16px 2px 0;color:var(--mut);font-size:13px;text-align:center">
  📱 Auf Tablet/Handy im selben WLAN erreichbar unter <b id=lanurl style="color:var(--blue)"></b>
 </div>
 <div style="text-align:center;margin:18px 0 4px">
  <a href="/about" style="color:var(--mut);font-size:12px;text-decoration:none">Impressum · Haftungsausschluss · Datenschutz</a>
 </div>
</div>
<script src="/static/leaflet.js"></script>
<script>
const SIL={
klein:'<svg viewBox="0 0 320 130" xmlns="http://www.w3.org/2000/svg"><g transform="translate(16,14)"><path d="M 8,96 L 10,70 C 12,57 22,49 40,46 L 66,43 L 96,15 C 102,8 112,5 126,5 L 200,5 C 214,5 224,9 230,17 L 250,45 L 272,51 C 284,55 288,65 288,76 L 288,96 Z" fill="#3aa0ff"/><circle cx="60" cy="96" r="19" fill="#0a1120"/><circle cx="60" cy="96" r="12" fill="#3aa0ff"/><circle cx="240" cy="96" r="19" fill="#0a1120"/><circle cx="240" cy="96" r="12" fill="#3aa0ff"/></g></svg>',
suv:'<svg viewBox="0 0 320 135" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,12)"><path d="M 6,100 L 8,62 C 10,48 20,40 38,37 L 60,34 L 88,10 C 94,4 104,1 118,1 L 214,1 C 228,1 238,5 242,13 L 252,36 L 278,42 C 290,46 294,56 294,68 L 294,100 Z" fill="#3aa0ff"/><circle cx="58" cy="100" r="22" fill="#0a1120"/><circle cx="58" cy="100" r="14" fill="#3aa0ff"/><circle cx="244" cy="100" r="22" fill="#0a1120"/><circle cx="244" cy="100" r="14" fill="#3aa0ff"/></g></svg>',
limo:'<svg viewBox="0 0 330 130" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,14)"><path d="M 6,96 L 8,72 C 10,60 20,52 38,49 L 74,45 L 108,17 C 114,10 124,7 138,7 L 196,7 C 210,7 220,11 226,18 L 258,46 L 282,50 C 294,54 298,64 298,74 L 298,96 Z" fill="#3aa0ff"/><circle cx="62" cy="96" r="19" fill="#0a1120"/><circle cx="62" cy="96" r="12" fill="#3aa0ff"/><circle cx="248" cy="96" r="19" fill="#0a1120"/><circle cx="248" cy="96" r="12" fill="#3aa0ff"/></g></svg>',
gross:'<svg viewBox="0 0 335 145" xmlns="http://www.w3.org/2000/svg"><g transform="translate(14,12)"><path d="M 4,112 L 6,66 C 8,52 18,44 36,41 L 56,38 L 82,14 C 88,8 98,5 112,5 L 228,5 C 242,5 252,9 256,17 L 264,40 L 288,46 C 300,50 304,60 304,72 L 304,112 Z" fill="#3aa0ff"/><circle cx="58" cy="112" r="23" fill="#0a1120"/><circle cx="58" cy="112" r="15" fill="#3aa0ff"/><circle cx="252" cy="112" r="23" fill="#0a1120"/><circle cx="252" cy="112" r="15" fill="#3aa0ff"/></g></svg>'};
const C=703;
function nv(x){return (x==null||x==='')?'–':x}
function yn(id,cond,ja,nein,warn){var e=document.getElementById(id);if(!e)return;
 e.textContent=cond?ja:nein;e.className=warn?(cond?'warnc':'okc'):(cond?'okc':'no');}

// --- Leaflet-Karte: dein Auto + die Ladesaeulen auf EINER Karte ---
let MAP=null, MK_CAR=null, MK_CHG=[];
function zeichneKarte(s){
 if(!s.latitude||!s.longitude||typeof L==='undefined') return;
 const pos=[s.latitude,s.longitude];
 if(!MAP){
  MAP=L.map('lmap',{zoomControl:true,attributionControl:true,scrollWheelZoom:false}).setView(pos,13);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
   {maxZoom:18,attribution:'© OpenStreetMap'}).addTo(MAP);
 }
 const ic=L.divIcon({className:'',html:'<div class=mk-car></div>',iconSize:[22,22],iconAnchor:[11,11]});
 if(!MK_CAR){MK_CAR=L.marker(pos,{icon:ic,zIndexOffset:1000}).addTo(MAP).bindPopup('<b>Dein Auto</b>');}
 else{MK_CAR.setLatLng(pos);}
 const key=JSON.stringify((s.chargers||[]).map(c=>c.lat+','+c.lon));
 if(MAP._k!==key){
  MAP._k=key; MK_CHG.forEach(m=>MAP.removeLayer(m)); MK_CHG=[];
  const ic2=L.divIcon({className:'',html:'<div class=mk-chg>⚡</div>',iconSize:[18,18],iconAnchor:[9,9]});
  (s.chargers||[]).forEach(c=>{
   const d=[c.operator,c.sockets,(c.kw?c.kw+' kW':'')].filter(Boolean).join(' · ');
   MK_CHG.push(L.marker([c.lat,c.lon],{icon:ic2}).addTo(MAP)
    .bindPopup('<b>'+c.name+'</b>'+(d?'<br>'+d:'')+'<br>'+c.km+__T(' km entfernt')));
  });
  if(MK_CHG.length){MAP.fitBounds(L.featureGroup(MK_CHG.concat([MK_CAR])).getBounds().pad(0.15));}
 }
}

// --- Benachrichtigungen: entstehen im Browser, verlassen den Rechner NICHT ---
let LETZTER = {};                       // vorheriger Zustand, um Wechsel zu erkennen
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
async function load(){try{
 const s=await (await fetch('/data')).json();
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
 // Reifen-Ampel — nur wenn der Nutzer einen Sollwert eingetragen hat
 const tm=document.getElementById('tyremsg');
 if(s.reifen){tm.style.display='block';tm.textContent=s.reifen.text;
  tm.style.color = s.reifen.stufe==='rot' ? '#ff9d84' : (s.reifen.stufe==='gelb' ? '#ffb020' : '#5be3a3');
  document.getElementById('tyrebox').style.borderColor =
    s.reifen.stufe==='rot' ? 'rgba(255,120,90,.55)' : (s.reifen.stufe==='gelb' ? 'rgba(255,176,32,.45)' : 'var(--line)');
 } else {tm.style.display='none';}
 // Laeuft die Klima? Das Auto meldet nur AN/AUS (kein "heizt gerade") -> beide Pills markieren
 const an=(s.klima_on==='ON');
 document.querySelector('.pill.heat').classList.toggle('on',an);
 document.querySelector('.pill.cool').classList.toggle('on',an);
 document.querySelector('.pill.batt').classList.toggle('on',s.battery_heat==='ON');
 if(s._msg&&!document.getElementById('msg').dataset.hold)document.getElementById('msg').textContent=s._msg;
 yn('s_lock',s.locked==='ON','Ja','Nein');
 yn('s_door',s.doors_open!=='ON','zu','OFFEN',true);
 yn('s_win',s.windows_open!=='ON','zu','OFFEN',true);
 yn('s_plug',s.plugged==='ON','Ja','Nein');
 yn('s_charge',s.charging==='ON','Ja','Nein');
 document.getElementById('s_gear').textContent=nv(s.gear);document.getElementById('s_gear').className='cm';
 // Eigenes Foto? Sonst gezeichnete Silhouette + Hinweis, dass man sein Auto einsetzen kann.
 const car=document.getElementById('car'), pk=s.photo||('sil:'+(s.silhouette||'klein'));
 if(car.dataset.p!==pk){car.dataset.p=pk;
  if(s.photo){car.innerHTML='<img src="'+s.photo+'" alt="Auto">';}
  else{car.innerHTML='<div class=wrap>'+(SIL[s.silhouette]||SIL.klein)+
   '<div class=hint><a href="/setup">📷 Eigenes Foto deines Autos einsetzen</a></div></div>';}}
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
  const k=JSON.stringify(s.chargers), box=document.getElementById('chglist');
  if(box.dataset.k!==k){box.dataset.k=k;
   box.innerHTML=s.chargers.map(c=>{
    const d=[c.operator,c.sockets,(c.kw?c.kw+' kW':''),(c.n?c.n+'x':'')].filter(Boolean).join(' · ');
    return '<div class=chg><div><div class=nm>'+
      '<a href="https://www.openstreetmap.org/?mlat='+c.lat+'&mlon='+c.lon+'#map=17/'+c.lat+'/'+c.lon+'" target="_blank" rel="noopener">'+
      c.name+'</a></div>'+(d?'<div class=sub>'+d+'</div>':'')+'</div><div class=km>'+c.km+' km</div></div>';
   }).join('');}
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
}catch(e){}}
function zusperren(){
 if(confirm('Auto wirklich zusperren?')) cmd('lock');}
function battUm(){ // an/aus je nach aktuellem Zustand des Autos
 const an=document.querySelector('.pill.batt').classList.contains('on');
 cmd(an?'batt_off':'batt_on');}
async function cmd(a){var m=document.getElementById('msg');m.dataset.hold=1;m.textContent='⏳ Sende …';
 try{await fetch('/cmd?a='+a,{method:'POST'});}catch(e){m.textContent='⚠️ Dienst weg';}
 setTimeout(()=>{m.dataset.hold='';load();},3000);}
glockeMalen(); load(); setInterval(load,8000);
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

ENERGY_PANEL = r'''<section id="energy-panel" style="margin:22px auto;max-width:1100px;padding:20px;border:1px solid #34506c;border-radius:18px;background:#101e30;color:#eaf2ff;font:15px system-ui">
<h2 style="margin:0 0 8px">⚡ Energie &amp; Ladepunkte</h2>
<p style="color:#a8bed5">PV, Netz, Speicher und mehrere Ladepunkte – direkt in deinem Cockpit. evcc steuert; das Cockpit zeigt nur an.</p>
<div style="display:flex;gap:8px;flex-wrap:wrap"><input id="evcc-host" placeholder="evcc-IP (z. B. 192.168.1.20)" style="padding:10px;border-radius:8px;background:#1b3047;color:white;border:1px solid #456">
<input id="evcc-port" type="number" value="7070" style="width:90px;padding:10px;background:#1b3047;color:white;border:1px solid #456;border-radius:8px">
<button id="evcc-connect" style="padding:10px;border-radius:8px;cursor:pointer">Verbinden</button>
<button id="evcc-discover" style="padding:10px;border-radius:8px;cursor:pointer">Geräte suchen</button></div>
<div id="evcc-message" style="margin:12px 0;color:#a8bed5">Optional – noch nicht verbunden</div>
<div id="evcc-values" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(145px,1fr));gap:10px"></div>
<h3>Ladepunkte / Fahrzeuge</h3><div id="evcc-points" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px"></div>
<div id="evcc-discovery" style="margin-top:12px"></div>
</section>
<script>
(function(){
 const el=id=>document.getElementById(id), h=el('evcc-host'),p=el('evcc-port');
 h.value=localStorage.getItem('evc_evcc_host')||'';
 p.value=localStorage.getItem('evc_evcc_port')||'7070';
 const card=(name,value)=>'<div style="background:#192d44;border-radius:12px;padding:14px"><div style="color:#a8bed5">'+name+'</div><strong style="font-size:23px">'+value+'</strong></div>';
 const kw=v=>typeof v==='number'?(v/1000).toLocaleString('de-DE',{maximumFractionDigits:2})+' kW':'–';
 const escapeHtml=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 async function refresh(){
  if(!h.value)return;
  try{
   const response=await fetch('/energy/state?host='+encodeURIComponent(h.value)+'&port='+encodeURIComponent(p.value));
   const d=await response.json();if(!response.ok)throw Error(d.error||'API error');
   const site=d.site||{};
   el('evcc-values').innerHTML=card('☀️ PV',kw(site.pv_w))+card('⚡ Netz (+ Bezug / − Einspeisung)',kw(site.grid_w))+card('🔋 Speicher',kw(site.battery_w))+card('🏠 Haus',kw(site.home_w));
   const vehicles=d.profiles||d.vehicles||[];
   const selected=localStorage.getItem('evc_selected_vehicle')||'';
   const vehicleCards=vehicles.map(v=>'<button type="button" data-vehicle="'+escapeHtml(v.id)+'" style="text-align:left;background:#192d44;border:1px solid '+(selected===v.id?'#4dd8ce':'#34506c')+';color:#eaf2ff;border-radius:12px;padding:14px;cursor:pointer">🚘 '+escapeHtml(v.title)+' · '+(typeof v.soc==='number'?escapeHtml(v.soc)+' %':'–')+'</button>').join('');
   const chosen=vehicles.find(v=>v.id===selected)||vehicles[0];
   const details=chosen?card('Fahrzeugdetails · '+escapeHtml(chosen.title),
    'Akku: '+(typeof chosen.soc==='number'?escapeHtml(chosen.soc)+' %':'–')+
    ' · Reichweite: '+(typeof chosen.range_km==='number'?escapeHtml(chosen.range_km)+' km':'–')+
    ' · Ladepunkt: '+escapeHtml(chosen.loadpoint||'nicht zugeordnet')+
    ' · Ladeleistung: '+kw(chosen.charge_power_w)+
    ' · Status: '+(chosen.charging?'Lädt':chosen.connected?'Angeschlossen':'Nicht angeschlossen')+
    ' · Fahrzeugsteuerung: über Herstellerintegration (hier nur Anzeige)'):'';

   const points=(d.loadpoints||[]).map((x,i)=>card('🔌 '+escapeHtml(x.title||x.name||'Ladepunkt '+(i+1)),kw(x.chargePower))).join('');
   el('evcc-points').innerHTML=vehicleCards+details+points||'Noch keine Fahrzeuge oder Ladepunkte in evcc konfiguriert';
   el('evcc-points').querySelectorAll('[data-vehicle]').forEach(button=>button.addEventListener('click',()=>{
    localStorage.setItem('evc_selected_vehicle',button.getAttribute('data-vehicle'));refresh();
   }));
   el('evcc-message').textContent='evcc verbunden · '+new Date().toLocaleTimeString();
  }catch(e){el('evcc-message').textContent='evcc: '+e.message;}
 }
 el('evcc-connect').onclick=()=>{localStorage.setItem('evc_evcc_host',h.value);localStorage.setItem('evc_evcc_port',p.value);refresh();};
 el('evcc-discover').onclick=async()=>{
  const cidr=prompt('Privates LAN-Netz eingeben (z. B. 192.168.1.0/24). Nur mit Berechtigung scannen:');
  if(!cidr)return;el('evcc-discovery').textContent='Suche läuft …';
  try{
   const r=await fetch('/energy/discover',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cidr})});
   const d=await r.json();if(!r.ok)throw Error(d.error||'Fehler');
   el('evcc-discovery').textContent=(d.found||[]).map(x=>x.vendor+' – '+x.ip).join(' | ')||'Keine unterstützten Geräte gefunden';
  }catch(e){el('evcc-discovery').textContent=e.message;}
 };
 setInterval(refresh,15000);if(h.value)refresh();
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
                                        "battery_kwh", "tyre_target", "lan", "count_optin", "show_price",
                                        "poll_min", "sentry", "car_adb", "show_chargers", "update_check", "features",
                                        "ha", "ha_host", "ha_port", "ha_user",
                                        "pv", "pv_url", "pv_entity")}
        vor["has_pw"] = bool(_CFG.get("password"))
        vor["has_photo"] = PHOTO_FILE.exists()
        vor["vin_known"] = _CFG.get("vin") or ""
        html = (WIZARD.replace("__COUNTRIES__", opts).replace("__TZ__", tzs)
                .replace("__MODELS__", mods).replace("__KWHMAP__", json.dumps(MODELS))
                .replace("__VOR__", json.dumps(vor, ensure_ascii=False)))
        self._send(_i18n(html))

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p.startswith("/static/"):
            # Leaflet aus dem Paket ausliefern — bewusst kein CDN, damit niemand Drittes
            # mitbekommt, dass/wann du dein Auto anschaust.
            name = os.path.basename(p)
            f = STATIC_DIR / name
            if f.exists() and name in ("leaflet.js", "leaflet.css"):
                self._send(f.read_bytes(),
                           "text/css" if name.endswith(".css") else "application/javascript")
            else:
                self._send(b"", "text/plain", 404)
        elif p == "/about":
            self._send(_i18n(ABOUT.replace("__VERSION__", VERSION)))
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
                self._send(json.dumps(result), "application/json")
            except Exception as e:
                self._send(json.dumps({"error": str(e)[:160]}), "application/json", 400)
        elif p == "/data":
            d = dict(_STATE)
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
            d["reifen"] = _reifen_urteil(_STATE)
            d["features"] = _CFG.get("features") or {}
            # Kein eigenes Foto -> welche Silhouette passt zum Modell?
            if not d["photo"]:
                d["silhouette"] = BODY_TYPE.get(_CFG.get("model") or "", "klein")
            d["lan_url"] = ("http://%s:%d" % (lan_ip(), WEBPORT)) if _CFG.get("lan") else ""
            d["sentry_on"] = bool(_CFG.get("sentry"))
            if _MSG["text"] and time.time() - _MSG["ts"] < 120:
                d["_msg"] = _MSG["text"]
            self._send(json.dumps(d), "application/json")
        elif p == "/setup" or not _CFG.get("vin"):
            self._wizard()
        else:
            self._send(_i18n(COCKPIT.replace("</body>", ENERGY_PANEL + "</body>")))

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            ln = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(json.dumps({"error": "Invalid Content-Length"}), "application/json", 400)
        if ln < 0 or ln > 2 * 1024 * 1024:
            return self._send(json.dumps({"error": "Request body too large"}), "application/json", 413)
        raw = self.rfile.read(ln).decode("utf-8") if ln else "{}"
        if u.path == "/energy/discover":
            try:
                from device_hub import discover
                found = discover(json.loads(raw)["cidr"])
                self._send(json.dumps({"found": [{k: v for k, v in item.items() if k != "data"} for item in found]}), "application/json")
            except Exception as e:
                self._send(json.dumps({"error": str(e)[:160]}), "application/json", 400)
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
                m = str(e)
                if "password" in m.lower() or "auth" in m.lower() or "login" in m.lower():
                    m = "Login abgelehnt — E-Mail/Passwort/Land prüfen"
                self._send(json.dumps({"ok": False, "error": m[:160]}), "application/json")
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
                self._send(json.dumps({"ok": False, "error": str(e)[:140]}), "application/json")
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
        elif u.path == "/save":
            try:
                c = json.loads(raw)
                if not c.get("vin"):
                    raise ValueError("VIN fehlt")
                # Passwortfeld leer gelassen -> gespeichertes Passwort behalten
                if not c.get("password") and _CFG.get("password"):
                    c["password"] = _CFG["password"]
                if not c.get("control_pin") and _CFG.get("control_pin"):
                    c["control_pin"] = _CFG["control_pin"]
                if not c.get("ha_pass") and _CFG.get("ha_pass"):
                    c["ha_pass"] = _CFG["ha_pass"]
                if not c.get("pv_token") and _CFG.get("pv_token"):
                    c["pv_token"] = _CFG["pv_token"]
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
                    c.pop("install_id", None)      # Haekchen weg -> ID weg
                save_cfg(c)
                load_cfg()
                _STATE.clear()
                threading.Thread(target=ping_optin, daemon=True).start()
                self._send(json.dumps({"ok": True}), "application/json")
            except Exception as e:
                self._send(json.dumps({"ok": False, "error": str(e)[:160]}), "application/json")
        elif u.path == "/cmd":
            a = (urllib.parse.parse_qs(u.query).get("a") or [""])[0]
            if a in ("heat", "cool", "off", "batt_on", "batt_off", "find", "lock",
                     "seat_off", "seat_lo", "seat_hi", "vent_off", "vent_lo", "vent_hi"):
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
