"""Opt-in LAN device discovery and read-only multi-vendor device inventory.

Run: python3 device_hub.py
Open http://127.0.0.1:8101. No cloud services or third-party dependencies.
Supported identification: evcc, go-eCharger (API v2), Shelly Gen2/3 (RPC).
Devices configured behind evcc remain manufacturer-independent.
"""
from __future__ import annotations
import concurrent.futures
import json
import os
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from network_safety import open_lan_url, private_ipv4, private_ipv4_network

PORT = int(os.environ.get("EVCOCKPIT_DEVICES_PORT", "8101"))
HOST = "127.0.0.1"
MAX_TARGETS = 254
_TIMEOUT = 0.6
_DEVICES = {}
_LOCK = threading.Lock()


def lan_address(value):
    return private_ipv4(value, "Device IP")


def probe(ip, timeout=_TIMEOUT):
    ip = lan_address(ip)
    for vendor, path in (
        ("evcc", "/api/state"),
        ("go-e", "/api/status?filter=car,pha,nrg"),
        ("Shelly", "/rpc/Shelly.GetDeviceInfo"),
    ):
        try:
            with open_lan_url(f"http://{ip}{path}", timeout=timeout) as response:
                if response.status != 200:
                    continue
                data = response.read(8193)
            if len(data) > 8192:
                continue
            payload = json.loads(data)
            if not isinstance(payload, dict):
                continue
            if vendor == "evcc":
                state = payload.get("result", payload)
                if not isinstance(state, dict) or not ({"loadpoints", "vehicles"} & state.keys()):
                    continue
                return {"ip": ip, "vendor": vendor,
                        "model": str(state.get("version") or "energy backend"), "online": True}
            if vendor == "go-e" and not any(k in payload for k in ("car", "pha", "nrg")):
                continue
            if vendor == "Shelly" and not ("model" in payload and "id" in payload):
                continue
            return {"ip": ip, "vendor": vendor, "model": str(payload.get("model", "")),
                    "online": True}
        except (OSError, ValueError, json.JSONDecodeError, TimeoutError):
            continue
    return {"ip": ip, "vendor": "Unknown", "online": False}


def discover(cidr):
    network = private_ipv4_network(cidr, max_addresses=256)
    targets = [str(ip) for ip in network.hosts()]
    if len(targets) > MAX_TARGETS:
        raise ValueError("Too many hosts")
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        return [item for item in pool.map(probe, targets) if item["online"]]


PAGE = """<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>EV-Cockpit · Geräte</title><style>
body{font:16px system-ui;background:#0c1423;color:#ecf4ff;max-width:750px;margin:35px auto;padding:16px}
input,button{font:inherit;padding:12px;border-radius:9px;margin:5px;background:#1b2d45;color:white;border:1px solid #456}
button{cursor:pointer;background:#185b91}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#162338;padding:16px;border-radius:10px}
small{color:#9cb0c8}</style><h1>Geräte im lokalen Netzwerk</h1>
<p>Herstellerübergreifende, schreibgeschützte Erkennung. Direkt: evcc, go-e und Shelly Gen2/3.
Weitere Wallboxen, PV-Systeme und Fahrzeuge werden über evcc eingebunden.</p>
<label>IP-Adresse <input id="ip" placeholder="192.168.1.50"></label>
<button onclick="run('add')">Gerät prüfen</button>
<p><label>Netzbereich <input id="cidr" placeholder="192.168.1.0/24"></label>
<button onclick="run('scan')">Netzwerk durchsuchen</button></p>
<small>Nur das eigene/autorisiert verwaltete LAN scannen. Keine Steuerbefehle.
Die Suche wird ausdrücklich erst nach Klick gestartet.</small><pre id="out">Noch keine Suche gestartet.</pre>
<script>
async function run(action){
 const out=document.getElementById('out');out.textContent='Suche läuft …';
 try{
  const body=action==='add'?{ip:document.getElementById('ip').value}:{cidr:document.getElementById('cidr').value};
  const r=await fetch('/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();out.textContent=JSON.stringify(d,null,2);
 }catch(e){out.textContent='Fehler: '+e.message}
}
</script></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, obj):
        payload = (obj if isinstance(obj, str) else json.dumps(obj)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8" if isinstance(obj, str) else "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/":
            return self._send(200, PAGE)
        if self.path == "/devices":
            with _LOCK:
                return self._send(200, list(_DEVICES.values()))
        self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path not in ("/add", "/scan"):
            return self._send(404, {"error": "Not found"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1024:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(size))
            if self.path == "/add":
                result = probe(data["ip"], timeout=2.0)
                found = [result] if result["online"] else []
            else:
                found = discover(data["cidr"])
            with _LOCK:
                for item in found:
                    _DEVICES[item["ip"]] = item
            return self._send(200, {"found": found, "count": len(found)})
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self._send(400, {"error": str(exc)})


if __name__ == "__main__":
    print(f"Device hub: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
