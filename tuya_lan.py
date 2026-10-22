"""Tuya-Geraet im Heimnetz (TCP 6668), Protokoll 3.3 / 3.4 / 3.5 (WALLBOX_VERTRAG §4b).

Eigene Umsetzung nach Protokollbeschreibung (wie Kern 6s TuyaProtokoll/TuyaLan in Panoptes); tinytuya (MIT) dient nur
als Testorakel ausserhalb des Produkts. Je Vorgang eine kurze Verbindung: verbinden -> (ab 3.4) Schluessel aushandeln
-> abfragen bzw. setzen -> schliessen. Der local_key verlaesst den Rechner nie (er verschluesselt nur). Zeitlimit 4 s.

  55AA (3.3/3.4): 000055AA | seq | cmd | len | [retcode] daten | CRC32 (3.3) bzw. HMAC-SHA256 (3.4) | 0000AA55
  6699 (3.5):     00006699 | 0000 | seq | cmd | len | IV(12) | AES-GCM(klar) | Tag(16) | 00009966
"""
import binascii
import hashlib
import hmac
import json
import os
import socket
import struct
import time

import aes_rein

PORT = 6668
ZEIT_S = 4.0
MAX_LAENGE = 64 * 1024
VERSIONEN = ("3.3", "3.4", "3.5")

SESS_START, SESS_ANTWORT, SESS_ENDE = 0x03, 0x04, 0x05
CONTROL, STATUS, DP_QUERY, CONTROL_NEW, DP_QUERY_NEW = 0x07, 0x08, 0x0A, 0x0D, 0x10


class TuyaFehler(Exception):
    """code: tuya_keine_antwort | tuya_schluessel | tuya_schluessel_fehlt | tuya_pruefsumme | tuya_antwort_ungueltig |
    tuya_variante | tuya_abgelehnt | tuya_version | nicht_erreichbar"""
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _hmac(k, d):
    return hmac.new(k, d, hashlib.sha256).digest()


def rahmen_55aa(seq, cmd, daten, hmac_schluessel=None):
    pruef = 4 if hmac_schluessel is None else 32
    kopf = struct.pack(">IIII", 0x55AA, seq, cmd, len(daten) + pruef + 4) + daten
    p = struct.pack(">I", binascii.crc32(kopf) & 0xFFFFFFFF) if hmac_schluessel is None else _hmac(hmac_schluessel, kopf)
    return kopf + p + struct.pack(">I", 0xAA55)


def _mit_retcode(seq, cmd, d):
    if len(d) >= 4 and d[0] == 0 and d[1] == 0 and d[2] == 0:
        return seq, cmd, struct.unpack(">I", d[:4])[0], d[4:]
    return seq, cmd, -1, d


def lies_55aa(f, hmac_schluessel=None):
    pruef = 4 if hmac_schluessel is None else 32
    if len(f) < 16 + pruef + 4:
        raise TuyaFehler("tuya_antwort_ungueltig")
    pre, seq, cmd, ln = struct.unpack(">IIII", f[:16])
    if pre != 0x55AA or struct.unpack(">I", f[-4:])[0] != 0xAA55 or ln != len(f) - 16:
        raise TuyaFehler("tuya_antwort_ungueltig")
    ende = len(f) - 4 - pruef
    ist = f[ende:ende + pruef]
    if hmac_schluessel is None:
        if struct.pack(">I", binascii.crc32(f[:ende]) & 0xFFFFFFFF) != ist:
            raise TuyaFehler("tuya_pruefsumme")
    elif not hmac.compare_digest(_hmac(hmac_schluessel, f[:ende]), ist):
        raise TuyaFehler("tuya_schluessel")
    return _mit_retcode(seq, cmd, f[16:ende])


def rahmen_6699(seq, cmd, klar, schluessel, iv):
    kopf = struct.pack(">IHIII", 0x6699, 0, seq, cmd, 12 + len(klar) + 16)
    return kopf + iv + aes_rein.gcm_ver(schluessel, iv, klar, kopf[4:]) + struct.pack(">I", 0x9966)


