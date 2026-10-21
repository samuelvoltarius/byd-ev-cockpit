"""Home Assistant von selbst finden und ohne Token-Abtippen verbinden (Alfred, 21.10.2026; Regel 1: fuer alle).

1) Suche im eigenen Netz: mDNS `_home-assistant._tcp.local` (so meldet sich HA selbst an), dazu
   homeassistant.local:8123 und schon bekannte Adressen. Erkannt wird HA an GET /auth/providers (ohne Login lesbar).
2) Anmelden mit HAs eingebautem OAuth2 (IndieAuth): client_id = Adresse dieses Cockpits, Redirect zurueck ans
   lokale Cockpit. HA erlaubt das fuer localhost/lokale Adressen ohne Registrierung. Der Refresh-Token wird
   wie alle Geheimnisse per DPAPI/Schluesselbund gespeichert (geheim.FELDER).
3) Sensor-Vorschlaege nur lesend: device_class power/energy bzw. Einheit W/kW, Name mit pv/solar zuerst.
Nichts davon verlaesst das eigene Netz bzw. den eigenen HA-Server.
"""
import json
import random
import re
import socket
import struct
import time
import urllib.error
import urllib.parse
import urllib.request

MDNS = ("224.0.0.251", 5353)
DIENST = "_home-assistant._tcp.local"
UA = "ev-cockpit"


# ---------------------------------------------------------------- mDNS (nur Standardbibliothek)
def _name(daten, i):
    """DNS-Name lesen (mit Komprimierung). -> (name, naechste Position)"""
    teile, sprung, ende = [], False, i
    for _ in range(64):
        n = daten[i]
        if n == 0:
            i += 1
            break
        if n & 0xC0 == 0xC0:
            if not sprung:
                ende = i + 2
            i = ((n & 0x3F) << 8) | daten[i + 1]
            sprung = True
            continue
        teile.append(daten[i + 1:i + 1 + n].decode("utf-8", "replace"))
        i += 1 + n
    return ".".join(teile), (ende if sprung else i)


def _frage(name, typ=12):
    kopf = struct.pack(">HHHHHH", 0, 0, 1, 0, 0, 0)
    q = b"".join(bytes([len(t)]) + t.encode() for t in name.split(".")) + b"\0"
    return kopf + q + struct.pack(">HH", typ, 1)


def lies_antwort(daten):
    """mDNS-Antwort -> Liste von (name, typ, wert). PTR/SRV/TXT/A werden ausgewertet."""
    out = []
    try:
        _, _, qd, an, ns, ar = struct.unpack(">HHHHHH", daten[:12])
        i = 12
        for _ in range(qd):
            _, i = _name(daten, i)
            i += 4
        for _ in range(an + ns + ar):
            name, i = _name(daten, i)
            typ, _, _, laenge = struct.unpack(">HHIH", daten[i:i + 10])
            i += 10
            roh = daten[i:i + laenge]
            if typ == 12:
                out.append((name, "PTR", _name(daten, i)[0]))
            elif typ == 33:
                _, _, port = struct.unpack(">HHH", roh[:6])
                out.append((name, "SRV", (port, _name(daten, i + 6)[0])))
            elif typ == 16:
                txt, j = {}, 0
                while j < len(roh):
                    n = roh[j]
                    t = roh[j + 1:j + 1 + n].decode("utf-8", "replace")
                    if "=" in t:
                        k, v = t.split("=", 1)
                        txt[k] = v
                    j += 1 + n
                out.append((name, "TXT", txt))
            elif typ == 1 and laenge == 4:
                out.append((name, "A", socket.inet_ntoa(roh)))
            i += laenge
    except Exception:
        pass
    return out


def _schnittstellen():
    """Lokale IPv4-Adressen (LAN, VPN, VM-Netze). Die Frage geht ueber jede raus: sonst landet sie oft im falschen
    Netz (z. B. Tailscale oder VirtualBox), und HA im Heimnetz hoert sie nie."""
    try:
        ips = {a[4][0] for a in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)}
    except Exception:
        ips = set()
    return sorted(ip for ip in ips if not ip.startswith(("127.", "169.254.")))


def mdns_suchen(dauer=2.0):
    """Fragt einmal (je Netzwerkschnittstelle) nach Home Assistant im lokalen Netz. -> [{name, url, version}]"""
    import select
    socks = []
    for ip in _schnittstellen() or [""]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
            if ip:
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))
            s.bind((ip, 0))
            s.sendto(_frage(DIENST), MDNS)
            socks.append(s)
        except OSError:
            continue
    recs, ende = [], time.time() + dauer
    try:
        while socks and time.time() < ende:
            bereit, _, _ = select.select(socks, [], [], max(0.0, min(0.3, ende - time.time())))
            for s in bereit:
                try:
                    recs += lies_antwort(s.recvfrom(9000)[0])
                except OSError:
                    pass
    finally:
        for s in socks:
            s.close()
    return aus_records(recs)


