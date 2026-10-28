# -*- coding: utf-8 -*-
"""qr_klein.py: gleiche Matrix wie das Paket `qrcode` (Stufe M, Byte-Modus) und von OpenCV lesbar."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qr_klein as q  # noqa: E402

BEISPIEL = "https://byd.serveone.at/p/#k=" + "eyJ2IjoyLCJjIjoiMTIzNDU2IiwiYiI6eyJwIjoi" * 6


def referenz(text, maske=None):
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    from qrcode.util import MODE_8BIT_BYTE, QRData
    k = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=0, mask_pattern=maske)
    k.add_data(QRData(text.encode("utf-8"), mode=MODE_8BIT_BYTE))
    k.make(fit=True)
    return [[bool(x) for x in z] for z in k.get_matrix()]


class QrKlein(unittest.TestCase):
    def test_gleich_wie_qrcode_paket_bei_jeder_maske(self):
        try:
            import qrcode  # noqa: F401
        except Exception:
            self.skipTest("qrcode fehlt")
        for t in ("A", "hallo", "x" * 14, "x" * 15, "https://byd.serveone.at/p/#k=abc", "ä€ü", "y" * 120, "z" * 200, BEISPIEL, "w" * 500, "v" * 900):
            for m in range(8):
                self.assertEqual(q.matrix(t, m), referenz(t, m), (t[:12], m))
            self.assertIn(q.matrix(t), [referenz(t, m) for m in range(8)])         # die gewaehlte Maske ist eine gueltige

    def test_von_opencv_lesbar(self):
        try:
            import cv2
            import numpy as np
        except Exception:
            self.skipTest("opencv fehlt")
        for t in ("hallo welt", BEISPIEL, "ä€ü " * 30):
            m = q.matrix(t)
            n = len(m)
            bild = np.full((n + 8, n + 8), 255, np.uint8)
            for i, z in enumerate(m):
                for j, d in enumerate(z):
                    if d:
                        bild[i + 4, j + 4] = 0
            bild = cv2.resize(bild, None, fx=8, fy=8, interpolation=cv2.INTER_NEAREST)
            text, _, _ = cv2.QRCodeDetector().detectAndDecode(bild)
            self.assertEqual(text, t)

    def test_svg_und_grenzen(self):
        s = q.svg(q.matrix("abc"))
        self.assertTrue(s.startswith("<svg") and "<path" in s)
        with self.assertRaises(ValueError):
            q.matrix("x" * 2000)


if __name__ == "__main__":
    unittest.main()
