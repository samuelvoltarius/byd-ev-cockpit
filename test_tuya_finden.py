"""1.17: Tuya-Rundrufe im LAN lesen. Pruefpakete aus tinytuya tinytuya 1.20.0 pack_message + decrypt_udp (Orakel) (Orakel, pack_message + decrypt_udp)."""
import json
import socket
import threading
import time
import unittest

import tuya_finden as tf

VEKTOREN = json.loads('[{"port": 6666, "hex": "000055aa00000000000000130000009e000000007b226970223a223139322e3136382e312e3530222c2267774964223a226266303132333435363738396162636465666768222c22616374697665223a322c226162696c697479223a302c226d6f6465223a302c22656e6372797074223a747275652c2270726f647563744b6579223a226b65796162636465666768696a6b6c6d222c2276657273696f6e223a22332e31227ddf92c7fc0000aa55", "erwartet": {"ip": "192.168.1.50", "gwId": "bf0123456789abcdefgh", "active": 2, "ability": 0, "mode": 0, "encrypt": true, "productKey": "keyabcdefghijklm", "version": "3.1"}}, {"port": 6667, "hex": "000055aa0000000000000013000000ac00000000d09766676f3369eb10b5e9f132fd802a70172896956a9e330910344d11ac363f482611d8caa5248ac6cea65bdad007dfa41f010dca2abb30c50459a9f88024ffcb5924bb8792fe5eae7c9040e5921a98017f2170860421e6fc66f0a1ade138915fde850cd157270c5f3d1ab5ae90b3006a1e627c92b38e5884660240e05fe7d01c8343bc25f3403c0c4c3db59350d34ae0bd1f2cbad705886d4ed8eed5ab9eb9c169bc550000aa55", "erwartet": {"ip": "192.168.1.50", "gwId": "bf0123456789abcdefgh", "active": 2, "ability": 0, "mode": 0, "encrypt": true, "productKey": "keyabcdefghijklm", "version": "3.3"}}, {"port": 7000, "hex": "0000669900000000000000000013000000b2303132333435363738396162042ce52c1986e9abb3bec8436999f733293fda25acbd8d0b2851e6e71da00fd51b5884a72f672c34128034051fcfa1e5bcc151eb9b1c27eac979f7bc377f56cf6745d760e02641be83d47949878234b4ae7cc387373e8f5924c47d0a17bc3aa85eb1f8445b0a41f9d28fb71f2808ce9144763a38af690ddc7dff39b046f801202aeb1ee3a4231041122ee38204daeb98af418a2faf482db28a8d6488b20ca5c27440fd57896d00009966", "erwartet": {"ip": "192.168.1.50", "gwId": "bf0123456789abcdefgh", "active": 2, "ability": 0, "mode": 0, "encrypt": true, "productKey": "keyabcdefghijklm", "version": "3.5"}}]')


class TestEntschluesseln(unittest.TestCase):
    def test_udp_schluessel(self):
        self.assertEqual(tf.UDP_KEY.hex(), "6c1ec8e2bb9bb59ab50b0daf649b410a")

    def test_tinytuya_pakete(self):
        for v in VEKTOREN:
            self.assertEqual(tf.entschluesseln(bytes.fromhex(v["hex"])), v["erwartet"], v["port"])

    def test_kaputt_und_fremd(self):
        self.assertIsNone(tf.entschluesseln(b"hallo"))
        p = bytearray(bytes.fromhex(VEKTOREN[1]["hex"]))
        p[25] ^= 1
        self.assertIsNone(tf.entschluesseln(bytes(p)))

    def test_eintrag_nur_privat(self):
        e = tf.eintrag(VEKTOREN[1]["erwartet"])
        self.assertEqual((e["geraeteId"], e["ip"], e["version"]), ("bf0123456789abcdefgh", "192.168.1.50", "3.3"))
        self.assertEqual(tf.eintrag(VEKTOREN[0]["erwartet"])["version"], "3.3")       # 3.1-Rundruf: LAN-Protokoll 3.3
        self.assertIsNone(tf.eintrag(dict(VEKTOREN[1]["erwartet"], ip="8.8.8.8")))
        self.assertIsNone(tf.eintrag(dict(VEKTOREN[1]["erwartet"], gwId="x;rm")))


class TestLauschen(unittest.TestCase):
    def test_empfaengt_rundruf_auf_freiem_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        def senden():
            time.sleep(0.3)
            u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            u.sendto(bytes.fromhex(VEKTOREN[2]["hex"]), ("127.0.0.1", port))
            u.close()
        threading.Thread(target=senden, daemon=True).start()
        erg = tf.suchen(dauer=1.5, ports=(port,))
        self.assertEqual([g["geraeteId"] for g in erg["geraete"]], ["bf0123456789abcdefgh"])
        self.assertEqual(erg["geraete"][0]["version"], "3.5")


if __name__ == "__main__":
    unittest.main()
