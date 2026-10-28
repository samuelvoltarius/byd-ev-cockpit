# -*- coding: utf-8 -*-
"""Tests der Bruecke (bruecke_client.py): mit dem ECHTEN Bruecken-Server von Kern 10 (F:\\panoptes-community, Zweig bruecke-server; Pfad in
BRUECKE_SERVER_PFAD) und einer Auto-Attrappe, die den Auto-Teil des Vertrags (Noise-Responder, [Flag][Daten], HTTP innen) nachbildet.
Ohne Server-Quelltext laufen nur die Tests ohne Netz."""
import asyncio
import base64
import hashlib
import http.client
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bruecke_client as bc  # noqa: E402
import noise_rein as nr  # noqa: E402
import ws_klein  # noqa: E402

SERVER_PFAD = os.environ.get("BRUECKE_SERVER_PFAD") or (r"F:\panoptes-community\server" if os.path.isdir(r"F:\panoptes-community\server") else "")
try:
    if SERVER_PFAD:
        sys.path.insert(0, SERVER_PFAD)
    import bruecke as server  # noqa: E402
except Exception:
    server = None


def b64(roh):
    return base64.urlsafe_b64encode(roh).decode().rstrip("=")


def geheimnis():
    roh = os.urandom(32)
    return b64(roh), hashlib.sha256(roh).hexdigest()


class Dienst:
    def __init__(self):
        self.dir = tempfile.mkdtemp()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

        async def start():
            b = server.Bruecke(os.path.join(self.dir, "b.db"), server.Grenzen())
            return b, await b.starte("127.0.0.1", 0)
        self.b, self.srv = asyncio.run_coroutine_threadsafe(start(), self.loop).result(10)
        self.port = self.srv.sockets[0].getsockname()[1]

    def rest(self, methode, pfad, body=None, g=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        h = {"Content-Type": "application/json"}
        if g:
            h["Authorization"] = "Bearer " + g
        c.request(methode, pfad, body=json.dumps(body).encode() if body is not None else None, headers=h)
        r = c.getresponse()
        t = r.read()
        c.close()
        return r.status, (json.loads(t) if t else None)

    def stop(self):
        async def ende():
            self.srv.close()
            for t in asyncio.all_tasks():
                if t is not asyncio.current_task():
                    t.cancel()
            await asyncio.sleep(0.05)
            self.b.speicher.schliessen()
        asyncio.run_coroutine_threadsafe(ende(), self.loop).result(10)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)


class AutoAttrappe(threading.Thread):
    """Der Auto-Teil: haengt ausgehend am Server, macht je Kanal den Noise-Responder, beantwortet HTTP innen mit `routen`."""

    def __init__(self, port, p, g_auto, auto_schluessel, erlaubte_h_pub, routen, stueck=60 * 1024):
        super().__init__(daemon=True)
        self.port, self.p, self.g, self.s, self.erlaubt, self.routen, self.stueck = port, p, g_auto, auto_schluessel, erlaubte_h_pub, routen, stueck
        self.ws = None
        self.kanaele = {}
        self.gesehen = []
        self.stop = False
        self.bereit = threading.Event()

    def run(self):
        self.ws = ws_klein.WsKlein("ws://127.0.0.1:%d/bruecke/v1/auto" % self.port, timeout=0.3).verbinden()
        self.ws.senden_text(json.dumps({"t": "hallo", "p": self.p, "g": self.g}))
        self.bereit.set()
        while not self.stop:
            try:
                art, d = self.ws.empfangen()
            except TimeoutError:
                continue
            except (ws_klein.WsZu, OSError):
                return
            if art == "text":
                continue
            k, nachricht = d[0], d[1:]
            st = self.kanaele.get(k)
            if st is None:
                hs = nr.HandshakeIK(False, self.s)
                try:
                    _, h_pub = hs.lese1(nachricht)
                except nr.NoiseFehler:
                    self.ws.senden_text(json.dumps({"t": "zu", "k": k}))
                    continue
                if b64(h_pub) not in self.erlaubt:
                    continue                       # unbekannter Handy-Schluessel: Kanal ohne Antwort
                self.ws.senden_bin(bytes([k]) + hs.nachricht2())
                ein, aus = hs.teilen()
                self.kanaele[k] = {"hs": hs, "aus": ein, "ein": aus, "roh": b""}
                continue
            klar = st["ein"].entschluesseln(b"", nachricht)
            st["roh"] += klar[1:]
            if klar[0] != 1:
                continue
            req, st["roh"] = json.loads(st["roh"].decode()), b""
            self.gesehen.append(req)
            s, h, b = self.routen(req)
            antwort = {"id": req["id"], "s": s, "h": h}
            if isinstance(b, bytes):
                antwort.update(b=base64.b64encode(b).decode(), b64=True)
            else:
                antwort["b"] = b
            roh = json.dumps(antwort).encode()
            teile = [roh[i:i + self.stueck] for i in range(0, len(roh), self.stueck)] or [b""]
            for i, t in enumerate(teile):
                self.ws.senden_bin(bytes([k]) + st["aus"].verschluesseln(b"", (b"\x01" if i == len(teile) - 1 else b"\x00") + t))