def lies_6699(f, schluessel):
    if len(f) < 18 + 12 + 16 + 4:
        raise TuyaFehler("tuya_antwort_ungueltig")
    pre, _, seq, cmd, ln = struct.unpack(">IHIII", f[:18])
    if pre != 0x6699 or struct.unpack(">I", f[-4:])[0] != 0x9966 or ln != len(f) - 22:
        raise TuyaFehler("tuya_antwort_ungueltig")
    try:
        klar = aes_rein.gcm_ent(schluessel, f[18:30], f[30:-4], f[4:18])
    except ValueError:
        raise TuyaFehler("tuya_schluessel")
    return _mit_retcode(seq, cmd, klar)


def versions_kopf(v):
    return v.encode("ascii") + bytes(12)


def ohne_versions_kopf(d):
    if len(d) >= 15 and d[:2] == b"3." and 48 <= d[2] <= 57:
        return d[15:]
    return d


def sitzungs_schluessel(version, local_key, lokal, fern):
    x = bytes(a ^ b for a, b in zip(lokal[:16], fern[:16]))
    if version == "3.4":
        return aes_rein.ecb_ver(local_key, x, auffuellen=False)
    return aes_rein.gcm_ver(local_key, lokal[:12], x)[:16]


def dps_aus(text):
    try:
        j = json.loads(text)
    except Exception:
        return None
    if not isinstance(j, dict):
        return None
    d = j.get("dps")
    if d is None and isinstance(j.get("data"), dict):
        d = j["data"].get("dps")
    return d if isinstance(d, dict) else None


def _tcp(ip, port):
    try:
        s = socket.create_connection((ip, port), timeout=ZEIT_S)
    except OSError:
        raise TuyaFehler("nicht_erreichbar")
    s.settimeout(ZEIT_S)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return s


