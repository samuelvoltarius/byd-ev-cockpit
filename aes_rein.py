"""AES-128 in reinem Python (ECB mit PKCS7, GCM) fuer das Tuya-LAN-Protokoll (WALLBOX_VERTRAG §4b).

Das mitgelieferte Python hat kein AES (nur Standardbibliothek). Die Rahmen sind winzig (wenige hundert Byte je
Vorgang), Geschwindigkeit spielt keine Rolle. Eigene Umsetzung nach FIPS-197 und NIST SP 800-38D; in den Tests
gegen das Paket `cryptography` und die NIST-Pruefvektoren geprueft.
"""
import hmac

_SBOX = [0] * 256
_INV = [0] * 256


def _xtime(a):
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a


def _mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = _xtime(a)
        b >>= 1
    return r


def _sbox_bauen():
    p = q = 1
    while True:                                   # p durchlaeuft alle Elemente, q ist sein Inverses
        p = p ^ ((p << 1) & 0xFF) ^ (0x1B if p & 0x80 else 0)
        q ^= q << 1
        q ^= q << 2
        q ^= q << 4
        q &= 0xFF
        if q & 0x80:
            q ^= 0x09
        x = q ^ ((q << 1) | (q >> 7)) & 0xFF ^ ((q << 2) | (q >> 6)) & 0xFF ^ ((q << 3) | (q >> 5)) & 0xFF \
            ^ ((q << 4) | (q >> 4)) & 0xFF
        _SBOX[p] = (x ^ 0x63) & 0xFF
        if p == 1:
            break
    _SBOX[0] = 0x63
    for i, v in enumerate(_SBOX):
        _INV[v] = i


_sbox_bauen()
_M2 = [_mul(i, 2) for i in range(256)]
_M3 = [_mul(i, 3) for i in range(256)]
_M9 = [_mul(i, 9) for i in range(256)]
_M11 = [_mul(i, 11) for i in range(256)]
_M13 = [_mul(i, 13) for i in range(256)]
_M14 = [_mul(i, 14) for i in range(256)]


def _schluessel(key):
    if len(key) != 16:
        raise ValueError("AES-128 braucht 16 Byte Schluessel")
    w = [list(key[i:i + 4]) for i in range(0, 16, 4)]
    rcon = 1
    for i in range(4, 44):
        t = list(w[i - 1])
        if i % 4 == 0:
            t = [_SBOX[b] for b in t[1:] + t[:1]]
            t[0] ^= rcon
            rcon = _xtime(rcon)
        w.append([a ^ b for a, b in zip(w[i - 4], t)])
    return [sum(w[r * 4:r * 4 + 4], []) for r in range(11)]


def _block_ver(rk, s):
    s = [a ^ b for a, b in zip(s, rk[0])]
    for r in range(1, 11):
        s = [_SBOX[b] for b in s]
        s = [s[(i + 4 * (i % 4)) % 16] for i in range(16)]        # ShiftRows (Spalten-Reihenfolge)
        if r != 10:
            n = []
            for c in range(4):
                a0, a1, a2, a3 = s[4 * c:4 * c + 4]
                n += [_M2[a0] ^ _M3[a1] ^ a2 ^ a3, a0 ^ _M2[a1] ^ _M3[a2] ^ a3,
                      a0 ^ a1 ^ _M2[a2] ^ _M3[a3], _M3[a0] ^ a1 ^ a2 ^ _M2[a3]]
            s = n
        s = [a ^ b for a, b in zip(s, rk[r])]
    return bytes(s)


def _block_ent(rk, s):
    s = [a ^ b for a, b in zip(s, rk[10])]
    for r in range(9, -1, -1):
        s = [s[(i - 4 * (i % 4)) % 16] for i in range(16)]        # InvShiftRows
        s = [_INV[b] for b in s]
        s = [a ^ b for a, b in zip(s, rk[r])]
        if r != 0:
            n = []
            for c in range(4):
                a0, a1, a2, a3 = s[4 * c:4 * c + 4]
                n += [_M14[a0] ^ _M11[a1] ^ _M13[a2] ^ _M9[a3], _M9[a0] ^ _M14[a1] ^ _M11[a2] ^ _M13[a3],
                      _M13[a0] ^ _M9[a1] ^ _M14[a2] ^ _M11[a3], _M11[a0] ^ _M13[a1] ^ _M9[a2] ^ _M14[a3]]
            s = n
    return bytes(s)


