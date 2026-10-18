"""Optional local energy dashboard for EV-Cockpit (read-only).

Launch: python3 energy_hub.py
Open http://127.0.0.1:8102
The evcc server address is entered in the browser and stored only in that
browser's localStorage. No charger control is performed.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
import json
import os
from evcc_backend import get_evcc_state

PORT = int(os.environ.get("EVCOCKPIT_ENERGY_PORT", "8102"))
HTML = """<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EV-Cockpit · Energie</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#091320;color:#eaf2ff;font:15px system-ui;padding:25px}
main{max-width:950px;margin:auto}h1{font-size:30px;font-weight:450}
header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
input,button{padding:12px;border-radius:10px;border:1px solid #36506d;background:#14253a;color:#fff;font:inherit}
button{background:#16659b;cursor:pointer}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;margin-top:22px}
.card{padding:20px;background:#142338;border:1px solid #28415c;border-radius:16px}
.k{color:#9cb3cd}.v{font-size:28px;font-weight:650;margin-top:10px}small{color:#9cb3cd}
#status{margin:16px 0;color:#9cb3cd}#loadpoints{white-space:pre-wrap;overflow-wrap:anywhere}
</style><main><header><div><h1>⚡ Energie-Hub</h1><small>PV · Netz · Speicher · Ladepunkte</small></div>
<a href="http://127.0.0.1:8099" style="color:#8ac8ff">EV-Cockpit ↗</a></header>
<p>evcc-IP: <input id="host" placeholder="192.168.1.20" aria-label="evcc IP">
Port: <input id="port" type="number" value="7070" min="1" max="65535" style="width:100px">
<button id="connect">Verbinden</button></p>
<small>Nur lokale Verbindung. Keine automatische Steuerung. evcc ist für die Laderegelung verantwortlich.</small>
<div id="status">Noch nicht verbunden</div><div class="grid">
<div class="card"><div class="k">☀️ PV</div><div class="v" id="pv">–</div></div>
<div class="card"><div class="k">⚡ Netz (+ Bezug / − Einspeisung)</div><div class="v" id="grid">–</div></div>
<div class="card"><div class="k">🔋 Speicher</div><div class="v" id="battery">–</div></div>
<div class="card"><div class="k">🏠 Haus</div><div class="v" id="home">–</div></div>
</div><h2>Ladepunkte</h2><div id="loadpoints" class="card">–</div></main>
<script>
const host=document.getElementById('host'),port=document.getElementById('port');
host.value=localStorage.getItem('evc_evcc_host')||'';
port.value=localStorage.getItem('evc_evcc_port')||'7070';
const watt=x=>typeof x==='number'&&Number.isFinite(x)?(x/1000).toLocaleString('de-DE',{maximumFractionDigits:2})+' kW':'–';
async function update(){
 if(!host.value)return;
 const status=document.getElementById('status');
 try{
  const url='/api/energy?host='+encodeURIComponent(host.value)+'&port='+encodeURIComponent(port.value);
  const res=await fetch(url);const data=await res.json();
  if(!res.ok)throw Error(data.error||'HTTP '+res.status);
  for(const key of ['pv','grid','battery','home'])document.getElementById(key).textContent=watt(data.site[key+'_w']);
  document.getElementById('loadpoints').textContent=JSON.stringify(data.loadpoints,null,2);
  status.textContent='Verbunden · letzte Aktualisierung '+new Date().toLocaleTimeString();
 }catch(e){status.textContent='Verbindung fehlgeschlagen: '+e.message;}
}
document.getElementById('connect').onclick=()=>{
 localStorage.setItem('evc_evcc_host',host.value);
 localStorage.setItem('evc_evcc_port',port.value);update();
};
setInterval(()=>{if(host.value)update()},15000);
if(host.value)update();
</script></html>"""


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body, mime):
        raw = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlsplit(self.path)
        if path.path == "/":
            return self.respond(200, HTML, "text/html; charset=utf-8")
        if path.path != "/api/energy":
            return self.respond(404, '{"error":"not found"}', "application/json")
        try:
            query = parse_qs(path.query)
            host = query["host"][0]
            port = int(query.get("port", ["7070"])[0])
            data = get_evcc_state(host, port)
            self.respond(200, json.dumps(data), "application/json")
        except (KeyError, ValueError, OSError, TimeoutError) as exc:
            self.respond(400, json.dumps({"error":str(exc)}), "application/json")


if __name__ == "__main__":
    print(f"Energy hub: http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
