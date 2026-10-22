"""Tuya-LAN (WALLBOX_VERTRAG §4b): Pruefvektoren aus tinytuya 1.20 (MIT, Orakel, uebernommen aus Kern 6s WallboxTuyaTest)
und eine Geraete-Attrappe auf 127.0.0.1 fuer 3.3/3.4/3.5 (Aushandlung, Abfrage, Setzen)."""
import hashlib
import hmac
import json
import os
import socket
import struct
import threading
import unittest

import aes_rein
import tuya_lan as t

K = b"0123456789abcdef"
H = bytes.fromhex


class TestVektoren(unittest.TestCase):
    def test_55aa_crc_und_hmac(self):
        crc = H("000055aa000000010000000a0000000b616263ccc1bab90000aa55")
        self.assertEqual(t.rahmen_55aa(1, 10, b"abc"), crc)
        self.assertEqual(t.lies_55aa(crc)[1:], (10, -1, b"abc"))
        h = H("000055aa000000020000000d00000027616263eed8470ebb325a1f9c5e95ba65ab9272581c0f558a9b5f6f0c90a4e3f2de4af40000aa55")
        self.assertEqual(t.rahmen_55aa(2, 13, b"abc", K), h)
        self.assertEqual(t.lies_55aa(h, K)[3], b"abc")
        kaputt = bytearray(crc)
        kaputt[17] ^= 1
        with self.assertRaises(t.TuyaFehler) as f:
            t.lies_55aa(bytes(kaputt))
        self.assertEqual(f.exception.code, "tuya_pruefsumme")
        with self.assertRaises(t.TuyaFehler) as f:
            t.lies_55aa(h, b"fedcba9876543210")
        self.assertEqual(f.exception.code, "tuya_schluessel")

    def test_6699_gcm(self):
        f = H("000066990000000000030000000d00000021313233343536373839303132ae342e99847cfb2c7cafba5e6b4b45bb2c23eda29200009966")
        self.assertEqual(t.rahmen_6699(3, 13, b"hello", K, b"123456789012"), f)
        self.assertEqual(t.lies_6699(f, K)[1:], (13, -1, b"hello"))
        k = bytearray(f)
        k[25] ^= 1
        with self.assertRaises(t.TuyaFehler):
            t.lies_6699(bytes(k), K)

    def test_sitzungsschluessel_und_ecb(self):
        lok, fern = bytes(range(16)), bytes(100 + i for i in range(16))
        self.assertEqual(t.sitzungs_schluessel("3.4", K, lok, fern), H("66c0d72e3ec70800f70b18898e76c684"))
        self.assertEqual(t.sitzungs_schluessel("3.5", K, lok, fern), H("995ba0797218575a8c42637ebce7cc51"))
        self.assertEqual(aes_rein.ecb_ver(K, b'{"dps":{"1":true}}'),
                         H("c27ee03f8be481e63320de7dc6eb429664215f365b0dad6b2ac8fab15b1d40bd"))

    def test_aes_fips197(self):
        self.assertEqual(aes_rein.block(H("000102030405060708090a0b0c0d0e0f"), H("00112233445566778899aabbccddeeff")).hex(),
                         "69c4e0d86a7b0430d8cdb78070b4c55a")

    def test_aes_gegen_cryptography(self):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            self.skipTest("cryptography fehlt (nur Entwicklungsrechner)")
        for n in range(40):
            k, iv, d = os.urandom(16), os.urandom(12), os.urandom(n)
            self.assertEqual(aes_rein.gcm_ver(k, iv, d, b"x"), AESGCM(k).encrypt(iv, d, b"x"))