class TuyaLan:
    """ip = bereits gepruefte private Adresse (network_safety.private_ziel)."""

    def __init__(self, ip, geraete_id, local_key, version, port=PORT, verbinde=_tcp):
        if not isinstance(local_key, (bytes, bytearray)) or len(local_key) != 16:
            raise TuyaFehler("tuya_schluessel_fehlt")
        if version not in VERSIONEN:
            raise TuyaFehler("tuya_version")
        self.ip, self.id, self.key, self.version, self.port, self.verbinde = ip, str(geraete_id), bytes(local_key), version, port, verbinde

    # ---------------------------------------------------------------- Sitzung
    def _oeffnen(self):
        self.s, self.seq, self.schl = self.verbinde(self.ip, self.port), 0, self.key
        try:
            if self.version != "3.3":
                lokal = os.urandom(16)
                self._sende(SESS_START, lokal, False)
                a = self._lies((SESS_ANTWORT,))
                if len(a) < 48 or not hmac.compare_digest(a[16:48], _hmac(self.key, lokal)):
                    raise TuyaFehler("tuya_schluessel")
                fern = a[:16]
                self._sende(SESS_ENDE, _hmac(self.key, fern), False)
                self.schl = sitzungs_schluessel(self.version, self.key, lokal, fern)
        except Exception:
            self._zu()
            raise

    def _zu(self):
        try:
            self.s.close()
        except Exception:
            pass

    def _sende(self, cmd, klar, mit_kopf):
        self.seq += 1
        inner = versions_kopf(self.version) + klar if mit_kopf and self.version != "3.3" else klar
        if self.version == "3.3":
            enc = aes_rein.ecb_ver(self.schl, klar)
            f = rahmen_55aa(self.seq, cmd, versions_kopf("3.3") + enc if mit_kopf else enc)
        elif self.version == "3.4":
            f = rahmen_55aa(self.seq, cmd, aes_rein.ecb_ver(self.schl, inner), self.schl)
        else:
            f = rahmen_6699(self.seq, cmd, inner, self.schl, os.urandom(12))
        try:
            self.s.sendall(f)
        except OSError:
            raise TuyaFehler("nicht_erreichbar")

    def _genau(self, n):
        b = bytearray()
        while len(b) < n:
            try:
                t = self.s.recv(n - len(b))
            except OSError:
                t = b""
            if not t:
                # Verbindung stand, aber keine (vollstaendige) Antwort: meist falscher local_key oder falsche Version
                raise TuyaFehler("tuya_keine_antwort")
            b += t
        return bytes(b)

    def _rahmen(self):
        pre = self._genau(4)
        p = struct.unpack(">I", pre)[0]
        if p == 0x55AA:
            kopf = self._genau(12)
            ln = struct.unpack(">I", kopf[8:12])[0]
            if ln < 8 or ln > MAX_LAENGE:
                raise TuyaFehler("tuya_antwort_ungueltig")
            return pre + kopf + self._genau(ln)
        if p == 0x6699:
            kopf = self._genau(14)
            ln = struct.unpack(">I", kopf[10:14])[0]
            if ln < 28 or ln > MAX_LAENGE:
                raise TuyaFehler("tuya_antwort_ungueltig")
            return pre + kopf + self._genau(ln + 4)
        raise TuyaFehler("tuya_antwort_ungueltig")

    def _lies(self, erwartet):
        for _ in range(8):
            f = self._rahmen()
            try:
                if self.version == "3.3":
                    seq, cmd, rc, d = lies_55aa(f)
                    d = ohne_versions_kopf(d)
                    klar = aes_rein.ecb_ent(self.schl, d) if d else d
                elif self.version == "3.4":
                    seq, cmd, rc, d = lies_55aa(f, self.schl)
                    klar = ohne_versions_kopf(aes_rein.ecb_ent(self.schl, d)) if d else d
                else:
                    seq, cmd, rc, d = lies_6699(f, self.schl)
                    klar = ohne_versions_kopf(d)
            except ValueError:
                raise TuyaFehler("tuya_schluessel")
            if rc > 0 and rc != 0xFFFFFFFF and not klar:
                raise TuyaFehler("tuya_abgelehnt")
            if cmd in erwartet:
                return klar
        raise TuyaFehler("tuya_antwort_ungueltig")

    # ---------------------------------------------------------------- oeffentlich
    def dps(self):
        """Alle Datenpunkte als dict ({"1": True, "4": 16, ...})."""
        self._oeffnen()
        try:
            t = str(int(time.time()))
            if self.version == "3.3":
                self._sende(DP_QUERY, json.dumps({"gwId": self.id, "devId": self.id, "uid": self.id, "t": t}).encode(), False)
            else:
                self._sende(DP_QUERY_NEW, b"{}", False)
            for _ in range(6):
                klar = self._lies((DP_QUERY, DP_QUERY_NEW, STATUS))
                if not klar:
                    continue
                text = klar.decode("utf-8", "replace")
                if "data unvalid" in text:
                    raise TuyaFehler("tuya_variante")
                d = dps_aus(text)
                if d is not None:
                    return d
            raise TuyaFehler("tuya_antwort_ungueltig")
        finally:
            self._zu()

    def setze(self, dps):
        """DPs setzen; kehrt zurueck, sobald das Geraet bestaetigt hat (Zuruecklesen macht der Aufrufer)."""
        self._oeffnen()
        try:
            t = int(time.time())
            if self.version == "3.3":
                body = {"devId": self.id, "uid": self.id, "t": str(t), "dps": dps}
                self._sende(CONTROL, json.dumps(body).encode(), True)
            else:
                self._sende(CONTROL_NEW, json.dumps({"protocol": 5, "t": t, "data": {"dps": dps}}).encode(), True)
            self._lies((CONTROL, CONTROL_NEW, STATUS))
        finally:
            self._zu()