def aus_records(recs):
    instanzen = {v for n, t, v in recs if t == "PTR" and n.lower() == DIENST}
    a = {n.lower(): v for n, t, v in recs if t == "A"}
    gefunden = []
    for inst in instanzen:
        txt = next((v for n, t, v in recs if t == "TXT" and n == inst), {})
        srv = next((v for n, t, v in recs if t == "SRV" and n == inst), None)
        url = txt.get("internal_url") or txt.get("base_url") or ""
        if not url and srv:
            host = a.get(srv[1].lower()) or srv[1].rstrip(".")
            url = "http://%s:%d" % (host, srv[0])
        if url:
            gefunden.append({"name": txt.get("location_name") or inst.split(".")[0], "url": url.rstrip("/"),
                             "version": txt.get("version") or "", "quelle": "mDNS"})
    return gefunden


# ---------------------------------------------------------------- Probe + Suche
def ist_ha(url, timeout=2.5):
    """True, wenn unter url ein Home Assistant antwortet (/auth/providers ist ohne Login lesbar)."""
    try:
        req = urllib.request.Request(url.rstrip("/") + "/auth/providers", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode("utf-8") or "null")
        return isinstance(d, (list, dict))
    except Exception:
        return False


def normal(url):
    url = (url or "").strip().rstrip("/")
    if url and not re.match(r"^https?://", url):
        url = "http://" + url
    if url and not re.search(r":\d+$", urllib.parse.urlsplit(url).netloc) and url.startswith("http://"):
        url += ":8123"
    return url


def suchen(bekannte=(), mdns=mdns_suchen, probe=ist_ha):
    """Alle Wege nacheinander; doppelte Adressen nur einmal. -> {gefunden:[...], geprueft:[...]}"""
    gefunden, gesehen = [], set()
    try:
        for g in mdns():
            if g["url"] not in gesehen:
                gesehen.add(g["url"])
                gefunden.append(g)
    except Exception:
        pass
    kandidaten = ["http://homeassistant.local:8123"] + [normal(b) for b in bekannte if b]
    geprueft = []
    for u in kandidaten:
        if not u or u in gesehen:
            continue
        gesehen.add(u)
        geprueft.append(u)
        if probe(u):
            gefunden.append({"name": urllib.parse.urlsplit(u).hostname or u, "url": u, "version": "", "quelle": "Probe"})
    return {"gefunden": gefunden, "geprueft": geprueft}


# ---------------------------------------------------------------- OAuth2 (HA IndieAuth)
def anmelde_url(ha, client_id, redirect, state):
    return ha.rstrip("/") + "/auth/authorize?" + urllib.parse.urlencode(
        {"response_type": "code", "client_id": client_id, "redirect_uri": redirect, "state": state})


def neuer_state():
    return "%032x" % random.SystemRandom().getrandbits(128)


def _token(ha, felder, timeout=10):
    req = urllib.request.Request(ha.rstrip("/") + "/auth/token", data=urllib.parse.urlencode(felder).encode(),
                                 headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def code_tauschen(ha, code, client_id, token=_token):
    d = token(ha, {"grant_type": "authorization_code", "code": code, "client_id": client_id})
    if not d.get("refresh_token") or not d.get("access_token"):
        raise ValueError("Home Assistant hat keine Anmeldung zurückgegeben")
    return d


class Zugang:
    """Kurzlebiger Access-Token aus dem gespeicherten Refresh-Token (HA: 30 min gueltig)."""
    def __init__(self, token=_token, uhr=time.time):
        self.token, self.uhr, self.cache = token, uhr, {}

    def access(self, ha, refresh, client_id):
        k = (ha, refresh)
        t, bis = self.cache.get(k, ("", 0))
        if t and self.uhr() < bis - 60:
            return t
        d = self.token(ha, {"grant_type": "refresh_token", "refresh_token": refresh, "client_id": client_id})
        if not d.get("access_token"):
            raise ValueError("Anmeldung bei Home Assistant abgelaufen – bitte neu anmelden")
        self.cache[k] = (d["access_token"], self.uhr() + int(d.get("expires_in") or 1800))
        return d["access_token"]


# ---------------------------------------------------------------- Sensor-Vorschlag
PV_WORT = re.compile(r"pv|solar|photovolt|wechselrichter|inverter|fronius|sma|huawei|growatt|enphase|hoymiles|kostal", re.I)


def sensoren_vorschlagen(states):
    """Nur Leistungs- bzw. Energiesensoren; PV-artige zuerst, Leistung (W/kW) vor Energie (kWh)."""
    out = []
    for e in states or []:
        a = e.get("attributes") or {}
        eid, unit, dc = e.get("entity_id") or "", a.get("unit_of_measurement") or "", a.get("device_class") or ""
        if not eid.startswith("sensor."):
            continue
        leistung = dc == "power" or unit in ("W", "kW")
        energie = dc == "energy" or unit in ("Wh", "kWh")
        if not (leistung or energie):
            continue
        name = a.get("friendly_name") or eid
        pv = bool(PV_WORT.search(eid) or PV_WORT.search(name))
        out.append({"id": eid, "name": name, "state": e.get("state"), "unit": unit, "art": "leistung" if leistung else "energie",
                    "pv": pv, "rang": (0 if pv else 2) + (0 if leistung else 1)})
    out.sort(key=lambda x: (x["rang"], x["name"].lower()))
    return out
