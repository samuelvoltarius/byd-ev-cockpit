# -*- coding: utf-8 -*-
"""1.22: Krypto fuer die Panoptes-Bruecke in reinem Python (nur Standardbibliothek), genau nach Vertrag (BRUECKE_VERTRAG, Kern 10):
    Noise_IK_25519_ChaChaPoly_BLAKE2s, Prolog b"panoptes-bruecke/1", das Handy (Cockpit) ist Initiator, das Auto Responder.
Bausteine: X25519 (RFC 7748), ChaCha20-Poly1305 (RFC 8439), BLAKE2s/HMAC/HKDF (hashlib/hmac; Noise-Spezifikation Rev. 34 §4.3).
KEINE eigenen Abwandlungen am Protokoll. Geschwindigkeit ist unwichtig (Rahmen sind klein); Richtigkeit wird in test_noise_rein.py
gegen die RFC-Vektoren UND das Paket `cryptography` geprueft, der Handshake gegen die Referenz von Kern 10."""
import hashlib
import hmac
import os
import struct

PROLOG = b"panoptes-bruecke/1"
NAME = b"Noise_IK_25519_ChaChaPoly_BLAKE2s"
MAXLEN = 65535


class NoiseFehler(Exception):
    pass


# ---------------------------------------------------------------- X25519 (RFC 7748)
_P = 2 ** 255 - 19
_A24 = 121665
BASIS = (9).to_bytes(32, "little")


def _klemme(k):
    b = bytearray(k)
    b[0] &= 248
    b[31] &= 127
    b[31] |= 64
    return int.from_bytes(b, "little")


def x25519(k, u):
    """Skalarmultiplikation (Montgomery-Leiter, RFC 7748 §5). k, u: je 32 Byte."""
    if len(k) != 32 or len(u) != 32:
        raise NoiseFehler("x25519: 32 Byte erwartet")
    kk = _klemme(k)
    x1 = int.from_bytes(u, "little") & ((1 << 255) - 1)
    x2, z2, x3, z3, tausch = 1, 0, x1, 1, 0
    for t in range(254, -1, -1):
        kt = (kk >> t) & 1
        tausch ^= kt
        if tausch:
            x2, x3, z2, z3 = x3, x2, z3, z2
        tausch = kt
        a = (x2 + z2) % _P
        aa = a * a % _P
        b = (x2 - z2) % _P
        bb = b * b % _P
        e = (aa - bb) % _P
        c = (x3 + z3) % _P
        d = (x3 - z3) % _P
        da = d * a % _P
        cb = c * b % _P
        x3 = (da + cb) % _P
        x3 = x3 * x3 % _P
        z3 = (da - cb) % _P
        z3 = z3 * z3 % _P * x1 % _P
        x2 = aa * bb % _P
        z2 = e * (aa + _A24 * e) % _P
    if tausch:
        x2, x3, z2, z3 = x3, x2, z3, z2
    return (x2 * pow(z2, _P - 2, _P) % _P).to_bytes(32, "little")


def oeffentlich(priv):
    return x25519(priv, BASIS)


def schluesselpaar(zufall=os.urandom):
    p = zufall(32)
    return p, oeffentlich(p)


def dh(priv, pub):
    s = x25519(priv, pub)
    if s == bytes(32):
        raise NoiseFehler("x25519: ungueltiger oeffentlicher Schluessel (Ergebnis 0)")
    return s


# ---------------------------------------------------------------- ChaCha20-Poly1305 (RFC 8439)
def _rotl(v, n):
    return ((v << n) & 0xFFFFFFFF) | (v >> (32 - n))


def _viertel(s, a, b, c, d):
    s[a] = (s[a] + s[b]) & 0xFFFFFFFF
    s[d] = _rotl(s[d] ^ s[a], 16)
    s[c] = (s[c] + s[d]) & 0xFFFFFFFF
    s[b] = _rotl(s[b] ^ s[c], 12)
    s[a] = (s[a] + s[b]) & 0xFFFFFFFF
    s[d] = _rotl(s[d] ^ s[a], 8)
    s[c] = (s[c] + s[d]) & 0xFFFFFFFF
    s[b] = _rotl(s[b] ^ s[c], 7)


