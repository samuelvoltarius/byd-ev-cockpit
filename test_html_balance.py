"""Seiten-Vorlagen: jedes <div>/<details> wird wieder geschlossen (faengt kaputte Zusammenfuehrungen ab)."""
import os
import re
import unittest

QUELLE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "evcockpit.py"), encoding="utf-8").read()


def vorlage(name):
    i = QUELLE.index(name + ' = r"""')
    return QUELLE[i:QUELLE.index('"""', i + len(name) + 8)]


class TestHtmlBalance(unittest.TestCase):
    def test_vorlagen_ausgeglichen(self):
        for name in ("WIZARD", "COCKPIT"):
            h = vorlage(name)
            for tag in ("div", "details", "table", "select"):
                self.assertEqual(len(re.findall(r"<%s\b" % tag, h)), h.count("</%s>" % tag), "%s: <%s> offen/zu ungleich" % (name, tag))


if __name__ == "__main__":
    unittest.main()
