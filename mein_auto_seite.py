# -*- coding: utf-8 -*-
"""Startseite "Mein Auto" (1.20): eine Seite, Panoptes-Look (Variablen/Fonts kommen aus LOOK_CSS), Kacheln wie im
freigegebenen Mockup (COCKPIT_NEU/mock120/mein_auto_panoptes.html). Alles Weitere: "Alle Funktionen" (Panoptes) und "Mehr".
Nur lesend ausser den drei Schnellknoepfen (Vorheizen, Zusperren, Klima aus) - KEIN Aufsperren, KEIN Finden/Blinken (Regel A+)."""

CSS = r"""
*{box-sizing:border-box}
body{margin:0;color:var(--ink);min-height:100vh}
.wrap{max-width:1280px;margin:0 auto;padding:18px 26px 40px}
.top{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:16px}
.top img.lg{width:46px;height:46px;border-radius:12px}
.top h1{font-family:'Sora',system-ui,sans-serif;font-weight:700;font-size:26px;letter-spacing:-.01em;margin:0}
.top .sub{color:var(--ink-2);font-size:14px}
.top .grow{flex:1}
.pill{display:inline-flex;align-items:center;gap:7px;padding:7px 12px;border-radius:999px;font-size:12.5px;font-weight:600;background:rgba(255,255,255,.045);border:1px solid var(--line);color:var(--ink-2);white-space:nowrap}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ink-3)}
.dot.ok{background:var(--lime);box-shadow:0 0 0 4px rgba(181,242,61,.15)}.dot.aq{background:var(--aqua)}.dot.warn{background:var(--amber)}
.btn{border:1px solid var(--line);background:rgba(255,255,255,.075);color:var(--ink);border-radius:12px;padding:10px 14px;font:600 13px 'Manrope',system-ui,sans-serif;cursor:pointer;display:inline-flex;align-items:center;gap:8px;text-decoration:none}
.btn:hover{border-color:var(--aqua)}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.card{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:20px;padding:20px;position:relative;overflow:hidden;min-width:0}
.card h2{font-family:'Sora',system-ui,sans-serif;font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:0 0 12px;display:flex;align-items:center;gap:8px}
.card h2 svg{width:16px;height:16px}
.card h2 .more{margin-left:auto;text-transform:none;letter-spacing:0;color:var(--aqua);font-weight:600;font-size:13px;text-decoration:none}
.c-hero{grid-column:span 7;display:grid;grid-template-columns:180px 1fr;gap:26px;align-items:center;padding:22px 24px;background:linear-gradient(135deg,rgba(11,92,102,.45),rgba(10,34,56,.35))}
.c-5{grid-column:span 5}.c-3{grid-column:span 3}
.gauge{width:180px;height:200px;border-radius:90px 90px 34px 34px;position:relative;overflow:hidden;background:rgba(4,16,27,.55);border:1px solid rgba(95,214,230,.25);box-shadow:inset 0 0 40px rgba(0,0,0,.35)}
.gauge .water{position:absolute;left:0;right:0;bottom:0;height:var(--lvl,0%);background:linear-gradient(180deg,#43c9db,#0B5C66);transition:height .6s}
.gauge .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-shadow:0 2px 14px rgba(0,0,0,.45)}
.gauge .val b{font-family:'Sora',system-ui,sans-serif;font-size:48px;font-weight:700;letter-spacing:-.03em;line-height:1}
.gauge .val b small{font-size:22px}.gauge .val>span{font-size:13px;color:#E8FBFD;opacity:.85;margin-top:4px}
.hero-txt .state{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--ink-2);margin-bottom:6px}
.hero-txt .range{font-family:'Sora',system-ui,sans-serif;font-size:56px;font-weight:700;letter-spacing:-.03em;line-height:1}
.hero-txt .range small{font-size:22px;color:var(--ink-2);font-weight:600;margin-left:4px}
.hero-txt .band{color:var(--ink-2);font-size:14px;margin:8px 0 16px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.carimg{height:132px;margin:-4px 0 4px;display:grid;place-items:center}
.carimg canvas{width:100%;max-width:300px;height:132px;display:block}
.carimg .ph{color:var(--ink-3);font-size:13px;text-align:center}
.cname{text-align:center;font-size:12px;color:var(--ink-3);margin-bottom:12px;min-height:16px}
.acts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.act{border:1px solid var(--line);background:rgba(255,255,255,.075);color:var(--ink);border-radius:16px;padding:14px 10px;display:flex;flex-direction:column;align-items:center;gap:8px;font:600 13px 'Manrope',system-ui,sans-serif;cursor:pointer}
.act svg{width:24px;height:24px;color:var(--aqua)}
.act.primary{background:var(--lime);color:var(--lime-ink);border-color:transparent}.act.primary svg{color:var(--lime-ink)}
.act.busy{opacity:.5;pointer-events:none}.act[disabled]{opacity:.5;cursor:not-allowed}
.actmsg{margin-top:10px;font-size:13px;color:var(--ink-2);min-height:18px}
.t{padding:16px 18px;min-height:118px}
.t .v{font-family:'Sora',system-ui,sans-serif;font-size:24px;font-weight:700;letter-spacing:-.02em}
.t .v small{font-size:13px;color:var(--ink-2);font-weight:600}
.t .muted{margin-top:4px;font-size:12.5px;color:var(--ink-2)}
.t .v.ok{color:var(--lime)}.t .v.warn{color:var(--amber)}
.minimap{height:62px;border-radius:12px;overflow:hidden;position:relative;background:linear-gradient(135deg,#0d2c40,#103b48);display:grid;place-items:center;color:var(--ink-3);font-size:12px}
.car{width:18px;height:18px;border-radius:50%;background:var(--lime);border:3px solid #0A2238;box-shadow:0 0 0 8px rgba(181,242,61,.18)}
.alle{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;border-style:dashed;text-decoration:none;color:var(--ink)}
.alle .v{font-size:20px}
.mehrmenu{position:absolute;right:26px;top:70px;z-index:50;background:#0e2a40;border:1px solid var(--line);border-radius:14px;padding:8px;min-width:260px;display:none;box-shadow:0 14px 40px rgba(2,10,18,.5)}
.mehrmenu.on{display:block}.mehrmenu a{display:block;padding:10px 12px;border-radius:10px;color:var(--ink);text-decoration:none;font-size:14px;font-weight:600}
.mehrmenu a:hover{background:rgba(95,214,230,.12)}.mehrmenu small{display:block;color:var(--ink-3);font-weight:500;font-size:12px}
.hinweis{margin:0 0 14px;padding:10px 14px;border-radius:12px;border:1px solid rgba(255,194,102,.55);background:rgba(255,194,102,.08);color:var(--amber);font-size:14px;font-weight:600;display:none}
.upd{margin:0 0 14px;padding:10px 14px;border-radius:12px;border:1px solid rgba(95,214,230,.45);background:rgba(95,214,230,.08);font-size:14px;display:none}
.upd a{color:var(--aqua)}
body.datenalt .c-hero,body.datenalt .t{opacity:.55}
@media(max-width:980px){.c-hero,.c-5{grid-column:span 12}.c-3{grid-column:span 6}}
@media(max-width:620px){.wrap{padding:14px 14px 40px}.c-hero{grid-template-columns:1fr;justify-items:center;text-align:center}.hero-txt .chips{justify-content:center}.c-3{grid-column:span 12}.top h1{font-size:22px}.act{padding:12px 4px;font-size:12px}}
"""