@unittest.skipIf(server is None, "Bruecken-Server (F:\\panoptes-community) nicht gefunden")
class MitEchtemServer(unittest.TestCase):
    def setUp(self):
        self.d = Dienst()
        self.addCleanup(self.d.stop)
        self.p, _ = geheimnis()
        self.g_auto, g_hash = geheimnis()
        self.d.rest("POST", "/bruecke/v1/postfach", {"p": self.p, "g_hash": g_hash})
        self.auto_s = nr.schluesselpaar()
        self.zug = bc.neue_schluessel()
        zh = hashlib.sha256(bc.b64u_ent(self.zug["g_handy"])).hexdigest()
        self.d.rest("POST", "/bruecke/v1/postfach/%s/zugang" % self.p, {"g_handy_hash": zh}, g=self.g_auto)
        self.cfg = dict(self.zug, server="http://127.0.0.1:%d/bruecke" % self.d.port, p=self.p, a_pub=b64(self.auto_s[1]))

    def auto(self, routen=None, erlaubt=None, **kw):
        a = AutoAttrappe(self.d.port, self.p, self.g_auto, self.auto_s, erlaubt if erlaubt is not None else [self.zug["h_pub"]],
                         routen or (lambda r: (200, {"content-type": "application/json"}, json.dumps({"pfad": r["p"], "m": r["m"], "auth": {k.lower(): v for k, v in r["h"].items()}.get("authorization", "")}))), **kw)
        a.start()
        self.assertTrue(a.bereit.wait(5))
        time.sleep(0.3)
        self.addCleanup(lambda: setattr(a, "stop", True))
        return a

    def test_anfrage_antwort_durch_echten_server(self):
        a = self.auto()
        br = bc.Bruecke(self.cfg)
        self.addCleanup(br.schliessen)
        r = br.anfrage("GET", "/api/ha/v1/zustand", {"Authorization": "Bearer JWT", "X-Boese": "1"})
        self.assertEqual(r["s"], 200)
        self.assertEqual(json.loads(r["b"]), {"pfad": "/api/ha/v1/zustand", "m": "GET", "auth": "Bearer JWT"})
        self.assertNotIn("x-boese", {k.lower() for k in a.gesehen[0]["h"]})          # nur die erlaubten Kopfzeilen
        r2 = br.anfrage("POST", "/api/handy/v1/aktion", {"Authorization": "Bearer J"}, b'{"aktion":"klima_aus"}')
        self.assertEqual(a.gesehen[1]["b"], '{"aktion":"klima_aus"}')               # zweite Anfrage in derselben Sitzung
        self.assertEqual(r2["s"], 200)

    def test_grosse_antwort_wird_gestueckelt(self):
        gross = os.urandom(150_000)
        self.auto(routen=lambda r: (200, {"content-type": "application/octet-stream"}, gross), stueck=20_000)
        br = bc.Bruecke(self.cfg)
        self.addCleanup(br.schliessen)
        self.assertEqual(br.anfrage("GET", "/x")["b"], gross)

    def test_grosse_anfrage_wird_gestueckelt(self):
        a = self.auto()
        br = bc.Bruecke(self.cfg)
        self.addCleanup(br.schliessen)
        body = json.dumps({"x": "a" * 200_000}).encode()
        br.anfrage("POST", "/api/x", {}, body)
        self.assertEqual(a.gesehen[0]["b"].encode(), body)

    def test_auto_offline(self):
        br = bc.Bruecke(self.cfg)
        with self.assertRaises(bc.BrueckeFehler) as e:
            br.anfrage("GET", "/x")
        self.assertEqual(e.exception.grund, "auto_offline")

    def test_falscher_zugang_4401(self):
        self.auto()
        br = bc.Bruecke(dict(self.cfg, g_handy=geheimnis()[0]))
        with self.assertRaises(bc.BrueckeFehler) as e:
            br.anfrage("GET", "/x")
        self.assertEqual(e.exception.grund, "zugang")

    def test_unbekannter_handy_schluessel_bekommt_keine_antwort(self):
        self.auto(erlaubt=[])
        br = bc.Bruecke(self.cfg)
        with self.assertRaises(bc.BrueckeFehler) as e:
            br.anfrage("GET", "/x", timeout=1.5)
        self.assertEqual(e.exception.grund, "entkoppelt")
        self.assertIn("nicht mehr gekoppelt", str(e.exception))

    def test_falscher_auto_schluessel_scheitert_ohne_antwort(self):
        self.auto()
        br = bc.Bruecke(dict(self.cfg, a_pub=b64(nr.schluesselpaar()[1])))
        with self.assertRaises(bc.BrueckeFehler):
            br.anfrage("GET", "/x", timeout=1.5)

    def test_sitzung_ueberlebt_abbruch_einmal_neu(self):
        self.auto()
        br = bc.Bruecke(self.cfg)
        self.addCleanup(br.schliessen)
        br.anfrage("GET", "/a")
        br.ws.s.close()                                   # Verbindung stirbt (Mobilfunk)
        self.assertEqual(br.anfrage("GET", "/b")["s"], 200)

    def test_weg_direkt_zuerst_dann_bruecke(self):
        self.auto()
        br = bc.Bruecke(self.cfg)
        self.addCleanup(br.schliessen)
        direkt = {"geht": True}

        def d_http(url, daten=None, jwt="", timeout=15, methode=None):
            if not direkt["geht"]:
                raise urllib.error.URLError("kein Weg")
            return {"direkt": True}

        def d_roh(url, daten=None, timeout=15, jwt=""):
            if not direkt["geht"]:
                raise urllib.error.URLError("kein Weg")
            return 200, {"direkt": True}
        t = {"t": 1000.0}
        w = bc.Weg("http://100.1.2.3:8180", br, d_http, d_roh, uhr=lambda: t["t"])
        self.assertTrue(w.gehoert("http://100.1.2.3:8180/api/x"))
        self.assertFalse(w.gehoert("http://100.1.2.30:8180/api/x"))
        self.assertEqual(w.http("http://100.1.2.3:8180/api/x"), {"direkt": True})
        self.assertEqual(w.aktiv, "direkt")
        direkt["geht"] = False
        r = w.http("http://100.1.2.3:8180/api/ha/v1/zustand", jwt="J")
        self.assertEqual(w.aktiv, "bruecke")
        self.assertEqual(r["pfad"], "/api/ha/v1/zustand")
        t["t"] += 10                                       # innerhalb der Pause: Direktweg gar nicht erst versuchen
        direkt["geht"] = True
        self.assertEqual(w.http("http://100.1.2.3:8180/api/x", jwt="J")["pfad"], "/api/x")
        t["t"] += 100                                      # Pause vorbei: wieder direkt
        self.assertEqual(w.http("http://100.1.2.3:8180/api/x"), {"direkt": True})
        self.assertEqual(w.aktiv, "direkt")


