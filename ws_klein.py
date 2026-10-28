# -*- coding: utf-8 -*-
"""1.22: kleiner WebSocket-Client (RFC 6455), nur Standardbibliothek, fuer die Panoptes-Bruecke (wss://byd.serveone.at/bruecke/v1/handy).
Client-Rahmen sind maskiert; Text/Binaer, Ping/Pong, Close; zerstueckelte Nachrichten werden zusammengesetzt. TLS wird geprueft."""
import base64
import hashlib
import os
import socket
import ssl
import struct
import urllib.parse

GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
OP_FORT, OP_TEXT, OP_BIN, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA
MAX_NACHRICHT = 1 << 20


class WsFehler(Exception):
    pass


class WsZu(WsFehler):
    """Gegenstelle hat geschlossen (oder die Verbindung ist weg). code = Close-Code oder None."""

    def __init__(self, code=None, grund=""):
        super().__init__("Verbindung zu (%s %s)" % (code, grund))
        self.code, self.grund = code, grund


class WsKlein:
    def __init__(self, url, timeout=10.0, ssl_kontext=None, zufall=os.urandom):
        self.url, self.timeout, self.ctx, self.zufall = url, timeout, ssl_kontext, zufall
        self.s = None
        self.puffer = b""
        self.offen = False

    # ------------------------------------------------------------ Aufbau
    def verbinden(self):
        u = urllib.parse.urlsplit(self.url)
        if u.scheme not in ("ws", "wss"):
            raise WsFehler("nur ws:// oder wss://")
        host, port = u.hostname, u.port or (443 if u.scheme == "wss" else 80)
        roh = socket.create_connection((host, port), self.timeout)
        try:
            if u.scheme == "wss":
                ctx = self.ctx or ssl.create_default_context()
                roh = ctx.wrap_socket(roh, server_hostname=host)
            roh.settimeout(self.timeout)
            key = base64.b64encode(self.zufall(16)).decode()
            pfad = (u.path or "/") + (("?" + u.query) if u.query else "")
            kopf = ("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                    "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\nUser-Agent: ev-cockpit\r\n\r\n"
                    % (pfad, u.netloc, key)).encode("ascii")
            roh.sendall(kopf)
            antwort = b""
            while b"\r\n\r\n" not in antwort:
                d = roh.recv(4096)
                if not d:
                    raise WsFehler("Server hat die Verbindung beendet")
                antwort += d
                if len(antwort) > 16384:
                    raise WsFehler("Antwortkopf zu gross")
            kopf_b, _, rest = antwort.partition(b"\r\n\r\n")
            zeilen = kopf_b.decode("latin-1").split("\r\n")
            if " 101 " not in zeilen[0] + " ":
                raise WsFehler("kein Upgrade: " + zeilen[0][:60])
            hs = {z.split(":", 1)[0].strip().lower(): z.split(":", 1)[1].strip() for z in zeilen[1:] if ":" in z}
            erwartet = base64.b64encode(hashlib.sha1(key.encode() + GUID).digest()).decode()
            if hs.get("sec-websocket-accept") != erwartet:
                raise WsFehler("Sec-WebSocket-Accept falsch")
            self.s, self.puffer, self.offen = roh, rest, True
        except Exception:
            try:
                roh.close()
            except Exception:
                pass
            raise
        return self

    # ------------------------------------------------------------ Senden
    def _rahmen(self, op, daten=b""):
        n = len(daten)
        kopf = bytes([0x80 | op])
        if n < 126:
            kopf += bytes([0x80 | n])
        elif n < 65536:
            kopf += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            kopf += bytes([0x80 | 127]) + struct.pack(">Q", n)
        m = self.zufall(4)
        mask = (m * (n // 4 + 1))[:n]
        return kopf + m + bytes(a ^ b for a, b in zip(daten, mask))

    def _senden(self, op, daten=b""):
        if not self.offen:
            raise WsZu(None, "nicht offen")
        try:
            self.s.sendall(self._rahmen(op, daten))
        except OSError as e:
            self.offen = False
            raise WsZu(None, str(e))

    def senden_text(self, text):
        self._senden(OP_TEXT, text.encode("utf-8"))

    def senden_bin(self, daten):
        self._senden(OP_BIN, bytes(daten))

    def ping(self):
        self._senden(OP_PING, b"")

    # ------------------------------------------------------------ Empfangen
    def _exakt(self, n):
        while len(self.puffer) < n:
            try:
                d = self.s.recv(65536)
            except socket.timeout:
                raise
            except OSError as e:
                self.offen = False
                raise WsZu(None, str(e))
            if not d:
                self.offen = False
                raise WsZu(None, "Verbindung beendet")
            self.puffer += d
        r, self.puffer = self.puffer[:n], self.puffer[n:]
        return r

    def _lies_rahmen(self):
        b0, b1 = self._exakt(2)
        fin, op, maskiert, n = bool(b0 & 0x80), b0 & 0x0F, bool(b1 & 0x80), b1 & 0x7F
        if b0 & 0x70:
            raise WsFehler("RSV-Bits gesetzt")
        if n == 126:
            n = struct.unpack(">H", self._exakt(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", self._exakt(8))[0]
        if n > MAX_NACHRICHT:
            raise WsFehler("Rahmen zu gross")
        mask = self._exakt(4) if maskiert else b""
        d = self._exakt(n)
        if maskiert:
            d = bytes(a ^ b for a, b in zip(d, (mask * (n // 4 + 1))[:n]))
        return fin, op, d

    def empfangen(self):
        """-> ("text", str) | ("bin", bytes). Ping wird beantwortet, Close wirft WsZu(code). socket.timeout wird durchgereicht."""
        teile, art = b"", None
        while True:
            fin, op, d = self._lies_rahmen()
            if op == OP_PING:
                self._senden(OP_PONG, d)
                continue
            if op == OP_PONG:
                continue
            if op == OP_CLOSE:
                code = struct.unpack(">H", d[:2])[0] if len(d) >= 2 else None
                grund = d[2:].decode("utf-8", "replace") if len(d) > 2 else ""
                try:
                    if self.offen:
                        self.s.sendall(self._rahmen(OP_CLOSE, d[:2]))
                except OSError:
                    pass
                self.offen = False
                raise WsZu(code, grund)
            if op in (OP_TEXT, OP_BIN):
                art, teile = op, d
            elif op == OP_FORT and art is not None:
                teile += d
            else:
                raise WsFehler("unerwarteter Rahmen")
            if len(teile) > MAX_NACHRICHT:
                raise WsFehler("Nachricht zu gross")
            if fin:
                if art == OP_TEXT:
                    return "text", teile.decode("utf-8")
                return "bin", teile

    def zeitlimit(self, sek):
        if self.s:
            self.s.settimeout(sek)

    def schliessen(self, code=1000):
        try:
            if self.offen and self.s:
                self.s.sendall(self._rahmen(OP_CLOSE, struct.pack(">H", code)))
        except OSError:
            pass
        self.offen = False
        try:
            if self.s:
                self.s.close()
        except OSError:
            pass