def block(key, daten):
    """Ein Block verschluesseln (16 Byte)."""
    return _block_ver(_schluessel(key), daten)


def ecb_ver(key, daten, auffuellen=True):
    if auffuellen:
        n = 16 - len(daten) % 16
        daten = daten + bytes([n]) * n
    if len(daten) % 16:
        raise ValueError("ECB ohne Auffuellen braucht ganze Bloecke")
    rk = _schluessel(key)
    return b"".join(_block_ver(rk, daten[i:i + 16]) for i in range(0, len(daten), 16))


def ecb_ent(key, daten, auffuellen=True):
    if not daten or len(daten) % 16:
        raise ValueError("ECB-Daten sind keine ganzen Bloecke")
    rk = _schluessel(key)
    klar = b"".join(_block_ent(rk, daten[i:i + 16]) for i in range(0, len(daten), 16))
    if auffuellen:
        n = klar[-1]
        if not 1 <= n <= 16 or klar[-n:] != bytes([n]) * n:
            raise ValueError("Auffuellung ungueltig (falscher Schluessel?)")
        klar = klar[:-n]
    return klar


# ---------------------------------------------------------------- GCM (NIST SP 800-38D, 96-bit IV, 128-bit Tag)
_R = 0xE1000000000000000000000000000000


def _gmul(x, y):
    z, v = 0, y
    for i in range(127, -1, -1):
        if (x >> i) & 1:
            z ^= v
        v = (v >> 1) ^ _R if v & 1 else v >> 1
    return z


def _ghash(h, aad, ct):
    def bloecke(b):
        b = b + b"\0" * (-len(b) % 16)
        return [int.from_bytes(b[i:i + 16], "big") for i in range(0, len(b), 16)]
    y = 0
    for x in bloecke(aad) + bloecke(ct) + [((len(aad) * 8) << 64) | (len(ct) * 8)]:
        y = _gmul(y ^ x, h)
    return y


def _ctr(rk, iv, daten, start):
    aus = bytearray()
    for i in range(0, len(daten), 16):
        ks = _block_ver(rk, iv + (start + i // 16).to_bytes(4, "big"))
        aus += bytes(a ^ b for a, b in zip(daten[i:i + 16], ks))
    return bytes(aus)


def gcm_ver(key, iv, klar, aad=b""):
    """-> Geheimtext + 16 Byte Tag."""
    if len(iv) != 12:
        raise ValueError("GCM braucht 12 Byte IV")
    rk = _schluessel(key)
    h = int.from_bytes(_block_ver(rk, bytes(16)), "big")
    ct = _ctr(rk, iv, klar, 2)
    tag = int.from_bytes(_block_ver(rk, iv + b"\0\0\0\1"), "big") ^ _ghash(h, aad, ct)
    return ct + tag.to_bytes(16, "big")


def gcm_ent(key, iv, ct_tag, aad=b""):
    """Prueft den Tag; falsch -> ValueError (falscher Schluessel oder veraenderte Daten)."""
    if len(iv) != 12 or len(ct_tag) < 16:
        raise ValueError("GCM-Daten ungueltig")
    rk = _schluessel(key)
    ct, tag = ct_tag[:-16], ct_tag[-16:]
    h = int.from_bytes(_block_ver(rk, bytes(16)), "big")
    soll = int.from_bytes(_block_ver(rk, iv + b"\0\0\0\1"), "big") ^ _ghash(h, aad, ct)
    if not hmac.compare_digest(soll.to_bytes(16, "big"), tag):
        raise ValueError("GCM-Tag passt nicht (falscher Schluessel?)")
    return _ctr(rk, iv, ct, 2)
