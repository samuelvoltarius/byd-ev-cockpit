"""Tuya-Geraete im Heimnetz finden (WALLBOX_VERTRAG §4b): nur LAUSCHEN auf die Rundrufe, die Tuya-Geraete von selbst
alle paar Sekunden senden (UDP 6666 Klartext 3.1, 6667 AES-ECB 3.3/3.4, 7000 AES-GCM 3.5). Es wird nichts gesendet.

Inhalt eines Rundrufs: Geraete-ID (gwId), IP, Protokollversion, productKey. Den local_key enthaelt er NICHT.
Der feste Rundruf-Schluessel md5("yGAdlopoPVldABfn") ist oeffentlich bekannt (tuya-convert, tinytuya).
Eigene Umsetzung; tinytuya diente nur als Testorakel (Pruefpakete in test_tuya_finden.py).
"""
import hashlib
import json
import select
import socket
import time

import aes_rein
import tuya_lan

UDP_KEY = hashlib.md5(b"yGAdlopoPVldABfn").digest()
PORTS = (6666, 6667, 7000)


def entschluesseln(pkt):
    """Ein Rundruf-Paket -> dict oder None (unbekannt/kaputt)."""
    try:
        if pkt[:4] == b"\x00\x00\x55\xaa":
            _, _, _, d = tuya_lan.lies_55aa(pkt)
            if d[:1] == b"{" and d.rstrip(b"\x00")[-1:] == b"}":
                text = d.rstrip(b"\x00")
            else:
                text = aes_rein.ecb_ent(UDP_KEY, d)
        elif pkt[:4] == b"\x00\x00\x66\x99":
            _, _, _, d = tuya_lan.lies_6699(pkt, UDP_KEY)
            text = d.rstrip(b"\x00")
        else:
            text = aes_rein.ecb_ent(UDP_KEY, pkt)
        o = json.loads(text.decode("utf-8"))
        return o if isinstance(o, dict) else None
    except Exception:
        return None


def eintrag(o):
    """Nur, was wir brauchen; IP muss privat sein (sonst verworfen)."""
    from network_safety import private_ipv4
    gid, ip, ver = str(o.get("gwId") or o.get("devId") or ""), str(o.get("ip") or ""), str(o.get("version") or "")
    if not gid or not gid.isalnum() or len(gid) > 40:
        return None
    try:
        ip = private_ipv4(ip, "Tuya")
    except ValueError:
        return None
    return {"geraeteId": gid, "ip": ip, "version": ver if ver in tuya_lan.VERSIONEN else ("3.3" if ver in ("3.1", "3.2") else ver[:5]),
            "versionRoh": ver[:5], "productKey": str(o.get("productKey") or "")[:40]}


def suchen(dauer=6.0, ports=PORTS, uhr=time.monotonic):
    """Lauscht 'dauer' Sekunden. -> {"geraete": [...], "ports": [belegt/geoeffnet], "hinweis"?}"""
    socks, offen, belegt = [], [], []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("", p))
        except OSError:
            s.close()
            belegt.append(p)
            continue
        s.setblocking(False)
        socks.append(s)
        offen.append(p)
    gefunden = {}
    ende = uhr() + dauer
    try:
        while socks and uhr() < ende:
            bereit, _, _ = select.select(socks, [], [], max(0.0, min(0.5, ende - uhr())))
            for s in bereit:
                try:
                    pkt, _ = s.recvfrom(4096)
                except OSError:
                    continue
                o = entschluesseln(pkt)
                e = eintrag(o) if o else None
                if e:
                    gefunden[e["geraeteId"]] = e
    finally:
        for s in socks:
            s.close()
    erg = {"geraete": sorted(gefunden.values(), key=lambda x: x["ip"]), "ports": offen, "belegt": belegt}
    if belegt and not offen:
        erg["hinweis"] = "ports_belegt"
    return erg
