# -*- coding: utf-8 -*-
"""1.22: Knopf "Handy verbinden": Das Cockpit holt ueber seine Kopplung beim Auto einen QR (QR v2) fuer eine NEUE Handy-Kopplung (art=handy)
und zeigt ihn gross an. Erlaubt wird NUR am Auto bzw. in Telegram (Pruefzahl), nie automatisch; das Cockpit speichert den QR nicht.

Vertrag (ENTWURF, von Panoptes noch nicht gebaut - Kern 12):
  POST /api/kopplung/weiteres-geraet  {"art":"handy","geraet":"<Name>","pruefzahl":"1234"}  -> {ok, id, gueltigBis} | {ok:false, grund}
  GET  /api/kopplung/weiteres-geraet/<id>  -> {status: wartet|erlaubt|abgelehnt|abgelaufen, qr: "https://byd.serveone.at/p/#k=..."}   (qr nur einmal)
Die Kopplung muss art=cockpit sein (nur direkt erreichbar; ueber die Bruecke gilt nur der Handy-Zugang)."""
import re

import qr_klein

PFAD = "/api/kopplung/weiteres-geraet"
QR_START = "https://byd.serveone.at/p/#k="
GRUENDE = {
    "nicht_erlaubt": "Panoptes erlaubt dem Cockpit das noch nicht. Bitte in Panoptes unter „Gekoppelte Geräte“ das Recht geben.",
    "ratenlimit": "Zu viele Anfragen. Bitte kurz warten.",
    "nicht_vorhanden": "Dein Panoptes kann das noch nicht. Bitte Panoptes aktualisieren.",
    "bruecke_aus": "Am Auto ist „Handy-App unterwegs nutzen“ noch aus. Ohne das klappt die Verbindung nur zu Hause im WLAN.",
}


def anfragen(pv, geraet, pruefzahl):
    """-> {"ok": True, "id"} | {"ok": False, "text"}"""
    d = pv.senden(PFAD, {"art": "handy", "geraet": geraet, "pruefzahl": pruefzahl})
    st = d.get("_status")
    if st in (404, 405):
        return {"ok": False, "text": GRUENDE["nicht_vorhanden"]}
    if st == 429:
        return {"ok": False, "text": GRUENDE["ratenlimit"]}
    if st in (401, 403) and not d.get("ok"):
        return {"ok": False, "text": GRUENDE.get(str(d.get("grund")), GRUENDE["nicht_erlaubt"])}
    if d.get("ok") and re.fullmatch(r"[0-9a-f]{32}", str(d.get("id") or "")):
        return {"ok": True, "id": d["id"]}
    return {"ok": False, "text": GRUENDE.get(str(d.get("grund")), "Das hat nicht geklappt. Bitte noch einmal versuchen.")}


def status(pv, aid):
    """-> {"status": wartet|erlaubt|abgelehnt|abgelaufen|fehler, "svg"?}. Der QR-Text wird nur in ein Bild umgewandelt, nicht gemerkt."""
    if not re.fullmatch(r"[0-9a-f]{32}", aid or ""):
        return {"status": "fehler"}
    d = pv._get(PFAD + "/" + aid)
    st = d.get("status") if isinstance(d, dict) else None
    if st == "erlaubt":
        qr = str(d.get("qr") or "")
        if not qr.startswith(QR_START) or len(qr) > 1000:
            return {"status": "fehler"}
        return {"status": "erlaubt", "svg": qr_klein.svg(qr_klein.matrix(qr), rand=4)}
    return {"status": st if st in ("wartet", "abgelehnt", "abgelaufen") else "fehler"}


SEITE = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Handy verbinden</title>
<meta name=evc-neu content=1>
<style>x</style></head><body><div class=w>
<h1>📱 Handy verbinden</h1>
<div class=sub>So bekommt die Panoptes-App auf deinem Handy Zugriff auf dein Auto.</div>
<div class=card id=s1>
 <h3>1 · Anfrage starten</h3>
 <div class=sub>Danach fragt dein Auto (oder Telegram), ob du das wirklich willst.</div>
 <button type=button id=los onclick="los()">📱 Handy verbinden</button>
 <div class=msg id=msg1></div>
</div>
<div class=card id=s2 style="display:none">
 <h3>2 · Am Auto oder in Telegram „Erlauben“ tippen</h3>
 <div class=sub>Die Prüfzahl dort muss so aussehen:</div>
 <div id=pz style="font:700 56px 'Sora',sans-serif;letter-spacing:.12em;text-align:center;margin:14px 0"></div>
 <div class=msg id=msg2>⏳ Warte auf dein „Erlauben“ …</div>
</div>
<div class=card id=s3 style="display:none">
 <h3>3 · Jetzt mit der Handy-App scannen</h3>
 <div id=qr style="max-width:420px;margin:12px auto;background:#fff;border-radius:16px;padding:6px"></div>
 <div class=sub style="text-align:center">Der Code gilt 10 Minuten und nur einmal. Er wird hier nicht gespeichert.</div>
 <div style="text-align:center;margin-top:12px"><button type=button class=sec onclick="location.reload()">Fertig</button></div>
</div>
</div>
<script>
const el=id=>document.getElementById(id);let PZ=null,ID=null,T=null;
async function los(){const b=el('los');b.disabled=true;el('msg1').textContent='⏳';
 try{const r=await (await fetch('/handy/qr/anfrage',{method:'POST',body:'{}'})).json();
  if(!r.ok){el('msg1').textContent='⚠️ '+__T(r.text||'Das hat nicht geklappt.');b.disabled=false;return;}
  ID=r.id;el('pz').textContent=r.pruefzahl;el('s1').style.display='none';el('s2').style.display='';warte(0);}
 catch(e){el('msg1').textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.');b.disabled=false;}}
async function warte(n){
 try{const r=await (await fetch('/handy/qr/status',{method:'POST',body:JSON.stringify({id:ID})})).json();
  if(r.status==='erlaubt'){el('s2').style.display='none';el('qr').innerHTML=r.svg;el('s3').style.display='';ID=null;return;}
  if(r.status==='abgelehnt'||r.status==='abgelaufen'||r.status==='fehler'||n>65){
   el('msg2').innerHTML='⚠️ '+esc(__T(r.status==='abgelehnt'?'Abgelehnt.':'Das hat nicht geklappt oder war zu langsam.'))+' <button type=button onclick="location.reload()">Noch einmal</button>';return;}}
 catch(e){}
 setTimeout(()=>warte(n+1),2000);}
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
</script></body></html>"""