ICONS = r"""<svg width="0" height="0" style="position:absolute">
 <symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10.5" width="14" height="10" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-flash" viewBox="0 0 24 24"><path d="M13 2 4 14h7l-1 8 9-12h-7z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
 <symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="9.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-snow" viewBox="0 0 24 24"><path d="M12 2v20M3.5 7l17 10M20.5 7l-17 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
 <symbol id="i-eye" viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-tyre" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-warn" viewBox="0 0 24 24"><path d="M12 3.5 21.5 20h-19zM12 10v5M12 17.5v.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></symbol>
 <symbol id="i-door" viewBox="0 0 24 24"><path d="M6 20V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v14zM14.5 12.5v.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></symbol>
 <symbol id="i-more" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.6" fill="currentColor"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><circle cx="19" cy="12" r="1.6" fill="currentColor"/></symbol>
</svg>"""

BODY = r"""<body class=mein-auto>
""" + ICONS + r"""
<div class=wrap>
 <div id=updbar class=upd>🔔 <b>Version <span id=updver></span> ist da.</b> <span id=updwas></span> <a id=updlink href="#" target="_blank" rel="noopener">Ansehen →</a></div>
 <header class=top>
  <img class=lg src="/static/panoptes-logo.svg" alt="Panoptes" width=46 height=46>
  <div><h1>Panoptes Cockpit</h1><div class=sub id=sub>–</div></div>
  <div class=grow></div>
  <span class=pill id=pw style="display:none"><i class="dot"></i><span id=pwt>–</span></span>
  <span class=pill id=pq><i class="dot aq"></i><span id=pqt>–</span></span>
  <button type=button class=btn id=refreshbtn onclick="manualRefresh()">↻ Aktualisieren</button>
  <button type=button class=btn onclick="mehrUm(event)"><svg width=18 height=18><use href="#i-more"/></svg> Mehr</button>
 </header>
 <nav id=mehr class=mehrmenu>
  <a href="/setup">⚙️ Einstellungen<small>Quelle, Panoptes, Wallbox, Routenplaner-Kopplung</small></a>
  <a href="/klassisch#d_energie">⚡ Wallbox &amp; Energie<small>Wallbox steuern, evcc, Solar</small></a>
  <a href="/klassisch">🧰 Weitere Funktionen<small>Route, Ladekarten, Camping, Fahrtenbuch (alte Ansicht)</small></a>
  <a href="/about">ℹ️ Über · Lizenzen · Datenschutz</a>
  <a href="#" onclick="return sprache()">🌐 Deutsch / English</a>
 </nav>
 <div id=altband class=hinweis role=alert></div>
 <div class=grid>
  <section class="card c-hero">
   <div class=gauge id=gauge style="--lvl:0%"><div class=water></div><div class=val><b><span id=soc>–</span><small>%</small></b><span id=kwh>&nbsp;</span></div></div>
   <div class=hero-txt>
    <div class=state><i class="dot" id=sdot></i><span id=state>–</span></div>
    <div class=range><span id=rng>–</span><small>km</small></div>
    <div class=band id=band>Reichweite (geschätzt)</div>
    <div class=chips id=chips></div>
   </div>
  </section>
  <section class="card c-5">
   <h2>Schnell</h2>
   <div class=carimg id=car><div class=ph>Auto …</div></div><div class=cname id=cname></div>
   <div class=acts id=acts>
    <button type=button class="act primary" id=a_heat onclick="cmd('heat')" style="display:none"><svg><use href="#i-snow"/></svg>Vorheizen</button>
    <button type=button class=act id=a_lock onclick="zusperren()" style="display:none"><svg><use href="#i-lock"/></svg>Zusperren</button>
    <button type=button class=act id=a_off onclick="cmd('off')" style="display:none"><svg><use href="#i-snow"/></svg>Klima aus</button>
   </div>
   <div style="margin-top:10px"><button type=button class=btn id=a_setup onclick="handyKoppeln()" style="display:none" disabled>🔗 Steuern einrichten</button></div>
   <div class=actmsg id=actmsg></div>
  </section>
  <section class="card t c-3"><h2><svg><use href="#i-flash"/></svg>Laden<a class=more href="/klassisch#d_energie">Wallbox</a></h2><div class=v id=t_laden>–</div><div class=muted id=t_laden2></div></section>
  <section class="card t c-3"><h2><svg><use href="#i-snow"/></svg>Klima</h2><div class=v id=t_klima>–</div><div class=muted id=t_klima2></div></section>
  <section class="card t c-3"><h2><svg><use href="#i-door"/></svg>Türen &amp; Fenster</h2><div class=v id=t_tuer>–</div><div class=muted id=t_tuer2></div></section>
  <section class="card t c-3"><h2><svg><use href="#i-tyre"/></svg>Reifen</h2><div class=v id=t_reifen>–</div><div class=muted id=t_reifen2></div></section>
  <section class="card t c-3"><h2><svg><use href="#i-eye"/></svg>Wächter<a class=more href="__PANOPTES_WEB__/waechter.html" target="_blank" rel="noopener">Aufnahmen</a></h2><div class=v id=t_waech>–</div><div class=muted id=t_waech2></div></section>
  <section class="card t c-3"><h2><svg><use href="#i-pin"/></svg>Standort</h2><div class=minimap id=map>–</div><div class=muted id=t_pos></div></section>
  <section class="card t c-3"><h2><svg><use href="#i-warn"/></svg>Warnungen</h2><div class=v id=t_warn>–</div><div class=muted id=t_warn2></div></section>
  <a class="card t c-3 alle" id=alle href="__PANOPTES_WEB__/" target="_blank" rel="noopener"><div class=v>Alle Funktionen ↗</div><div class=muted>Fahrten, Ladeplan, Camping, Aufnahmen, Einstellungen – in Panoptes</div></a>
 </div>
</div>
<script>
const KARTEN_STIL='__KARTENSTIL__';
let S=null,DATA_TS=0,MSGHOLD=0,HANDY_OK;
const el=id=>document.getElementById(id);
const n=v=>(v==null||v==='')?'–':v;
const z=(v,d)=>v==null?'–':Number(v).toFixed(d==null?0:d).replace('.',window.__LANG__==='en'?'.':',');
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function mehrUm(e){e.stopPropagation();el('mehr').classList.toggle('on');}
document.addEventListener('click',()=>el('mehr').classList.remove('on'));
function sprache(){try{localStorage.setItem('evc_lang',window.__LANG__==='en'?'de':'en');}catch(e){}location.reload();return false;}
const WZ={scharf:['scharf','ok'],startet:['startet',''],unterdrueckt:['pausiert (sicherer Ort)',''],aus:['aus','warn'],nicht_gewaehlt:['bitte wählen','warn']};
function zeichne(s){
 S=s;DATA_TS=(s._poll_ts?s._poll_ts*1000:Date.now());
 const en=window.__LANG__==='en';
 el('sub').textContent=[s.model||'',__T('Daten von')+' '+new Date(DATA_TS).toLocaleTimeString(en?'en-GB':'de-AT',{hour:'2-digit',minute:'2-digit'}),
  s.gear==='P'?__T('geparkt'):(s.gear?__T('Gang')+' '+s.gear:'')].filter(Boolean).join(' · ');
 // Kopf-Pillen
 const wz=WZ[s.waechter_zustand];
 const pw=el('pw');if(s.panoptes_an){pw.style.display='';el('pwt').textContent=__T('Wächter')+' '+(wz?__T(wz[0]):'–');pw.querySelector('.dot').className='dot '+(wz&&wz[1]||'');}else pw.style.display='none';
 el('pqt').textContent=s.quelle||'–';
 // Akku + Reichweite
 const soc=s.soc==null?null:Math.round(s.soc);
 el('soc').textContent=soc==null?'–':soc;el('gauge').style.setProperty('--lvl',(soc==null?0:soc)+'%');
 const kwh=(s.battery_kwh&&soc!=null)?s.battery_kwh*soc/100:null;
 el('kwh').innerHTML=kwh==null?'&nbsp;':z(kwh,1)+' '+__T('von')+' '+z(s.battery_kwh,1)+' kWh';
 el('rng').textContent=s.real_range_km!=null?Math.round(s.real_range_km):(s.range_km!=null?Math.round(s.range_km):'–');
 el('band').textContent=(s.real_range_km!=null?__T('Reichweite (geschätzt)'):__T('Reichweite laut Auto'))+(s.real_range_km!=null&&s.range_km!=null?' · '+__T('Auto zeigt')+' '+Math.round(s.range_km)+' km':'');
 const lt=s.locked==='ON'?__T('zugesperrt'):s.locked==='OFF'?__T('offen'):__T('Schloss unbekannt');
 const lad=s.charging==='ON'?__T('lädt'):s.plugged==='ON'?__T('angesteckt'):__T('lädt nicht');
 el('state').textContent=[s.gear==='P'?__T('Geparkt'):'',lt,s.klima_on==='ON'?__T('Klima an'):__T('Klima aus')].filter(Boolean).join(' · ');
 el('sdot').className='dot '+(s.locked==='ON'?'ok':s.locked==='OFF'?'warn':'');
 const ch=[];if(s.gear)ch.push('Gang '+s.gear);if(s.v12!=null)ch.push('12 V · '+z(s.v12,1)+' V');if(s.odometer!=null)ch.push(Math.round(s.odometer).toLocaleString(en?'en-GB':'de-AT')+' km');
 el('chips').innerHTML=ch.map(c=>'<span class=pill>'+esc(c)+'</span>').join('');
 // Kacheln
 el('t_laden').textContent=lad;
 el('t_laden2').innerHTML=(s.charging==='ON'&&s.charge_power!=null?z(Math.abs(s.charge_power),1)+' kW':'')+(s.consumption_avg!=null?(s.charging==='ON'?'<br>':'')+'Ø '+z(s.consumption_avg,1)+' kWh/100 km':'');
 el('t_klima').textContent=s.klima_on==='ON'?__T('an'):s.klima_on==='OFF'?__T('aus'):'–';
 el('t_klima2').textContent=[s.temp_out!=null?__T('Außen')+' '+z(s.temp_out,0)+' °C':'',__T('innen unbekannt')].filter(Boolean).join(' · ');
 const tz=s.doors_open==='ON'?__T('offen'):s.doors_open==='OFF'?__T('alle zu'):'–';
 el('t_tuer').textContent=tz;el('t_tuer').className='v '+(s.doors_open==='ON'?'warn':'');
 el('t_tuer2').textContent=s.windows_open==='ON'?__T('Fenster offen'):s.windows_open==='OFF'?__T('Fenster zu'):__T('Fenster meldet Panoptes gerade nicht');
 const ty=['tyre_fl','tyre_fr','tyre_rl','tyre_rr'].map(k=>s[k]).filter(v=>v!=null);
 el('t_reifen').innerHTML=ty.length?z(Math.min.apply(null,ty),0)+' <small>kPa</small>':'–';
 el('t_reifen2').textContent=s.reifen&&s.reifen.stufe?(s.reifen.stufe==='gruen'?__T('in Ordnung'):__T('bitte prüfen')):(ty.length?__T('kleinster Wert aller vier Reifen'):'');
 el('t_waech').textContent=wz?__T(wz[0]):(s.panoptes_an?'–':__T('nicht verbunden'));el('t_waech').className='v '+(wz&&wz[1]||'');
 const w=s.waechter_letzt;
 el('t_waech2').textContent=w&&w.timestamp?__T('Letztes Ereignis')+' '+rel(w.timestamp):__T('noch kein Ereignis');
 el('t_pos').textContent=s.latitude!=null?z(s.latitude,4)+', '+z(s.longitude,4):__T('Standort unbekannt');
 karte(s);
 // Warnungen
 const W=[];
 if(s.reifen&&s.reifen.stufe&&s.reifen.stufe!=='gruen')W.push(__T('Reifendruck prüfen'));
 if(s.v12!=null&&s.v12<11.8)W.push(__T('12-V-Batterie schwach'));
 if(s._err)W.push(s._err);
 if(s.geheim_warnung)W.push(s.geheim_warnung);
 if(s.panoptes_an&&s.panoptes_erreichbar===false)W.push(__T('Panoptes antwortet gerade nicht'));
 el('t_warn').textContent=W.length?W.length+' '+__T(W.length>1?'Hinweise':'Hinweis'):__T('keine');el('t_warn').className='v '+(W.length?'warn':'');
 el('t_warn2').textContent=W.length?W[0]:'';
 // Schnellknoepfe
 const F=s.features||{},hy=!!s.handy_an,sicht=(id,an)=>{el(id).style.display=an?'':'none';};
 sicht('a_heat',F.klima||hy);sicht('a_off',F.klima||hy);sicht('a_lock',F.lock||hy);
 sicht('a_setup',!!s.panoptes_an&&!hy);
 if(s.panoptes_an&&!hy&&HANDY_OK===undefined){HANDY_OK=null;fetch('/panoptes/handy/pruefen',{method:'POST',body:'{}'}).then(r=>r.json()).then(r=>{HANDY_OK=r.vorhanden;handyKnopf();}).catch(()=>{HANDY_OK=undefined;});}
 handyKnopf();
 if(s._msg&&Date.now()>MSGHOLD)el('actmsg').textContent=s._msg;
 el('alle').style.display=s.panoptes_web?'':'none';
 if(s.update){el('updbar').style.display='block';el('updver').textContent=s.update.version;el('updwas').textContent=s.update.was_neu||'';el('updlink').href=s.update.url;}
 freshness();
}
function rel(ms){const m=Math.max(0,Math.round((Date.now()-ms)/60000)),en=window.__LANG__==='en';
 if(m<2)return en?'just now':'gerade eben';if(m<120)return en?m+' min ago':'vor '+m+' Min.';if(m<2880)return en?Math.round(m/60)+' h ago':'vor '+Math.round(m/60)+' Std.';return en?Math.round(m/1440)+' d ago':'vor '+Math.round(m/1440)+' Tagen';}
function freshness(){
 if(!S)return;const age=(Date.now()-DATA_TS)/1000,a=S.abfrage,takt=a&&a.takt_s?a.takt_s:null;
 const manuell=!!(a&&a.takt_s==null&&S.panoptes_an&&!a.pausiert),alt=!manuell&&age>Math.max(900,2*(takt||0));
 document.body.classList.toggle('datenalt',alt);const b=el('altband');
 if(!alt){b.style.display='none';return;}
 const h=age>=7200?Math.round(age/3600)+' h':Math.round(age/60)+' min',uhr=new Date(DATA_TS).toLocaleTimeString(window.__LANG__==='en'?'en-GB':'de-AT',{hour:'2-digit',minute:'2-digit'});
 b.style.display='block';b.textContent='⚠️ '+__T('Die Werte sind veraltet')+' – '+__T('Stand')+' '+uhr+' ('+h+'). '+__T('Das Auto meldet sich gerade nicht oder ist nicht erreichbar.');}
setInterval(freshness,5000);
// Auto-Bild: Modell aus dem Panoptes-Katalog (3D, nur mit Einwilligung), sonst Silhouette; keine frei waehlbare Farbe (Auto ist die Quelle)
let AUTO3D={ok:null};
async function auto3d(s){
 if(AUTO3D.ok!==null)return;AUTO3D.ok='laedt';
 try{const i=await (await fetch('/modell3d/info',{cache:'no-store'})).json();
  if(!i.verfuegbar||!window.WebGLRenderingContext)throw {};
  const THREE=await import('three');
  const {GLTFLoader}=await import('/static/three/examples/jsm/loaders/GLTFLoader.js');
  const {DRACOLoader}=await import('/static/three/examples/jsm/loaders/DRACOLoader.js');
  el('car').innerHTML='<canvas id=auto3d></canvas>';
  const cv=el('auto3d'),r=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});r.setPixelRatio(Math.min(2,window.devicePixelRatio||1));
  const sc=new THREE.Scene(),cam=new THREE.PerspectiveCamera(30,1,0.1,100);
  sc.add(new THREE.HemisphereLight(0xeaf6f8,0x0a2238,2.2));const dl=new THREE.DirectionalLight(0xffffff,2.4);dl.position.set(4,6,5);sc.add(dl);
  const dr=new DRACOLoader();dr.setDecoderPath('/static/three/examples/jsm/libs/draco/gltf/');const lo=new GLTFLoader();lo.setDRACOLoader(dr);
  const g=await lo.loadAsync('/modell3d/datei');const auto=g.scene,lack=[];
  auto.traverse(o=>{if(o.isMesh){const nm=((o.name||'')+' '+((o.material&&o.material.name)||'')).toLowerCase();if(nm.includes(i.paint)){o.material=o.material.clone();lack.push(o.material);}}});
  const box=new THREE.Box3().setFromObject(auto),gr=box.getSize(new THREE.Vector3()),mi=box.getCenter(new THREE.Vector3());
  auto.position.sub(mi);const pivot=new THREE.Group();pivot.add(auto);sc.add(pivot);
  const lang=Math.max(gr.x,gr.z);cam.position.set(lang*1.15,lang*0.42,lang*1.15);cam.lookAt(0,-gr.y*0.05,0);
  const farbe=i.farbe||((i.farben||[])[0]||{}).hex||'#E8E8EC';lack.forEach(m=>m.color&&m.color.set(farbe));
  const gro=()=>{const w=cv.clientWidth||300,h=cv.clientHeight||132;r.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();};gro();window.addEventListener('resize',gro);
  r.setAnimationLoop(()=>{if(document.hidden)return;pivot.rotation.y+=0.004;r.render(sc,cam);});
  el('cname').innerHTML=esc(i.name||s.model||'')+' · 3D: '+esc(i.author||'')+(i.license?', '+esc(String(i.license).replace('-',' ').replace('-',' ')):'')+' · <a href="'+esc(i.lizenzen||'#')+'" target=_blank rel=noopener style="color:inherit" title="'+esc(i.attribution||'')+'">'+esc(__T('Lizenz'))+'</a>';
  AUTO3D.ok=true;
 }catch(e){AUTO3D.ok=false;el('car').innerHTML='<div class=ph>🚗 '+esc((S&&S.model)||'')+'</div>';el('cname').textContent=(S&&S.model)||'';}}
// kleine Karte (nur mit Einwilligung fuer die Community-Karte), sonst Koordinaten
let MAPOBJ=null;
async function karte(s){
 const m=el('map');if(s.latitude==null){m.textContent='–';return;}
 if(!KARTEN_STIL){if(!MAPOBJ){m.textContent='📍';MAPOBJ=0;}return;}
 try{
  if(!MAPOBJ){
   await new Promise((ok,no)=>{const c=document.createElement('link');c.rel='stylesheet';c.href='/static/maplibre-gl.css';document.head.appendChild(c);
    const lade=u=>new Promise((o,n2)=>{const sc=document.createElement('script');sc.src=u;sc.onload=o;sc.onerror=n2;document.head.appendChild(sc);});
    lade('/static/maplibre-gl.js').then(()=>lade('/static/pmtiles.js')).then(ok,no);});
   if(window.pmtiles&&!window.__PMT){window.__PMT=1;maplibregl.addProtocol('pmtiles',new pmtiles.Protocol().tile);}
   m.textContent='';MAPOBJ=new maplibregl.Map({container:'map',style:KARTEN_STIL,center:[s.longitude,s.latitude],zoom:13,interactive:false,attributionControl:false});
   const d=document.createElement('div');d.className='car';MAPOBJ._mk=new maplibregl.Marker({element:d}).setLngLat([s.longitude,s.latitude]).addTo(MAPOBJ);
  }else if(MAPOBJ.setCenter){MAPOBJ.setCenter([s.longitude,s.latitude]);MAPOBJ._mk.setLngLat([s.longitude,s.latitude]);}
 }catch(e){MAPOBJ=0;m.textContent='📍';}}
// Schnellknoepfe: gleiche Wege wie bisher (/cmd), Panoptes-Weg wenn mit "Steuern einrichten" gekoppelt
function zusperren(){if(confirm(__T('Auto wirklich zusperren?')))cmd('lock');}
async function cmd(a){
 const m=el('actmsg');MSGHOLD=Date.now()+6000;m.textContent='⏳ '+__T('Sende …');
 const bs=[...document.querySelectorAll('.act')];bs.forEach(b=>b.classList.add('busy'));
 try{const r=await fetch('/cmd?a='+encodeURIComponent(a),{method:'POST'});const d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||__T('Befehl abgelehnt'));
  m.textContent='✓ '+__T('Befehl angenommen · Fahrzeugstatus wird aktualisiert');}
 catch(ex){m.textContent='⚠️ '+ex.message;}
 finally{bs.forEach(b=>b.classList.remove('busy'));}
 setTimeout(()=>{MSGHOLD=0;manualRefresh();},2500);}
function handyKnopf(){const b=el('a_setup');if(!b)return;const alt=HANDY_OK===false;b.disabled=HANDY_OK!==true;b.style.opacity=b.disabled?'.5':'';
 b.title=alt?__T('Braucht Panoptes ab 0.1.19.1'):__T('Einmal koppeln, damit das Cockpit über Panoptes zusperren und vorheizen darf.');}
async function handyKoppeln(){
 const m=el('actmsg');MSGHOLD=Date.now()+300000;m.textContent='⏳ …';
 try{const r=await (await fetch('/panoptes/handy/anfrage',{method:'POST',body:'{}'})).json();
  if(!r.ok){m.textContent='⚠️ '+r.error;return;}
  m.textContent='🔗 '+__T('In Panoptes (Telegram, Web oder Auto-Display) erlauben. Prüfzahl:')+' '+r.pruefzahl;
  for(let i=0;i<65;i++){await new Promise(zz=>setTimeout(zz,2000));
   const s=await (await fetch('/panoptes/handy/status',{method:'POST',body:'{}'})).json();
   if(s.status==='erlaubt'){m.textContent='✅ '+__T('Gekoppelt. Zusperren und Vorheizen gehen jetzt über Panoptes.');MSGHOLD=0;manualRefresh();return;}
   if(s.status!=='wartet'){m.textContent='⚠️ '+(s.error||'');return;}}
 }catch(e){m.textContent='⚠️ '+e;}}
// Laden: Daten holen
let TIMER=null;
async function load(){
 clearTimeout(TIMER);let t=60000;
 try{const s=await (await fetch('/data',{cache:'no-store'})).json();zeichne(s);auto3d(s);
  if(s.abfrage&&s.abfrage.takt_s)t=Math.min(60000,Math.max(5000,s.abfrage.takt_s*500));}catch(e){}
 try{const w=await (await fetch('/wallbox/status',{cache:'no-store'})).json();const lp=w&&w.ok&&w.quelle&&w.ladepunkte&&w.ladepunkte[0];
  if(lp&&S){const k=lp.leistungW!=null?z(Math.round(lp.leistungW/100)/10,1)+' kW':'–';
   el('t_laden2').innerHTML=(el('t_laden2').innerHTML?el('t_laden2').innerHTML+'<br>':'')+'Wallbox: '+esc(lp.erreichbar===false?__T('nicht erreichbar'):lp.laedt?__T('lädt'):__T('bereit'))+' · '+k+(lp.stromA!=null?' · '+lp.stromA+' A':'')+
    (lp.faehigkeiten&&lp.faehigkeiten.gesperrt?'<br>🔒 '+esc(__T('Steuerung an der Wallbox-Brücke gesperrt'))+'':'');}}catch(e){}
 TIMER=setTimeout(load,t);}
function manualRefresh(){clearTimeout(TIMER);fetch('/jetzt',{method:'POST'}).catch(function(){}).then(function(){setTimeout(load,1500);});}
document.addEventListener('visibilitychange',()=>{if(!document.hidden){clearTimeout(TIMER);load();}else clearTimeout(TIMER);});
load();
</script></body>"""

HEAD = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Panoptes Cockpit</title>
<script type=importmap>{"imports":{"three":"/static/three/three.module.min.js"}}</script>
<style>""" + CSS + """</style></head>"""

SEITE = HEAD + BODY + "</html>"


def seite(karten_stil="", panoptes_web=""):
    return SEITE.replace("__KARTENSTIL__", karten_stil).replace("__PANOPTES_WEB__", panoptes_web.rstrip("/"))
