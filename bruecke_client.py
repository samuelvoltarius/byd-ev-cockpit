# -*- coding: utf-8 -*-
"""1.22: Das Cockpit erreicht Panoptes UEBER DIE BRUECKE (ns1) - ohne Tailscale. Vertrag: BRUECKE_VERTRAG.md + BRUECKE_STAND_0120.md (Kern 10).
Der Server sieht nur Chiffretext (Noise IK, noise_rein.py); innen laufen dieselben HTTP-Aufrufe wie im Direktweg.

  Bruecke   eine verschluesselte Sitzung (WebSocket + Noise): anfrage(methode, pfad, header, body) -> {s, h, b}
  Weg       waehlt je Aufruf: erst direkt (Tailnet/LAN, kurze Zeit), sonst die Bruecke; merkt sich den aktiven Weg.
Festlegungen laut Kern 10 (nicht abwandeln): base64url ohne "=", Prolog "panoptes-bruecke/1", Rahmen Handy->Server: erst Text
{"t":"hallo","p":P,"z":G_handy}, danach NUR Binaer (Noise-Nachricht ohne k-Byte); innen je Noise-Nachricht [Flag][Daten], Flag 1 = letztes
Stueck, <= 60 KiB; Anfrage {"id","m","p","h","b"[,"b64"]}, Antwort {"id","s","h","b"[,"b64"]}."""
import base64
import io
import json
import re
import threading
import time
import urllib.error

import noise_rein as nr
import ws_klein

STUECK = 60 * 1024
B64U = re.compile(r"^[A-Za-z0-9_-]{43}$")
DURCHGEREICHT = ("authorization", "content-type", "accept", "accept-language", "if-none-match")

# Gruende, die der Nutzer lesen darf (Regel DAU: sagen, was zu tun ist)
GRUND_TEXT = {
    "auto_offline": "Das Auto ist gerade nicht erreichbar – vielleicht kein Empfang. Später noch einmal.",
    "limit": "Gerade zu viele Anfragen. Bitte kurz warten.",
    "entkoppelt": "Dieses Cockpit ist beim Auto nicht mehr gekoppelt. Bitte neu koppeln.",
    "jwt": "Die Erlaubnis zum Steuern ist abgelaufen. Bitte einmal neu erlauben.",
    "zugang": "Die Verbindung über das Internet gilt nicht mehr. Bitte noch einmal mit Panoptes verbinden.",
    "geloescht": "Die Verbindung über das Internet wurde in Panoptes ausgeschaltet. Bitte noch einmal verbinden.",
    "netz": "Das Internet-Netz zum Auto ist gerade nicht erreichbar.",
    "handshake": "Die sichere Verbindung zum Auto kam nicht zustande. Bitte noch einmal mit Panoptes verbinden.",
    "zeit": "Das Auto antwortet gerade nicht.",
    "format": "Das Auto hat unerwartet geantwortet. Bitte noch einmal versuchen.",
}


class BrueckeFehler(Exception):
    def __init__(self, grund, detail=""):
        super().__init__(GRUND_TEXT.get(grund, grund) + ((" (" + detail + ")") if detail else ""))
        self.grund, self.detail = grund, detail