class OhneNetz(unittest.TestCase):
    def test_schluessel_und_adressen(self):
        z = bc.neue_schluessel()
        self.assertTrue(all(len(bc.b64u_ent(z[k])) == 32 for k in ("h_priv", "h_pub", "g_handy")))
        self.assertEqual(z["h_pub"], b64(nr.oeffentlich(bc.b64u_ent(z["h_priv"]))))
        self.assertEqual(bc.ws_url("https://byd.serveone.at/bruecke/"), "wss://byd.serveone.at/bruecke/v1/handy")
        self.assertEqual(bc.ws_url("http://127.0.0.1:8471/bruecke"), "ws://127.0.0.1:8471/bruecke/v1/handy")
        for schlecht in ("http://example.org/bruecke", "ftp://x", ""):
            with self.assertRaises(bc.BrueckeFehler):
                bc.ws_url(schlecht)
        with self.assertRaises(bc.BrueckeFehler):
            bc.b64u_ent("zu kurz")

    def test_fehlertexte_sind_klartext(self):
        for g in ("auto_offline", "limit", "zugang", "geloescht", "netz", "handshake", "zeit", "format", "entkoppelt", "jwt"):
            self.assertIn(g, bc.GRUND_TEXT)
        self.assertIn("kein Empfang", str(bc.BrueckeFehler("auto_offline")))

    def test_401_ueber_die_bruecke_heisst_zugang_abgelaufen(self):
        class B:
            def anfrage(self, *a, **k):
                return {"s": 401, "h": {}, "b": b"{}"}

        def kein_weg(*a, **k):
            raise urllib.error.URLError("x")
        w = bc.Weg("http://h:1", B(), kein_weg, kein_weg)
        import panoptes_source as ps
        with self.assertRaises(ps.NichtAngemeldet):
            w.http("http://h:1/x", jwt="alt")
        self.assertEqual(w.letzter_fehler, "jwt")

    def test_weg_ohne_bruecke_reicht_fehler_durch(self):
        def d_http(*a, **k):
            raise urllib.error.URLError("x")
        w = bc.Weg("http://h:1", None, d_http, d_http)
        with self.assertRaises(urllib.error.URLError):
            w.http("http://h:1/x")

    def test_weg_http_fehler_ist_antwort_und_kein_wegwechsel(self):
        def d_http(url, daten=None, jwt="", timeout=15, methode=None):
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        w = bc.Weg("http://h:1", object(), d_http, d_http)
        with self.assertRaises(urllib.error.HTTPError):
            w.http("http://h:1/x")
        self.assertEqual(w.aktiv, "direkt")


if __name__ == "__main__":
    unittest.main()
