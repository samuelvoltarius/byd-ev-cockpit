# -*- coding: utf-8 -*-
"""1.21: "Anpassen"-Modus der Startseite. Ein Stift-Knopf schaltet ihn ein; NUR dort lassen sich Kacheln verschieben (Ziehen oder Pfeile),
vergroessern (S/M/L, grosse Knoepfe), ausblenden/einblenden und alles zuruecksetzen. Ausserhalb des Modus passiert beim Antippen nichts davon.

Speicherort: im Profil des Cockpits (config.json, Schluessel "layout"), Zugriff ueber GET/POST /layout. Format (klein, fuer die Handy-App dokumentiert):
    {"v": 1, "reihe": ["route", "laden", ...], "kacheln": {"route": {"gr": "S", "aus": false}, ...}}
  reihe   = Reihenfolge der beweglichen Kacheln (IDs aus KACHELN); fehlende werden hinten angehaengt, unbekannte verworfen.
  gr      = Groesse "S" | "M" | "L" (Breite 2 | 4 | 6 von 10 Spalten; auf kleinen Schirmen passt sich das an).
  aus     = true: Kachel ausgeblendet (nur im Anpassen-Modus wieder sichtbar).
Die grosse Anzeige oben (Ladestand, Auto) ist fest und nicht Teil des Layouts."""

KACHELN = ("route", "laden", "wallbox", "klima", "camping", "tuer", "reifen", "waech", "pos", "warn", "alle")
GROESSEN = ("S", "M", "L")
STANDARD_GR = {"pos": "M"}          # alle anderen: S


def standard():
    return {"v": 1, "reihe": list(KACHELN), "kacheln": {k: {"gr": STANDARD_GR.get(k, "S"), "aus": False} for k in KACHELN}}


def bereinigen(roh):
    """Beliebige Eingabe -> gueltiges Layout (nie ein Fehler; Unbekanntes faellt weg, Fehlendes kommt aus dem Standard)."""
    out = standard()
    if not isinstance(roh, dict):
        return out
    r = roh.get("reihe")
    if isinstance(r, list):
        gesehen = []
        for k in r:
            if isinstance(k, str) and k in KACHELN and k not in gesehen:
                gesehen.append(k)
        out["reihe"] = gesehen + [k for k in KACHELN if k not in gesehen]
    kk = roh.get("kacheln")
    if isinstance(kk, dict):
        for k in KACHELN:
            e = kk.get(k)
            if isinstance(e, dict):
                if e.get("gr") in GROESSEN:
                    out["kacheln"][k]["gr"] = e["gr"]
                if isinstance(e.get("aus"), bool):
                    out["kacheln"][k]["aus"] = e["aus"]
    return out


CSS = r"""
.t.gr-S:not(.open){grid-column:span 2}.t.gr-M:not(.open){grid-column:span 4}.t.gr-L:not(.open){grid-column:span 6}
.t.anp-aus{display:none!important}
.anp .t.anp-aus{display:block!important;opacity:.38}
.anpbar{display:none}
.anp .anpbar{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:0 0 10px;padding-bottom:10px;border-bottom:1px dashed var(--line)}
.anp .t{outline:2px dashed rgba(95,214,230,.55);outline-offset:-2px;cursor:default;touch-action:pan-y}
.anp .t.ziehen{opacity:.55;outline-color:var(--lime)}
.anpbar button{min-height:46px;min-width:0;padding:0 6px;border-radius:12px;border:1px solid var(--line);background:rgba(255,255,255,.1);color:var(--ink);font:700 15px 'Manrope',system-ui,sans-serif;cursor:pointer}
.anpbar button.on{background:var(--lime);color:var(--lime-ink);border-color:transparent}
.anpbar .grip{cursor:grab;touch-action:none;font-size:20px}
.anpfuss{display:none;position:fixed;left:0;right:0;bottom:0;z-index:60;background:rgba(7,26,43,.97);border-top:1px solid var(--line);padding:12px 18px;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap}
.anp .anpfuss{display:flex}
.anpfuss .txt{color:var(--ink-2);font-size:14px;flex:1 1 220px}
.anp body,.anp{padding-bottom:84px}
@media(max-width:1000px){.t.gr-S:not(.open){grid-column:span 5}.t.gr-M:not(.open),.t.gr-L:not(.open){grid-column:span 10}}
@media(max-width:620px){.t.gr-S:not(.open),.t.gr-M:not(.open),.t.gr-L:not(.open){grid-column:span 10}}
"""

KNOPF = ('<button type=button class=btn id=anpknopf onclick="anpEin()" title="Kacheln anordnen" aria-label="Kacheln anordnen">'
         '<svg width=18 height=18 viewBox="0 0 24 24"><path d="M4 20l1-5L16.5 3.5a2 2 0 0 1 3 3L8 18z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg> Anpassen</button>')

FUSS = ('<div class=anpfuss id=anpfuss><span class=txt>Ziehen am Griff ⠿ oder mit den Pfeilen verschieben · Größe S M L · ✕ blendet aus.</span>'
        '<button type=button class=btn onclick="anpReset()">↺ Zurücksetzen</button><button type=button class="btn lime" onclick="anpAus()">✔ Fertig</button></div>')