def chacha20_block(key, zaehler, nonce):
    k = struct.unpack("<8I", key)
    n = struct.unpack("<3I", nonce)
    anfang = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574, *k, zaehler & 0xFFFFFFFF, *n]
    s = list(anfang)
    for _ in range(10):
        _viertel(s, 0, 4, 8, 12)
        _viertel(s, 1, 5, 9, 13)
        _viertel(s, 2, 6, 10, 14)
        _viertel(s, 3, 7, 11, 15)
        _viertel(s, 0, 5, 10, 15)
        _viertel(s, 1, 6, 11, 12)
        _viertel(s, 2, 7, 8, 13)
        _viertel(s, 3, 4, 9, 14)
    return struct.pack("<16I", *[(s[i] + anfang[i]) & 0xFFFFFFFF for i in range(16)])


def chacha20_xor(key, zaehler, nonce, daten):
    aus = bytearray()
    for i in range(0, len(daten), 64):
        ks = chacha20_block(key, zaehler + i // 64, nonce)
        blk = daten[i:i + 64]
        aus += bytes(a ^ b for a, b in zip(blk, ks))
    return bytes(aus)


def poly1305(key, nachricht):
    r = int.from_bytes(key[:16], "little") & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    s = int.from_bytes(key[16:32], "little")
    p = (1 << 130) - 5
    acc = 0
    for i in range(0, len(nachricht), 16):
        blk = nachricht[i:i + 16]
        acc = (acc + int.from_bytes(blk + b"\x01", "little")) * r % p
    return ((acc + s) & ((1 << 128) - 1)).to_bytes(16, "little")


def _pad16(b):
    return b"\x00" * (-len(b) % 16)


def _mac(key, nonce, aad, chiffre):
    otk = chacha20_block(key, 0, nonce)[:32]
    return poly1305(otk, aad + _pad16(aad) + chiffre + _pad16(chiffre) + struct.pack("<QQ", len(aad), len(chiffre)))


def aead_verschluesseln(key, nonce, aad, klar):
    c = chacha20_xor(key, 1, nonce, klar)
    return c + _mac(key, nonce, aad, c)


def aead_entschluesseln(key, nonce, aad, chiffre):
    if len(chiffre) < 16:
        raise NoiseFehler("zu kurz")
    c, tag = chiffre[:-16], chiffre[-16:]
    if not hmac.compare_digest(tag, _mac(key, nonce, aad, c)):
        raise NoiseFehler("Entschluesselung fehlgeschlagen")
    return chacha20_xor(key, 1, nonce, c)


# ---------------------------------------------------------------- Noise: Hilfen (Spezifikation Rev. 34)
def _hash(d):
    return hashlib.blake2s(d).digest()


def _hmac(k, d):
    return hmac.new(k, d, hashlib.blake2s).digest()


def hkdf(ck, ikm, n):
    temp = _hmac(ck, ikm)
    o1 = _hmac(temp, b"\x01")
    o2 = _hmac(temp, o1 + b"\x02")
    if n == 2:
        return o1, o2
    return o1, o2, _hmac(temp, o2 + b"\x03")


def _nonce(n):
    return b"\x00\x00\x00\x00" + struct.pack("<Q", n)


class CipherState:
    def __init__(self, k=None):
        self.k, self.n = k, 0

    def verschluesseln(self, aad, klar):
        if self.k is None:
            return klar
        if self.n >= 2 ** 64 - 1:
            raise NoiseFehler("Nonce erschoepft")
        c = aead_verschluesseln(self.k, _nonce(self.n), aad, klar)
        self.n += 1
        return c

    def entschluesseln(self, aad, chiffre):
        if self.k is None:
            return chiffre
        if self.n >= 2 ** 64 - 1:
            raise NoiseFehler("Nonce erschoepft")
        k = aead_entschluesseln(self.k, _nonce(self.n), aad, chiffre)
        self.n += 1
        return k


class _Symmetrisch:
    def __init__(self):
        self.h = _hash(NAME) if len(NAME) > 32 else NAME.ljust(32, b"\x00")
        self.ck = self.h
        self.cs = CipherState()

    def mix_hash(self, d):
        self.h = _hash(self.h + d)

    def mix_key(self, ikm):
        self.ck, k = hkdf(self.ck, ikm, 2)
        self.cs = CipherState(k)

    def verschluesseln_und_hashen(self, klar):
        c = self.cs.verschluesseln(self.h, klar)
        self.mix_hash(c)
        return c

    def entschluesseln_und_hashen(self, chiffre):
        k = self.cs.entschluesseln(self.h, chiffre)
        self.mix_hash(chiffre)
        return k

    def teilen(self):
        a, b = hkdf(self.ck, b"", 2)
        return CipherState(a), CipherState(b)


class HandshakeIK:
    """Noise IK. Initiator (Cockpit): HandshakeIK(True, s=(priv,pub), rs=auto_pub). Responder (Test/Attrappe): HandshakeIK(False, s=...).
    Nachricht 1: e, es, s, ss. Nachricht 2: e, ee, se. Danach teilen() -> (senden, empfangen) aus Sicht dieser Seite."""

    def __init__(self, initiator, s, rs=None, zufall=os.urandom, e=None):
        self.ini, self.s, self.rs, self.re = initiator, s, rs, None
        self.e = e
        self.zufall = zufall
        self.sym = _Symmetrisch()
        self.sym.mix_hash(PROLOG)
        # Vor-Nachricht: der statische Schluessel des Responders ist beiden bekannt
        self.sym.mix_hash(rs if initiator else s[1])
        if initiator and (rs is None or len(rs) != 32):
            raise NoiseFehler("Auto-Schluessel (32 Byte) fehlt")

    def _neu_e(self):
        if self.e is None:
            self.e = schluesselpaar(self.zufall)
        return self.e

    def nachricht1(self, nutzlast=b""):
        if not self.ini:
            raise NoiseFehler("nur Initiator")
        e = self._neu_e()
        aus = bytearray(e[1])
        self.sym.mix_hash(e[1])
        self.sym.mix_key(dh(e[0], self.rs))                       # es
        aus += self.sym.verschluesseln_und_hashen(self.s[1])      # s
        self.sym.mix_key(dh(self.s[0], self.rs))                  # ss
        aus += self.sym.verschluesseln_und_hashen(nutzlast)
        if len(aus) > MAXLEN:
            raise NoiseFehler("zu lang")
        return bytes(aus)

    def lese1(self, msg):
        """Responder: Nachricht 1 lesen -> (Nutzlast, Handy-Schluessel rs)."""
        if self.ini:
            raise NoiseFehler("nur Responder")
        if len(msg) < 32 + 48 + 16:
            raise NoiseFehler("Nachricht 1 zu kurz")
        self.re = msg[:32]
        self.sym.mix_hash(self.re)
        self.sym.mix_key(dh(self.s[0], self.re))                  # es
        self.rs = self.sym.entschluesseln_und_hashen(msg[32:80])  # s
        self.sym.mix_key(dh(self.s[0], self.rs))                  # ss
        return self.sym.entschluesseln_und_hashen(msg[80:]), self.rs

    def nachricht2(self, nutzlast=b""):
        if self.ini:
            raise NoiseFehler("nur Responder")
        e = self._neu_e()
        aus = bytearray(e[1])
        self.sym.mix_hash(e[1])
        self.sym.mix_key(dh(e[0], self.re))                       # ee
        self.sym.mix_key(dh(e[0], self.rs))                       # se
        aus += self.sym.verschluesseln_und_hashen(nutzlast)
        return bytes(aus)

    def lese2(self, msg):
        """Initiator: Nachricht 2 lesen -> Nutzlast."""
        if not self.ini:
            raise NoiseFehler("nur Initiator")
        if len(msg) < 32 + 16:
            raise NoiseFehler("Nachricht 2 zu kurz")
        self.re = msg[:32]
        self.sym.mix_hash(self.re)
        self.sym.mix_key(dh(self.e[0], self.re))                  # ee
        self.sym.mix_key(dh(self.s[0], self.re))                  # se
        return self.sym.entschluesseln_und_hashen(msg[32:])

    def teilen(self):
        c1, c2 = self.sym.teilen()
        return (c1, c2) if self.ini else (c2, c1)

    @property
    def hash(self):
        return self.sym.h
