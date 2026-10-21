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

    def test_js_ids_gibt_es_im_html(self):
        """Jede getElementById('x') im Cockpit muss es als Element geben (sonst bricht load() ab: 1.12-Umbau)."""
        h = vorlage("COCKPIT")
        i = QUELLE.index("ENERGY_PANEL = r\'\'\'")
        ep = QUELLE[i:QUELLE.index("\'\'\'", i + 20)]
        alles = h + ep
        ids = set(re.findall(r"\bid=([A-Za-z_][\w-]*)", alles)) | set(re.findall(r'\bid="([A-Za-z_][\w-]*)"', alles))
        js = set(re.findall(r"getElementById\('([\w-]+)'\)", alles))
        dynamisch = {"geheimwarn", "einwhinweis"}
        self.assertEqual(sorted(js - ids - dynamisch), [])

    def test_keine_unquotierten_werte_vor_schraegstrich(self):
        """stroke-width=14/> wird im HTML zu '14/' und schliesst das Element nicht (Ring-Bogen fehlte jahrelang)."""
        self.assertEqual(re.findall(r"=[^\s\"'>=]+/>", QUELLE), [])


if __name__ == "__main__":
    unittest.main()