def b64u(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def b64u_ent(t):
    t = str(t or "")
    if not B64U.match(t):
        raise BrueckeFehler("format", "Schlüssel")
    return base64.urlsafe_b64decode(t + "=")


def ws_url(server):
    """https://byd.serveone.at/bruecke -> wss://byd.serveone.at/bruecke/v1/handy (nur https; http nur an 127.0.0.1 zum Testen)."""
    s = (server or "").strip().rstrip("/")
    if s.startswith("https://"):
        return "wss://" + s[8:] + "/v1/handy"
    if s.startswith("http://127.0.0.1") or s.startswith("http://localhost"):
        return "ws://" + s[7:] + "/v1/handy"
    raise BrueckeFehler("format", "Server-Adresse")


def neue_schluessel(zufall=None):
    """Zugang fuer dieses Cockpit: Handy-Schluessel H (X25519) und Handy-Zugang G_handy (32 Byte Zufall), alles base64url."""
    import os
    z = zufall or os.urandom
    priv, pub = nr.schluesselpaar(z)
    return {"h_priv": b64u(priv), "h_pub": b64u(pub), "g_handy": b64u(z(32))}


class Bruecke:
    """Eine Sitzung zum Auto. cfg: server, p, a_pub, g_handy, h_priv, h_pub (alles base64url). Thread-sicher (eine Anfrage zur Zeit)."""

    def __init__(self, cfg, ws_klasse=ws_klein.WsKlein, zufall=None, uhr=time.time, leerlauf_s=120.0):
        import os
        self.cfg = cfg
        self.ws_klasse, self.zufall, self.uhr, self.leerlauf = ws_klasse, zufall or os.urandom, uhr, leerlauf_s
        self.ws, self.senden, self.empfang = None, None, None
        self.lock = threading.RLock()
        self.zuletzt = 0.0
        self.naechste_id = 1

    # ------------------------------------------------------------ Aufbau
    def _zu(self):
        w, self.ws, self.senden, self.empfang = self.ws, None, None, None
        if w:
            try:
                w.schliessen()
            except Exception:
                pass

    def schliessen(self):
        with self.lock:
            self._zu()

    def _verbinden(self, timeout):
        c = self.cfg
        p, a_pub = b64u_ent(c.get("p")), b64u_ent(c.get("a_pub"))
        h_priv, h_pub, g = b64u_ent(c.get("h_priv")), b64u_ent(c.get("h_pub")), b64u_ent(c.get("g_handy"))
        ws = self.ws_klasse(ws_url(c.get("server")), timeout=timeout, zufall=self.zufall)
        try:
            ws.verbinden()
        except (OSError, ws_klein.WsFehler) as e:
            raise BrueckeFehler("netz", type(e).__name__)
        self.ws = ws
        try:
            ws.senden_text(json.dumps({"t": "hallo", "p": b64u(p), "z": b64u(g)}, separators=(",", ":")))
            hs = nr.HandshakeIK(True, (h_priv, h_pub), rs=a_pub, zufall=self.zufall)
            ws.senden_bin(hs.nachricht1())
            try:
                art, d = self._lies_bruecke(ws)
            except BrueckeFehler as e:
                if e.grund in ("netz", "zeit"):
                    raise BrueckeFehler("entkoppelt")     # Server nahm uns an, das Auto antwortet nicht: es kennt diesen Schluessel nicht mehr
                raise
            if art != "bin":
                raise BrueckeFehler("handshake")
            hs.lese2(d)
            self.senden, self.empfang = hs.teilen()
        except nr.NoiseFehler:
            self._zu()
            raise BrueckeFehler("handshake")
        except BrueckeFehler:
            self._zu()
            raise

    def _lies_bruecke(self, ws):
        """Naechste Nachricht; Text-Steuerrahmen und Close-Codes des Servers werden zu klaren Gruenden."""
        while True:
            try:
                art, d = ws.empfangen()
            except ws_klein.WsZu as z:
                self._zu()
                raise BrueckeFehler({4401: "zugang", 4410: "geloescht", 4429: "limit", 4400: "format"}.get(z.code, "netz"), str(z.code or ""))
            except TimeoutError:
                self._zu()
                raise BrueckeFehler("zeit")
            except OSError as e:
                self._zu()
                raise BrueckeFehler("zeit" if "timed out" in str(e) else "netz", type(e).__name__)
            except ws_klein.WsFehler as e:
                self._zu()
                raise BrueckeFehler("format", str(e)[:40])
            if art == "text":
                try:
                    t = json.loads(d).get("t")
                except Exception:
                    t = None
                if t in ("auto_offline", "limit"):
                    self._zu()
                    raise BrueckeFehler(t)
                if t == "zu":
                    self._zu()
                    raise BrueckeFehler("handshake")
                continue
            return art, d

    # ------------------------------------------------------------ Anfrage
    def _gestueckelt_senden(self, roh):
        n = len(roh)
        teile = [roh[i:i + STUECK] for i in range(0, max(n, 1), STUECK)] or [b""]
        for i, t in enumerate(teile):
            letzt = b"\x01" if i == len(teile) - 1 else b"\x00"
            self.ws.senden_bin(self.senden.verschluesseln(b"", letzt + t))

    def _antwort_lesen(self, aid, frist):
        while True:
            roh = b""
            while True:
                self.ws.zeitlimit(max(0.5, frist - self.uhr()))
                art, d = self._lies_bruecke(self.ws)
                try:
                    k = self.empfang.entschluesseln(b"", d)
                except nr.NoiseFehler:
                    self._zu()
                    raise BrueckeFehler("handshake")
                if not k:
                    self._zu()
                    raise BrueckeFehler("format")
                roh += k[1:]
                if k[0] == 1:
                    break
                if len(roh) > 8 * 1024 * 1024:
                    self._zu()
                    raise BrueckeFehler("format", "zu gross")
            try:
                a = json.loads(roh.decode("utf-8"))
            except Exception:
                self._zu()
                raise BrueckeFehler("format")
            if isinstance(a, dict) and a.get("id") == aid:
                return a                      # Antworten auf frueher abgebrochene Anfragen werden uebersprungen

    def anfrage(self, methode, pfad, header=None, body=None, timeout=15.0):
        """-> {"s": Status, "h": {Kopfzeilen klein}, "b": bytes}. BrueckeFehler bei allem, was nicht Antwort des Autos ist."""
        with self.lock:
            if self.ws is not None and self.uhr() - self.zuletzt > self.leerlauf:
                self._zu()
            frist = self.uhr() + timeout
            neu = self.ws is None
            if neu:
                self._verbinden(min(timeout, 10.0))
            req = {"id": self.naechste_id, "m": methode, "p": pfad,
                   "h": {k: v for k, v in (header or {}).items() if k.lower() in DURCHGEREICHT}}
            self.naechste_id += 1
            if body:
                try:
                    req["b"] = body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else str(body)
                except UnicodeDecodeError:
                    req["b"], req["b64"] = base64.b64encode(body).decode(), True
            try:
                self._gestueckelt_senden(json.dumps(req, separators=(",", ":")).encode("utf-8"))
                a = self._antwort_lesen(req["id"], frist)
            except (ws_klein.WsFehler, OSError):
                self._zu()
                if neu:
                    raise BrueckeFehler("netz")
                return self.anfrage(methode, pfad, header, body, max(2.0, frist - self.uhr()))    # alte Sitzung war weg: einmal neu
            except BrueckeFehler as e:
                if neu or e.grund not in ("netz", "zeit"):
                    raise
                return self.anfrage(methode, pfad, header, body, max(2.0, frist - self.uhr()))
            self.zuletzt = self.uhr()
            b = a.get("b") or ""
            b = base64.b64decode(b) if a.get("b64") else (b.encode("utf-8") if isinstance(b, str) else b"")
            return {"s": int(a.get("s") or 0), "h": {str(k).lower(): v for k, v in (a.get("h") or {}).items()}, "b": b}


# ------------------------------------------------------------ Weg: direkt oder Bruecke
class Weg:
    """Wahl des Wegs zu EINEM Panoptes (basis = dessen Direkt-Adresse, z. B. http://100.x.x.x:8180). Erst direkt (kurz), dann Bruecke.
    Scheitert der Direktweg, wird er erst nach `pause_s` wieder versucht. aktiv: "direkt" | "bruecke" | "" (noch nichts)."""

    def __init__(self, basis, bruecke, direkt_http, direkt_roh, uhr=time.time, pause_s=60.0, direkt_timeout=2.5, jwt_bruecke=None):
        self.jwt_bruecke = jwt_bruecke            # Ueber die Bruecke gilt NUR der Zugang (JWT) der Handy-Kopplung, die den Handshake gemacht hat
        self.basis = (basis or "").rstrip("/")
        self.bruecke, self.direkt_http, self.direkt_roh, self.uhr = bruecke, direkt_http, direkt_roh, uhr
        self.pause_s, self.direkt_timeout = pause_s, direkt_timeout
        self.aktiv, self.direkt_wieder, self.letzter_fehler = "", 0.0, ""

    def gehoert(self, url):
        return bool(self.basis) and (url == self.basis or url.startswith(self.basis + "/"))

    def _pfad(self, url):
        return url[len(self.basis):] or "/"

    def _direkt_moeglich(self):
        return self.uhr() >= self.direkt_wieder

    def _ueber_bruecke(self, url, daten, jwt, timeout):
        if self.bruecke is None:
            raise urllib.error.URLError("kein Weg")
        kopf = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.jwt_bruecke is not None:
            jwt = self.jwt_bruecke() or ""
        if jwt:
            kopf["Authorization"] = "Bearer " + jwt
        try:
            r = self.bruecke.anfrage("POST" if daten is not None else "GET", self._pfad(url), kopf,
                                     json.dumps(daten).encode() if daten is not None else None, timeout)
        except BrueckeFehler as e:
            self.letzter_fehler = e.grund
            raise urllib.error.URLError(str(e))
        self.aktiv, self.letzter_fehler = "bruecke", ("jwt" if r["s"] == 401 else "")      # 401 innen: der Handy-Zugang ist abgelaufen
        try:
            return r["s"], json.loads(r["b"].decode("utf-8") or "{}")
        except Exception:
            return r["s"], {}

    def _kurz(self, timeout):
        return min(timeout, self.direkt_timeout) if self.bruecke is not None else timeout

    # -- (Status, JSON) wie panoptes_source._roh
    def roh(self, url, daten=None, timeout=15.0, jwt=""):
        if self._direkt_moeglich():
            try:
                r = self.direkt_roh(url, daten, timeout=self._kurz(timeout), jwt=jwt)
                self.aktiv, self.letzter_fehler = "direkt", ""
                return r
            except OSError:
                if self.bruecke is None:
                    raise
                self.direkt_wieder = self.uhr() + self.pause_s
        return self._ueber_bruecke(url, daten, jwt, timeout)

    # -- JSON-Antwort wie panoptes_source._http (401 -> NichtAngemeldet, 403/409 -> Antwort mit _status, sonst HTTPError)
    def http(self, url, daten=None, jwt="", timeout=15.0, methode=None):
        if self._direkt_moeglich():
            try:
                r = self.direkt_http(url, daten, jwt=jwt, timeout=self._kurz(timeout), methode=methode)
                self.aktiv, self.letzter_fehler = "direkt", ""
                return r
            except urllib.error.HTTPError:
                self.aktiv = "direkt"            # das Auto hat geantwortet (z. B. 404) - der Weg ist in Ordnung
                raise
            except OSError as e:
                if e.__class__.__name__ == "NichtAngemeldet" or self.bruecke is None:
                    raise
                self.direkt_wieder = self.uhr() + self.pause_s
        code, d = self._ueber_bruecke(url, daten, jwt, timeout)
        if code == 401:
            from panoptes_source import NichtAngemeldet
            raise NichtAngemeldet()
        if code in (403, 409):
            d = d if isinstance(d, dict) else {}
            d["_status"] = code
            return d
        if code >= 400:
            raise urllib.error.HTTPError(url, code, "Brücke", {}, io.BytesIO(json.dumps(d).encode()))
        return d if isinstance(d, dict) else {}
