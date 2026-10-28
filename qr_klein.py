# -*- coding: utf-8 -*-
"""1.22: QR-Code in reinem Python (nur Standardbibliothek), nur das Noetige: Byte-Modus, Fehlerkorrektur M, Version 1-25 (bis ~1000 Byte).
Fuer "Handy verbinden": der Kopplungs-QR (QR v2) wird gross als SVG angezeigt. In den Tests gegen `qrcode` verglichen und mit OpenCV gelesen."""

# (Anzahl Bloecke, Codewoerter je Block gesamt, Datenwoerter je Block) je Version, Stufe M (ISO/IEC 18004, Tabelle 9)
RS_M = {
    1: [(1, 26, 16)], 2: [(1, 44, 28)], 3: [(1, 70, 44)], 4: [(2, 50, 32)], 5: [(2, 67, 43)], 6: [(4, 43, 27)], 7: [(4, 49, 31)],
    8: [(2, 60, 38), (2, 61, 39)], 9: [(3, 58, 36), (2, 59, 37)], 10: [(4, 69, 43), (1, 70, 44)], 11: [(1, 80, 50), (4, 81, 51)],
    12: [(6, 58, 36), (2, 59, 37)], 13: [(8, 59, 37), (1, 60, 38)], 14: [(4, 64, 40), (5, 65, 41)], 15: [(5, 65, 41), (5, 66, 42)],
    16: [(7, 73, 45), (3, 74, 46)], 17: [(10, 74, 46), (1, 75, 47)], 18: [(9, 69, 43), (4, 70, 44)], 19: [(3, 70, 44), (11, 71, 45)],
    20: [(3, 67, 41), (13, 68, 42)], 21: [(17, 68, 42)], 22: [(17, 74, 46)], 23: [(4, 75, 47), (14, 76, 48)],
    24: [(6, 73, 45), (14, 74, 46)], 25: [(8, 75, 47), (13, 76, 48)],
}