JS = r"""
// ---- Anpassen-Modus (1.21) ----
let ANP=null,ANPAN=false;
const ANP_ID={alle:'alle'};
function anpEl(k){return document.getElementById(ANP_ID[k]||('t_'+k));}
function anpStd(){const o={v:1,reihe:['route','laden','wallbox','klima','camping','tuer','reifen','waech','pos','warn','alle'],kacheln:{}};o.reihe.forEach(k=>o.kacheln[k]={gr:k==='pos'?'M':'S',aus:false});return o;}
function anpAnwenden(){
 if(!ANP)return;const grid=document.querySelector('.grid');
 ANP.reihe.forEach(k=>{const e=anpEl(k);if(e)grid.appendChild(e);});
 ANP.reihe.forEach(k=>{const e=anpEl(k),c=ANP.kacheln[k];if(!e||!c)return;
  e.classList.remove('gr-S','gr-M','gr-L');e.classList.add('gr-'+c.gr);e.classList.toggle('anp-aus',!!c.aus);});
 if(ANPAN)anpBalken();}
function anpBalken(){
 ANP.reihe.forEach(k=>{const e=anpEl(k);if(!e)return;let b=e.querySelector(':scope>.anpbar');
  if(!b){b=document.createElement('div');b.className='anpbar';e.insertBefore(b,e.firstChild);}
  const c=ANP.kacheln[k];
  b.innerHTML='<button type=button class=grip data-k="'+k+'" title="'+__T('Ziehen')+'">⠿</button><button type=button onclick="anpBew(\''+k+'\',-1)" title="'+__T('Früher')+'">◀</button><button type=button onclick="anpBew(\''+k+'\',1)" title="'+__T('Später')+'">▶</button>'
   +['S','M','L'].map(g=>'<button type=button class="'+(c.gr===g?'on':'')+'" onclick="anpGr(\''+k+'\',\''+g+'\')">'+g+'</button>').join('')
   +'<button type=button onclick="anpSicht(\''+k+'\')" title="'+(c.aus?__T('Einblenden'):__T('Ausblenden'))+'" aria-label="'+(c.aus?__T('Einblenden'):__T('Ausblenden'))+'">'+(c.aus?'👁':'✕')+'</button>';
  b.querySelector('.grip').addEventListener('pointerdown',ev=>anpZiehen(ev,k));});}
function anpEin(){ANPAN=true;document.documentElement.classList.add('anp');document.body.classList.add('anp');document.querySelectorAll('.t.open').forEach(t=>t.classList.remove('open'));anpAnwenden();window.scrollTo({top:0,behavior:'smooth'});}
function anpAus(){ANPAN=false;document.documentElement.classList.remove('anp');document.body.classList.remove('anp');document.querySelectorAll('.anpbar').forEach(b=>b.remove());}
function anpSpeichern(){anpAnwenden();fetch('/layout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(ANP)}).catch(()=>{});}
function anpBew(k,r){const a=ANP.reihe,i=a.indexOf(k),j=i+r;if(i<0||j<0||j>=a.length)return;a.splice(i,1);a.splice(j,0,k);anpSpeichern();}
function anpGr(k,g){ANP.kacheln[k].gr=g;anpSpeichern();}
function anpSicht(k){ANP.kacheln[k].aus=!ANP.kacheln[k].aus;anpSpeichern();}
function anpReset(){if(!confirm(__T('Alle Kacheln wieder auf Standard setzen?')))return;ANP=anpStd();anpSpeichern();}
function anpZiehen(ev,k){ev.preventDefault();const e=anpEl(k),grid=document.querySelector('.grid');e.classList.add('ziehen');
 const g=ev.target;try{g.setPointerCapture(ev.pointerId);}catch(x){}
 const mv=m=>{const f=document.elementFromPoint(m.clientX,m.clientY),t=f&&f.closest&&f.closest('.t');
  if(t&&t!==e&&t.parentNode===grid){const r=t.getBoundingClientRect(),vor=(m.clientY<r.top+r.height/2)||(m.clientX<r.left+r.width/2&&m.clientY<r.bottom);grid.insertBefore(e,vor?t:t.nextSibling);}};
 const up=()=>{g.removeEventListener('pointermove',mv);g.removeEventListener('pointerup',up);g.removeEventListener('pointercancel',up);e.classList.remove('ziehen');
  const neu=[...grid.children].map(c=>(c.id==='alle'?'alle':(c.id||'').replace(/^t_/,''))).filter(x=>ANP.reihe.includes(x));
  ANP.reihe=neu.concat(ANP.reihe.filter(x=>!neu.includes(x)));anpSpeichern();};
 g.addEventListener('pointermove',mv);g.addEventListener('pointerup',up);g.addEventListener('pointercancel',up);}
document.addEventListener('click',ev=>{if(ANPAN&&ev.target.closest&&ev.target.closest('.t')&&!ev.target.closest('.anpbar')){ev.stopPropagation();ev.preventDefault();}},true);
fetch('/layout',{cache:'no-store'}).then(r=>r.json()).then(d=>{ANP=d&&d.reihe?d:anpStd();anpAnwenden();}).catch(()=>{ANP=anpStd();});
"""