class Geraet(threading.Thread):
    """Geraeteseite einer Tuya-Wallbox (nur Test): DP 18 Schalter, 4 Strom, 3 Status, 9 Leistung."""

    def __init__(self, version, key=K):
        super().__init__(daemon=True)
        self.version, self.key = version, key
        self.dps = {"18": False, "4": 16, "3": "charger_free", "9": 0}
        self.srv = socket.socket()
        self.srv.bind(("127.0.0.1", 0))
        self.srv.listen(4)
        self.port = self.srv.getsockname()[1]
        self.gesetzt = []

    def run(self):
        while True:
            try:
                c, _ = self.srv.accept()
            except OSError:
                return
            try:
                self.sitzung(c)
            except Exception:
                pass
            finally:
                c.close()

    def lies(self, c, schl):
        pre = c.recv(4, socket.MSG_WAITALL)
        if len(pre) < 4:
            return None
        if struct.unpack(">I", pre)[0] == 0x55AA:
            kopf = c.recv(12, socket.MSG_WAITALL)
            f = pre + kopf + c.recv(struct.unpack(">I", kopf[8:])[0], socket.MSG_WAITALL)
            return t.lies_55aa(f, None if self.version == "3.3" else schl)
        kopf = c.recv(14, socket.MSG_WAITALL)
        f = pre + kopf + c.recv(struct.unpack(">I", kopf[10:])[0] + 4, socket.MSG_WAITALL)
        return t.lies_6699(f, schl)

    def schreibe(self, c, seq, cmd, klar, schl):
        if self.version == "3.3":
            f = t.rahmen_55aa(seq, cmd, b"\x00\x00\x00\x00" + (aes_rein.ecb_ver(schl, klar) if klar else b""))
        elif self.version == "3.4":
            f = t.rahmen_55aa(seq, cmd, b"\x00\x00\x00\x00" + (aes_rein.ecb_ver(schl, klar) if klar else b""), schl)
        else:
            f = t.rahmen_6699(seq, cmd, b"\x00\x00\x00\x00" + klar, schl, os.urandom(12))
        c.sendall(f)

    def sitzung(self, c):
        schl = self.key
        while True:
            r = self.lies(c, schl)
            if r is None:
                return
            seq, cmd, _, d = r
            if cmd == t.SESS_START:
                lokal = aes_rein.ecb_ent(schl, d) if self.version == "3.4" else d
                fern = os.urandom(16)
                self.schreibe(c, seq, t.SESS_ANTWORT, fern + hmac.new(self.key, lokal, hashlib.sha256).digest(), schl)
                self.lokal, self.fern = lokal, fern
                continue
            if cmd == t.SESS_ENDE:
                schl = t.sitzungs_schluessel(self.version, self.key, self.lokal, self.fern)
                continue
            if self.version == "3.3":
                klar = aes_rein.ecb_ent(schl, t.ohne_versions_kopf(d))
            elif self.version == "3.4":
                klar = t.ohne_versions_kopf(aes_rein.ecb_ent(schl, d))
            else:
                klar = t.ohne_versions_kopf(d)
            j = json.loads(klar)
            if cmd in (t.CONTROL, t.CONTROL_NEW):
                neu = j.get("dps") or j["data"]["dps"]
                self.gesetzt.append(neu)
                self.dps.update(neu)
                an = bool(self.dps["18"])
                self.dps["3"], self.dps["9"] = ("charger_charging", self.dps["4"] * 230) if an else ("charger_free", 0)
            self.schreibe(c, seq, cmd, json.dumps({"dps": self.dps}).encode(), schl)


class TestAttrappe(unittest.TestCase):
    def test_alle_versionen_lesen_und_setzen(self):
        for v in t.VERSIONEN:
            g = Geraet(v)
            g.start()
            lan = t.TuyaLan("127.0.0.1", "bf0123456789abcdefgh", K, v, port=g.port)
            self.assertEqual(lan.dps()["4"], 16, v)
            lan.setze({"4": 10})
            lan.setze({"18": True})
            d = lan.dps()
            self.assertEqual((d["4"], d["18"], d["3"], d["9"]), (10, True, "charger_charging", 2300), v)
            g.srv.close()

    def test_falscher_schluessel(self):
        for v in ("3.4", "3.5"):
            g = Geraet(v)
            g.start()
            with self.assertRaises(t.TuyaFehler) as f:
                t.TuyaLan("127.0.0.1", "x", b"fedcba9876543210", v, port=g.port).dps()
            self.assertIn(f.exception.code, ("tuya_schluessel", "tuya_keine_antwort"), v)
            g.srv.close()

    def test_schluessel_fehlt_und_version(self):
        with self.assertRaises(t.TuyaFehler):
            t.TuyaLan("192.168.1.5", "x", b"", "3.3")
        with self.assertRaises(t.TuyaFehler):
            t.TuyaLan("192.168.1.5", "x", K, "3.1")


if __name__ == "__main__":
    unittest.main()