_EXP, _LOG = [0] * 512, [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _mul(a, b):
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def _erzeuger(n):
    g = [1]
    for i in range(n):
        neu = [0] * (len(g) + 1)
        for j, c in enumerate(g):
            neu[j] ^= c
            neu[j + 1] ^= _mul(c, _EXP[i])
        g = neu
    return g


def _rs(daten, n):
    g = _erzeuger(n)
    rest = list(daten) + [0] * n
    for i in range(len(daten)):
        c = rest[i]
        if c:
            for j in range(1, len(g)):
                rest[i + j] ^= _mul(g[j], c)
    return rest[len(daten):]


def _version_fuer(n):
    for v in range(1, 26):
        daten = sum(a * d for a, _, d in RS_M[v])
        bits = 4 + (8 if v < 10 else 16) + 8 * n
        if bits <= daten * 8:
            return v
    raise ValueError("zu lang fuer den QR-Code (%d Byte)" % n)


def _codewoerter(daten, v):
    gesamt = sum(a * d for a, _, d in RS_M[v])
    bits = "0100" + format(len(daten), "08b" if v < 10 else "016b") + "".join(format(b, "08b") for b in daten)
    bits += "0" * min(4, gesamt * 8 - len(bits))
    bits += "0" * (-len(bits) % 8)
    cw = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
    nd = len(cw)
    while len(cw) < gesamt:
        cw.append(0xEC if (len(cw) - nd) % 2 == 0 else 0x11)
    blocks, ecs, pos = [], [], 0
    for anz, tot, d in RS_M[v]:
        for _ in range(anz):
            b = cw[pos:pos + d]
            pos += d
            blocks.append(b)
            ecs.append(_rs(b, tot - d))
    aus = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                aus.append(b[i])
    for i in range(len(ecs[0])):
        for e in ecs:
            aus.append(e[i])
    return aus


def _ausrichtung(v):
    if v == 1:
        return []
    n = v // 7 + 2
    gross = 4 * v + 17
    roh = -(-(gross - 13) // (n - 1))          # ISO: Abstand = (Groesse-13)/(n-1), aufgerundet auf eine gerade Zahl
    schritt = roh + (roh % 2)
    return [6] + [gross - 7 - schritt * i for i in range(n - 2, -1, -1)]


def _bch(wert, gen, bits_gen):
    r = wert << (bits_gen - 1)
    while r.bit_length() >= bits_gen:
        r ^= gen << (r.bit_length() - bits_gen)
    return r


def _maske(m, i, j):
    return [(i + j) % 2 == 0, i % 2 == 0, j % 3 == 0, (i + j) % 3 == 0, (i // 2 + j // 3) % 2 == 0,
            (i * j) % 2 + (i * j) % 3 == 0, ((i * j) % 2 + (i * j) % 3) % 2 == 0, ((i + j) % 2 + (i * j) % 3) % 2 == 0][m]


def _strafe(mat):
    n = len(mat)
    p = 0
    for zeilen in (mat, [list(s) for s in zip(*mat)]):
        for z in zeilen:
            lauf = 1
            for k in range(1, n):
                if z[k] == z[k - 1]:
                    lauf += 1
                else:
                    if lauf >= 5:
                        p += 3 + lauf - 5
                    lauf = 1
            if lauf >= 5:
                p += 3 + lauf - 5
            s = "".join("1" if x else "0" for x in z)
            p += 40 * (s.count("10111010000") + s.count("00001011101"))
    for i in range(n - 1):
        for j in range(n - 1):
            if mat[i][j] == mat[i + 1][j] == mat[i][j + 1] == mat[i + 1][j + 1]:
                p += 3
    dunkel = sum(sum(1 for x in z if x) for z in mat)
    p += 10 * (abs(dunkel * 100 // (n * n) - 50) // 5)
    return p


def matrix(text, maske=None):
    """text (str, UTF-8) -> Matrix aus bool (True = dunkel), ohne Ruhezone."""
    daten = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    v = _version_fuer(len(daten))
    cw = _codewoerter(daten, v)
    n = 4 * v + 17
    mat = [[False] * n for _ in range(n)]
    fest = [[False] * n for _ in range(n)]

    def setze(i, j, dunkel):
        mat[i][j] = dunkel
        fest[i][j] = True
    for (zi, zj) in ((0, 0), (0, n - 7), (n - 7, 0)):                 # Suchmuster + Trennstreifen
        for di in range(-1, 8):
            for dj in range(-1, 8):
                i, j = zi + di, zj + dj
                if 0 <= i < n and 0 <= j < n:
                    ring = max(abs(di - 3), abs(dj - 3))
                    setze(i, j, 0 <= di <= 6 and 0 <= dj <= 6 and ring != 2)
    for k in range(8, n - 8):                                         # Zeitleisten
        setze(6, k, k % 2 == 0)
        setze(k, 6, k % 2 == 0)
    pos = _ausrichtung(v)
    for a in pos:
        for b in pos:
            if (a == 6 and b == 6) or (a == 6 and b == pos[-1]) or (a == pos[-1] and b == 6):
                continue                                              # an den Suchmustern entfaellt es
            for di in range(-2, 3):
                for dj in range(-2, 3):
                    setze(a + di, b + dj, max(abs(di), abs(dj)) != 1)
    setze(n - 8, 8, True)                                             # dunkles Modul
    for k in range(9):                                                # Format-Bereiche reservieren
        fest[8][k] = fest[k][8] = True
    for k in range(8):
        fest[8][n - 1 - k] = fest[n - 1 - k][8] = True
    if v >= 7:
        for a in range(6):
            for b in range(3):
                fest[a][n - 11 + b] = fest[n - 11 + b][a] = True
    bits = "".join(format(c, "08b") for c in cw)
    idx, aufwaerts = 0, True
    j = n - 1
    while j > 0:
        if j == 6:
            j -= 1
        for t in range(n):
            i = n - 1 - t if aufwaerts else t
            for dj in (0, 1):
                jj = j - dj
                if not fest[i][jj]:
                    mat[i][jj] = idx < len(bits) and bits[idx] == "1"
                    idx += 1
        aufwaerts = not aufwaerts
        j -= 2
    beste, bestm = None, None
    for m in ([maske] if maske is not None else range(8)):
        k = [z[:] for z in mat]
        for i in range(n):
            for jj in range(n):
                if not fest[i][jj] and _maske(m, i, jj):
                    k[i][jj] = not k[i][jj]
        _format(k, m, n)
        _versionsbits(k, v, n)
        s = _strafe(k)
        if beste is None or s < beste:
            beste, bestm = s, k
    return bestm


def _format(k, m, n):
    f = (0b00 << 3) | m                                                 # Stufe M = 00, dann Maske
    bits = ((f << 10) | _bch(f, 0b10100110111, 11)) ^ 0b101010000010010
    for i in range(15):
        d = (bits >> i) & 1 == 1
        if i < 6:
            k[i][8] = d
        elif i < 8:
            k[i + 1][8] = d
        else:
            k[n - 15 + i][8] = d
        if i < 8:
            k[8][n - i - 1] = d
        elif i < 9:
            k[8][15 - i - 1 + 1] = d
        else:
            k[8][15 - i - 1] = d
    k[n - 8][8] = True


def _versionsbits(k, v, n):
    if v < 7:
        return
    bits = (v << 12) | _bch(v, 0b1111100100101, 13)
    for i in range(18):
        d = (bits >> i) & 1 == 1
        k[i // 3][n - 11 + i % 3] = d
        k[n - 11 + i % 3][i // 3] = d


def svg(mat, rand=4, farbe_dunkel="#000", farbe_hell="#fff"):
    n = len(mat)
    teile = []
    for i, z in enumerate(mat):
        j = 0
        while j < n:
            if z[j]:
                k = j
                while k < n and z[k]:
                    k += 1
                teile.append("M%d %dh%dv1h-%dz" % (j + rand, i + rand, k - j, k - j))
                j = k
            else:
                j += 1
    g = n + 2 * rand
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" shape-rendering="crispEdges"><rect width="%d" height="%d" fill="%s"/>'
            '<path d="%s" fill="%s"/></svg>' % (g, g, g, g, farbe_hell, "".join(teile), farbe_dunkel))
