# -*- coding: utf-8 -*-
"""Pruefung der Bruecken-Krypto (noise_rein.py): RFC-Vektoren, Gegenprobe mit dem Paket `cryptography` (falls da) und mit einer
unabhaengigen Noise-Bibliothek (`noiseprotocol`, nur zum Testen, Pfad in NOISE_REF_PFAD)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import noise_rein as nr  # noqa: E402

H = bytes.fromhex


class X25519Vektoren(unittest.TestCase):
    def test_rfc7748_5_2(self):
        self.assertEqual(nr.x25519(H("a546e36bf0527c9d3b16154b82465edd62144c0ac1fc5a18506a2244ba449ac4"),
                                   H("e6db6867583030db3594c1a424b15f7c726624ec26b3353b10a903a6d0ab1c4c")),
                         H("c3da55379de9c6908e94ea4df28d084f32eccf03491c71f754b4075577a28552"))
        self.assertEqual(nr.x25519(H("4b66e9d4d1b4673c5ad22691957d6af5c11b6421e0ea01d42ca4169e7918ba0d"),
                                   H("e5210f12786811d3f4b7959d0538ae2c31dbe7106fc03c3efc4cd549c715a493")),
                         H("95cbde9476e8907d7aade45cb4b873f88b595a68799fa152e6f8f7647aac7957"))

    def test_rfc7748_6_1_diffie_hellman(self):
        a = H("77076d0a7318a57d3c16c17251b26645df4c2f87ebc0992ab177fba51db92c2a")
        b = H("5dab087e624a8a4b79e17f8b83800ee66f3bb1292618b6fd1c2f8b27ff88e0eb")
        self.assertEqual(nr.oeffentlich(a), H("8520f0098930a754748b7ddcb43ef75a0dbf3a0d26381af4eba4a98eaa9b4e6a"))
        self.assertEqual(nr.oeffentlich(b), H("de9edb7d7b7dc1b4d35b61c2ece435373f8343c85b78674dadfc7e146f882b4f"))
        gem = H("4a5d9d5ba4ce2de1728e3bf480350f25e07e21c947d19e3376f09b3c1e161742")
        self.assertEqual(nr.dh(a, nr.oeffentlich(b)), gem)
        self.assertEqual(nr.dh(b, nr.oeffentlich(a)), gem)

    def test_rfc7748_iteriert_1(self):
        k = u = nr.BASIS
        k, u = nr.x25519(k, u), k
        self.assertEqual(k, H("422c8e7a6227d7bca1350b3e2bb7279f7897b87bb6854b783c60e80311ae3079"))

    def test_null_ergebnis_wird_abgelehnt(self):
        with self.assertRaises(nr.NoiseFehler):
            nr.dh(os.urandom(32), bytes(32))

    def test_gegen_cryptography(self):
        try:
            from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
            from cryptography.hazmat.primitives import serialization as s
        except Exception:
            self.skipTest("cryptography fehlt")
        for _ in range(5):
            a, b = X25519PrivateKey.generate(), X25519PrivateKey.generate()
            raw = lambda k: k.private_bytes(s.Encoding.Raw, s.PrivateFormat.Raw, s.NoEncryption())
            pub = lambda k: k.public_key().public_bytes(s.Encoding.Raw, s.PublicFormat.Raw)
            self.assertEqual(nr.oeffentlich(raw(a)), pub(a))
            self.assertEqual(nr.dh(raw(a), pub(b)), a.exchange(X25519PublicKey.from_public_bytes(pub(b))))


class ChaChaPolyVektoren(unittest.TestCase):
    def test_rfc8439_2_8_2(self):
        key = bytes(range(0x80, 0xA0))
        nonce = H("070000004041424344454647")
        aad = H("50515253c0c1c2c3c4c5c6c7")
        klar = (b"Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, "
                b"sunscreen would be it.")
        c = nr.aead_verschluesseln(key, nonce, aad, klar)
        self.assertEqual(c[-16:], H("1ae10b594f09e26a7e902ecbd0600691"))
        self.assertEqual(c[:16], H("d31a8d34648e60db7b86afbc53ef7ec2"))
        self.assertEqual(nr.aead_entschluesseln(key, nonce, aad, c), klar)

    def test_rfc8439_2_3_2_block(self):
        key = bytes(range(32))
        b = nr.chacha20_block(key, 1, H("000000090000004a00000000"))
        self.assertEqual(b[:16], H("10f1e7e4d13b5915500fdd1fa32071c4"))

    def test_rfc8439_2_5_2_poly1305(self):
        key = H("85d6be7857556d337f4452fe42d506a80103808afb0db2fd4abff6af4149f51b")
        self.assertEqual(nr.poly1305(key, b"Cryptographic Forum Research Group"), H("a8061dc1305136c6c22b8baf0c0127a9"))

    def test_verfaelscht_wird_abgelehnt(self):
        key, nonce = os.urandom(32), os.urandom(12)
        c = bytearray(nr.aead_verschluesseln(key, nonce, b"x", b"hallo"))
        c[0] ^= 1
        with self.assertRaises(nr.NoiseFehler):
            nr.aead_entschluesseln(key, nonce, b"x", bytes(c))

    def test_gegen_cryptography(self):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
        except Exception:
            self.skipTest("cryptography fehlt")
        for n in (0, 1, 15, 16, 17, 63, 64, 65, 200, 1000):
            key, nonce, aad, klar = os.urandom(32), os.urandom(12), os.urandom(n % 40), os.urandom(n)
            self.assertEqual(nr.aead_verschluesseln(key, nonce, aad, klar), ChaCha20Poly1305(key).encrypt(nonce, klar, aad), n)


class Blake2sVektoren(unittest.TestCase):
    def test_referenz(self):
        self.assertEqual(nr._hash(b"abc"), H("508c5e8c327c14e2e1a72ba34eeb452f37458b209ed63a294d999b4c86675982"))
        self.assertEqual(nr._hash(b""), H("69217a3079908094e11121d042354a7c1f55b6482ca1a51e1b250dfd1ed0eef9"))

    def test_hmac_blake2s_blockgroesse_64(self):
        # HMAC mit BLAKE2s braucht Blockgroesse 64 (hashlib liefert sie); Gegenprobe von Hand nach RFC 2104
        import hashlib
        k, m = b"k" * 20, b"Hi There"
        ipad = bytes(x ^ 0x36 for x in k.ljust(64, b"\x00"))
        opad = bytes(x ^ 0x5C for x in k.ljust(64, b"\x00"))
        hand = hashlib.blake2s(opad + hashlib.blake2s(ipad + m).digest()).digest()
        self.assertEqual(nr._hmac(k, m), hand)


class NoiseIK(unittest.TestCase):
    def _paar(self):
        auto, handy = nr.schluesselpaar(), nr.schluesselpaar()
        return auto, handy

    def test_handshake_beide_seiten_und_transport(self):
        auto, handy = self._paar()
        ini = nr.HandshakeIK(True, handy, rs=auto[1])
        res = nr.HandshakeIK(False, auto)
        m1 = ini.nachricht1()
        self.assertEqual(len(m1), 32 + 48 + 16)
        nutz, h_pub = res.lese1(m1)
        self.assertEqual((nutz, h_pub), (b"", handy[1]))        # Auto sieht den Handy-Schluessel (Zugangspruefung)
        m2 = res.nachricht2()
        self.assertEqual(len(m2), 32 + 16)
        ini.lese2(m2)
        self.assertEqual(ini.hash, res.hash)
        s_i, e_i = ini.teilen()
        s_r, e_r = res.teilen()
        c = s_i.verschluesseln(b"", b"GET /api/x")
        self.assertEqual(e_r.entschluesseln(b"", c), b"GET /api/x")
        c = s_r.verschluesseln(b"", b"antwort")
        self.assertEqual(e_i.entschluesseln(b"", c), b"antwort")

    def test_falscher_auto_schluessel_scheitert(self):
        auto, handy = self._paar()
        fremd = nr.schluesselpaar()
        ini = nr.HandshakeIK(True, handy, rs=fremd[1])
        res = nr.HandshakeIK(False, auto)
        with self.assertRaises(nr.NoiseFehler):
            res.lese1(ini.nachricht1())

    def test_fremder_schluessel_im_handshake_wird_erkannt(self):
        auto, handy = self._paar()
        ini = nr.HandshakeIK(True, handy, rs=auto[1])
        res = nr.HandshakeIK(False, auto)
        _, h_pub = res.lese1(ini.nachricht1())
        self.assertNotEqual(h_pub, nr.schluesselpaar()[1])

    def test_manipulierte_nachricht_2(self):
        auto, handy = self._paar()
        ini = nr.HandshakeIK(True, handy, rs=auto[1])
        res = nr.HandshakeIK(False, auto)
        res.lese1(ini.nachricht1())
        m2 = bytearray(res.nachricht2())
        m2[-1] ^= 1
        with self.assertRaises(nr.NoiseFehler):
            ini.lese2(bytes(m2))

    def test_nonce_zaehlt_weiter(self):
        auto, handy = self._paar()
        ini = nr.HandshakeIK(True, handy, rs=auto[1])
        res = nr.HandshakeIK(False, auto)
        res.lese1(ini.nachricht1())
        ini.lese2(res.nachricht2())
        s, _ = ini.teilen()
        _, e = res.teilen()
        c1, c2 = s.verschluesseln(b"", b"a"), s.verschluesseln(b"", b"a")
        self.assertNotEqual(c1, c2)
        with self.assertRaises(nr.NoiseFehler):               # falsche Reihenfolge -> Nonce passt nicht
            e.entschluesseln(b"", c2)

    def test_gegen_unabhaengige_noise_bibliothek(self):
        pfad = os.environ.get("NOISE_REF_PFAD")
        if not pfad:
            self.skipTest("NOISE_REF_PFAD nicht gesetzt")
        sys.path.insert(0, pfad)
        try:
            from noise.connection import NoiseConnection, Keypair
        except Exception as e:
            self.skipTest("noiseprotocol nicht ladbar: %s" % e)
        auto, handy = self._paar()
        # (a) unser Initiator gegen die fremde Bibliothek als Responder
        ref = NoiseConnection.from_name(b"Noise_IK_25519_ChaChaPoly_BLAKE2s")
        ref.set_as_responder()
        ref.set_keypair_from_private_bytes(Keypair.STATIC, auto[0])
        ref.set_prologue(nr.PROLOG)
        ref.start_handshake()
        ini = nr.HandshakeIK(True, handy, rs=auto[1])
        ref.read_message(ini.nachricht1())
        ini.lese2(ref.write_message())
        self.assertTrue(ref.handshake_finished)
        self.assertEqual(ref.get_handshake_hash(), ini.hash)
        s, e = ini.teilen()
        self.assertEqual(ref.decrypt(s.verschluesseln(b"", b"vom cockpit")), b"vom cockpit")
        self.assertEqual(e.entschluesseln(b"", ref.encrypt(b"vom auto")), b"vom auto")
        # (b) fremder Initiator gegen unseren Responder
        ref = NoiseConnection.from_name(b"Noise_IK_25519_ChaChaPoly_BLAKE2s")
        ref.set_as_initiator()
        ref.set_keypair_from_private_bytes(Keypair.STATIC, handy[0])
        ref.set_keypair_from_public_bytes(Keypair.REMOTE_STATIC, auto[1])
        ref.set_prologue(nr.PROLOG)
        ref.start_handshake()
        res = nr.HandshakeIK(False, auto)
        _, h_pub = res.lese1(ref.write_message())
        self.assertEqual(h_pub, handy[1])
        ref.read_message(res.nachricht2())
        self.assertEqual(ref.get_handshake_hash(), res.hash)


class PruefwerteKern10(unittest.TestCase):
    """Byte-gleich mit der Referenz von Kern 10 (BrueckeNoiseTest): Schluessel 1..32, 33..64, 65..96, 97..128, Prolog panoptes-bruecke/1."""
    MSG1 = ("64b101b1d0be5a8704bd078f9895001fc03e8e9f9522f188dd128d9846d48466822e8514e6389169bdfd10afecae5bded9cda3f0157ac1d03cd3620b3bb73a8"
            "66421c9c63a37995f11597388d964de276fadba84a508d06f472a78d8cfd8b141aa1c90feda248edc32ed")
    MSG2 = "244fe3b963e899dd295baffce248d3530f3a9a7479ba063002680ebfe7adad4985b4c79c930248ce911bbcaf33c3c69b39a64cf31427af67fc141b"
    T1 = "18060777b4ff4a1e3894653ebd2ec49d2204bc21b8d463"
    T2 = "0440d8d92c344a587b13268d281c6b369c961761803ec5"
    T3 = "58d50a4f514a7b1794a4d0562448371c6709dd758e8c84"
    HHASH = "de8da9cf6ac61fa72ef3cc4933143c2a9f103cd538c4c473deebbf3c4f9f2b6c"

    def test_handshake_und_transport_wie_die_referenz(self):
        si, sr, ei, er = (bytes(range(a, a + 32)) for a in (1, 33, 65, 97))
        ini = nr.HandshakeIK(True, (si, nr.oeffentlich(si)), rs=nr.oeffentlich(sr), e=(ei, nr.oeffentlich(ei)))
        res = nr.HandshakeIK(False, (sr, nr.oeffentlich(sr)), e=(er, nr.oeffentlich(er)))
        m1 = ini.nachricht1(b"hallo auto")
        self.assertEqual(m1.hex(), self.MSG1)
        self.assertEqual(res.lese1(m1)[0], b"hallo auto")
        m2 = res.nachricht2(b"hallo handy")
        self.assertEqual(m2.hex(), self.MSG2)
        self.assertEqual(ini.lese2(m2), b"hallo handy")
        self.assertEqual(ini.hash.hex(), self.HHASH)
        senden, empfangen = ini.teilen()
        auto_senden, _ = res.teilen()
        self.assertEqual(senden.verschluesseln(b"", b"anfrage").hex(), self.T1)
        self.assertEqual(auto_senden.verschluesseln(b"", b"antwort").hex(), self.T2)
        self.assertEqual(senden.verschluesseln(b"", b"anfrage").hex(), self.T3)

    def test_blake2s_und_hmac_wie_die_referenz(self):
        import hashlib
        self.assertEqual(hashlib.blake2s(bytes(range(256)) * 3).hexdigest(), "b928a17862e211e99759ba8819280803a914cd3dee7c5d711a3b5185aa96a7b3")
        self.assertEqual(nr._hmac(b"k" * 70, b"daten").hex(), "7a7b08c4a1142171acba52ab828082256b1bb919b0d9a9e3fa0a90655d86b938")


if __name__ == "__main__":
    unittest.main()
