# -*- coding: utf-8 -*-
"""Startseite "Mein Auto" (1.20.1): eine Seite im Panoptes-Look (Variablen/Fonts aus LOOK_CSS), Kacheln wie im freigegebenen
Mockup (COCKPIT_NEU/mock120/mein_auto_121.html). Bedien-Kacheln (Route, Laden, Klima, Camping) klappen auf.
Route und Camping werden aus der alten Ansicht (/klassisch) UEBERNOMMEN, nicht neu erfunden: Das Skript wird zur Laufzeit aus
dem COCKPIT-Text geschnitten (eine Quelle, bis /klassisch in 1.21 entfaellt). Befehle: nur die geprueften Wege (/cmd, /wallbox/*).
KEIN Aufsperren, KEIN Finden/Blinken (Regel A+)."""
import re

import anpassen

CSS = r"""
*{box-sizing:border-box}
:root{--surface:#0A2238;--soft:#0f2c40;--border:#1d4152;--txt:#EAF6F8;--mut:#A9C7CE;--blue:#5FD6E6;--lime-ink:#1d2a00}
body{margin:0;color:var(--ink);min-height:100vh}
.wrap{max-width:1280px;margin:0 auto;padding:12px 26px 24px}
.top{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:12px}
.top img.lg{width:42px;height:42px;border-radius:12px}
.top h1{font-family:'Sora',system-ui,sans-serif;font-weight:700;font-size:22px;letter-spacing:-.01em;margin:0}
.top .sub{color:var(--ink-2);font-size:14px}
.top .grow{flex:1}
.pill{display:inline-flex;align-items:center;gap:7px;padding:7px 12px;border-radius:999px;font-size:12.5px;font-weight:600;background:rgba(255,255,255,.045);border:1px solid var(--line);color:var(--ink-2);white-space:nowrap}
.dot{width:8px;height:8px;border-radius:50%;background:var(--ink-3)}
.dot.ok{background:var(--lime);box-shadow:0 0 0 4px rgba(181,242,61,.15)}.dot.aq{background:var(--aqua)}.dot.warn{background:var(--amber)}
.btn{border:1px solid var(--line);background:rgba(255,255,255,.075);color:var(--ink);border-radius:12px;padding:9px 14px;font:600 13px 'Manrope',system-ui,sans-serif;cursor:pointer;display:inline-flex;align-items:center;gap:8px;text-decoration:none}
.btn:hover{border-color:var(--aqua)}.btn.lime{background:var(--lime);color:var(--lime-ink);border-color:transparent}
.btn[disabled]{opacity:.45;cursor:not-allowed}
.grid{display:grid;grid-template-columns:repeat(10,1fr);gap:12px}
.card{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:20px;padding:14px 16px;position:relative;overflow:hidden;min-width:0}
.card h2{font-family:'Sora',system-ui,sans-serif;font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);margin:0 0 6px;display:flex;align-items:center;gap:8px}
.card h2 svg{width:16px;height:16px}
.card h2 .more{margin-left:auto;text-transform:none;letter-spacing:0;color:var(--aqua);font-weight:600;font-size:13px;text-decoration:none}
.c-hero{grid-column:span 6;display:grid;grid-template-columns:150px 1fr;gap:22px;align-items:center;padding:14px 22px;background:linear-gradient(135deg,rgba(11,92,102,.45),rgba(10,34,56,.35))}
.c-4{grid-column:span 4}
.gauge{width:150px;height:158px;border-radius:75px 75px 30px 30px;position:relative;overflow:hidden;background:rgba(4,16,27,.55);border:1px solid rgba(95,214,230,.25);box-shadow:inset 0 0 40px rgba(0,0,0,.35)}
.gauge .water{position:absolute;left:0;right:0;bottom:0;height:var(--lvl,0%);background:linear-gradient(180deg,#43c9db,#0B5C66);transition:height .6s}
.gauge .val{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-shadow:0 2px 14px rgba(0,0,0,.45)}
.gauge .val b{font-family:'Sora',system-ui,sans-serif;font-size:40px;font-weight:700;letter-spacing:-.03em;line-height:1}
.gauge .val b small{font-size:20px}.gauge .val>span{font-size:12px;color:#E8FBFD;opacity:.85;margin-top:4px}
.hero-txt .state{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--ink-2);margin-bottom:4px}
.hero-txt .range{font-family:'Sora',system-ui,sans-serif;font-size:46px;font-weight:700;letter-spacing:-.03em;line-height:1}
.hero-txt .range small{font-size:20px;color:var(--ink-2);font-weight:600;margin-left:4px}
.hero-txt .band{color:var(--ink-2);font-size:14px;margin:6px 0 10px}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.carimg{height:88px;margin:-4px 0 0;display:grid;place-items:center}
.carimg canvas{width:100%;max-width:240px;height:88px;display:block}
.carimg .ph{color:var(--ink-3);font-size:13px;text-align:center}
.cname{text-align:center;font-size:11.5px;color:var(--ink-3);margin-bottom:8px;min-height:15px}
.acts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.act{border:1px solid var(--line);background:rgba(255,255,255,.075);color:var(--ink);border-radius:16px;padding:9px 8px;display:flex;flex-direction:row;justify-content:center;align-items:center;gap:8px;font:600 13px 'Manrope',system-ui,sans-serif;cursor:pointer}
.act svg{width:20px;height:20px;color:var(--aqua)}
.act.primary{background:var(--lime);color:var(--lime-ink);border-color:transparent}.act.primary svg{color:var(--lime-ink)}
.act.busy{opacity:.5;pointer-events:none}
.actmsg{margin-top:6px;font-size:12.5px;color:var(--ink-2);min-height:16px}
.t{grid-column:span 2;min-height:96px}
.t .kk{cursor:pointer}
.t.ro .kk{cursor:default}
.t h2 .chev{margin-left:auto;color:var(--aqua);font-size:12px;font-weight:600;text-transform:none;letter-spacing:0}
.t .v{font-family:'Sora',system-ui,sans-serif;font-size:20px;font-weight:700;letter-spacing:-.02em}
.t .v small{font-size:12px;color:var(--ink-2);font-weight:600}
.t .muted{margin-top:3px;font-size:12px;color:var(--ink-2)}
.t .v.ok{color:var(--lime)}.t .v.warn{color:var(--amber)}
.t .auf{display:none;margin-top:10px;border-top:1px solid var(--line);padding-top:10px}
.t.open{grid-column:span 6;background:linear-gradient(135deg,rgba(11,92,102,.30),rgba(10,34,56,.30))}
.t.open .auf{display:block}
.t{align-self:start}
.t.open#t_route,.t.open#t_camping{grid-column:span 10}
#routetile{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 26px;align-items:start}
#routetile>*{grid-column:1}#routetile>#rerg{grid-column:2;grid-row:1/span 14}
#t_camping .auf{column-count:2;column-gap:28px}#t_camping .auf>*{break-inside:avoid}.t.open .chev::after{content:" ▴"}.t:not(.open) .chev::after{content:" ▾"}
.sitzz{display:flex;align-items:center;gap:12px;margin:8px 0}.sitzz>span{min-width:84px;font-weight:700}.btn.big{min-height:52px;font-size:15px;padding:0 20px;border-radius:16px}.seg button{min-height:48px;min-width:56px}
.zwei{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.lab{font-size:11.5px;color:var(--ink-3);font-weight:600;letter-spacing:.04em;text-transform:uppercase;margin:8px 0 4px}
.row2{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:6px 0}
.hint{font-size:12px;color:var(--ink-3)}.warnb{font-size:12px;color:var(--amber)}
.aus{opacity:.5}
input[type=range]{width:100%;accent-color:#B5F23D;padding:0}
.skala{display:flex;justify-content:space-between;font-size:11px;color:var(--ink-3)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}.seg button{padding:8px 14px;font:600 13px 'Manrope',system-ui,sans-serif;border:0;border-right:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}.seg button:last-child{border:0}.seg button[disabled]{opacity:.45;cursor:not-allowed}
.wimg{display:none;position:relative;margin-top:8px;height:96px;border-radius:10px;overflow:hidden;background:#0d2c40}.wimg img{width:100%;height:100%;object-fit:cover;display:block}.wimg span{position:absolute;left:6px;bottom:5px;font-size:11px;font-weight:600;padding:1px 7px;border-radius:99px;background:rgba(5,16,28,.72);color:var(--ink)}
.wm{position:fixed;inset:0;z-index:50;background:rgba(3,10,18,.97);overflow:auto;display:none}.wm.on{display:block}
.wmbox{max-width:980px;margin:0 auto;padding:16px 18px 40px}
.wmtop{display:flex;align-items:center;gap:12px;margin-bottom:12px}.wmtop b{font:700 24px 'Sora',system-ui,sans-serif;flex:1}
.wmbig{border:1px solid var(--line);background:rgba(255,255,255,.1);color:var(--ink);border-radius:16px;padding:14px 20px;font:700 17px 'Manrope',system-ui,sans-serif;cursor:pointer;min-height:56px}
.wmbig.lime{background:var(--lime);color:var(--lime-ink);border-color:transparent}.wmbig[disabled]{opacity:.35;cursor:default}
.wmplay{position:relative;background:#06121d;border-radius:20px;overflow:hidden;aspect-ratio:16/9;display:grid;place-items:center}
.wmplay video,.wmplay img{width:100%;height:100%;object-fit:contain;background:#06121d}
.wmplay .leer{color:var(--ink-2);font-size:18px;text-align:center;padding:20px}
.wmplay .gross{position:absolute;inset:0;display:grid;place-items:center;background:rgba(3,10,18,.25);border:0;cursor:pointer;color:#fff;font-size:72px}
.wminfo{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}.wminfo span{background:rgba(255,255,255,.08);border:1px solid var(--line);border-radius:14px;padding:10px 14px;font:700 17px 'Manrope',system-ui,sans-serif}
.wmnav{display:grid;grid-template-columns:1fr 1.4fr 1fr;gap:10px;margin-bottom:16px}
.wmstrip{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.wmth{border:2px solid transparent;border-radius:16px;overflow:hidden;background:#0d2c40;cursor:pointer;padding:0;color:var(--ink);text-align:left}
.wmth.on{border-color:var(--lime)}.wmth img{width:100%;aspect-ratio:16/10;object-fit:cover;display:block}.wmth div{padding:6px 9px;font-weight:700;font-size:14px}.wmth small{display:block;color:var(--ink-2);font-weight:600}
@media(max-width:620px){.wmnav{grid-template-columns:1fr 1fr}.wmnav .lime{grid-column:1/3;order:-1}}
#t_pos{grid-column:span 4;min-height:300px}#t_pos .minimap{height:220px;border-radius:14px}#t_pos h2 .more{background:none;border:0;cursor:pointer;font:600 13px 'Manrope',system-ui,sans-serif}
.pmg{height:62vh;border-radius:20px;overflow:hidden;background:#0d2c40;display:grid;place-items:center;color:var(--ink-2);font-size:18px;text-align:center;padding:10px}
.minimap{height:46px;border-radius:10px;overflow:hidden;position:relative;background:linear-gradient(135deg,#0d2c40,#103b48);display:grid;place-items:center;color:var(--ink-3);font-size:12px}
.car{width:16px;height:16px;border-radius:50%;background:var(--lime);border:3px solid #0A2238;box-shadow:0 0 0 7px rgba(181,242,61,.18)}
.alle{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;border-style:dashed;text-decoration:none;color:var(--ink)}
.alle .v{font-size:17px}
.mehrmenu{position:absolute;right:26px;top:64px;z-index:50;background:#0e2a40;border:1px solid var(--line);border-radius:14px;padding:8px;min-width:260px;display:none;box-shadow:0 14px 40px rgba(2,10,18,.5)}
.mehrmenu.on{display:block}.mehrmenu a{display:block;padding:10px 12px;border-radius:10px;color:var(--ink);text-decoration:none;font-size:14px;font-weight:600}
.mehrmenu a:hover{background:rgba(95,214,230,.12)}.mehrmenu small{display:block;color:var(--ink-3);font-weight:500;font-size:12px}
.hinweis{margin:0 0 12px;padding:10px 14px;border-radius:12px;border:1px solid rgba(255,194,102,.55);background:rgba(255,194,102,.08);color:var(--amber);font-size:14px;font-weight:600;display:none}
.upd{margin:0 0 12px;padding:10px 14px;border-radius:12px;border:1px solid rgba(95,214,230,.45);background:rgba(95,214,230,.08);font-size:14px;display:none}
.upd a{color:var(--aqua)}
body.datenalt .c-hero,body.datenalt .t{opacity:.55}
/* uebernommene Bausteine der alten Ansicht (Route, Camping) - hier an den Panoptes-Look angepasst */
.auf input,.auf select{background:rgba(4,16,27,.5);border:1px solid var(--line);border-radius:10px;color:var(--ink);padding:9px 11px;font:500 13px 'Manrope',system-ui,sans-serif}
.auf .tile{padding:0;background:none;border:0}
.label2{font-size:11.5px;color:var(--ink-3);font-weight:600;letter-spacing:.04em;margin:10px 0 4px}
@@ALT_CSS@@
@@ANP_CSS@@
@media(max-width:1000px){.c-hero,.c-4{grid-column:span 10}.t,.t.open,.t.open#t_route,.t.open#t_camping{grid-column:span 5}.zwei{grid-template-columns:1fr}#routetile{display:block}#t_camping .auf{column-count:1}}
@media(max-width:620px){.wrap{padding:12px 14px 40px}.c-hero{grid-template-columns:1fr;justify-items:center;text-align:center}.hero-txt .chips{justify-content:center}.t,.t.open,.t.open#t_route,.t.open#t_camping{grid-column:span 10}.top h1{font-size:20px}.act{padding:10px 4px;font-size:12px}}
"""

ICONS = r"""<svg width="0" height="0" style="position:absolute">
 <symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10.5" width="14" height="10" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-flash" viewBox="0 0 24 24"><path d="M13 2 4 14h7l-1 8 9-12h-7z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
 <symbol id="i-pin" viewBox="0 0 24 24"><path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="9.5" r="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-route" viewBox="0 0 24 24"><circle cx="6" cy="18" r="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="18" cy="6" r="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8.5 18H15a3.5 3.5 0 0 0 0-7H9a3.5 3.5 0 0 1 0-7h6.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
 <symbol id="i-snow" viewBox="0 0 24 24"><path d="M12 2v20M3.5 7l17 10M20.5 7l-17 10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
 <symbol id="i-eye" viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-tent" viewBox="0 0 24 24"><path d="M3 20 12 4l9 16zM12 4v16M9 20l3-6 3 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
 <symbol id="i-tyre" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="i-warn" viewBox="0 0 24 24"><path d="M12 3.5 21.5 20h-19zM12 10v5M12 17.5v.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></symbol>
 <symbol id="i-door" viewBox="0 0 24 24"><path d="M6 20V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v14zM14.5 12.5v.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></symbol>
 <symbol id="i-more" viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.6" fill="currentColor"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><circle cx="19" cy="12" r="1.6" fill="currentColor"/></symbol>
</svg>"""


def _tile(k, ico, titel, v_id, m_id, auf, extra_h2=""):
    return ('<section class="card t" id="t_%s"><div class=kk onclick="kachelUm(\'%s\')"><h2><svg><use href="#i-%s"/></svg>%s%s<span class=chev>Bedienen</span></h2>'
            '<div class=v id=%s>–</div><div class=muted id=%s></div></div><div class=auf>%s</div></section>' % (k, k, ico, titel, extra_h2, v_id, m_id, auf))


ROUTE_FALLBACK = '<div class=hint>Route</div>'

BODY_TEIL1 = r"""<body class=mein-auto>
""" + ICONS + r"""
<div class=wrap>
 <div id=updbar class=upd>🔔 <b>Version <span id=updver></span> ist da.</b> <span id=updwas></span> <a id=updlink href="#" target="_blank" rel="noopener">Ansehen →</a></div>
 <header class=top>
  <img class=lg src="/static/panoptes-logo.svg" alt="Panoptes" width=42 height=42>
  <div><h1>Panoptes Cockpit</h1><div class=sub id=sub>–</div></div>
  <div class=grow></div>
  <span class=pill id=pw style="display:none"><i class="dot"></i><span id=pwt>–</span></span>
  <span class=pill id=pq><i class="dot aq"></i><span id=pqt>–</span></span>
  <button type=button class=btn id=refreshbtn onclick="manualRefresh()">↻ Aktualisieren</button>
  @@ANP_KNOPF@@<button type=button class=btn onclick="location.href='/mehr'"><svg width=18 height=18><use href="#i-more"/></svg> Mehr</button>
 </header>

 <div id=altband class=hinweis role=alert></div>
 <div id=wegband class=hinweis role=status></div>
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
  <section class="card c-4">
   <div class=carimg id=car><div class=ph>Auto …</div></div><div class=cname id=cname></div>
   <div class=acts id=acts>
    <button type=button class="act primary" id=a_heat onclick="cmd('heat')" style="display:none"><svg><use href="#i-snow"/></svg>Vorheizen</button>
    <button type=button class=act id=a_lock onclick="zusperren()" style="display:none"><svg><use href="#i-lock"/></svg>Zusperren</button>
    <button type=button class=act id=a_off onclick="cmd('off')" style="display:none"><svg><use href="#i-snow"/></svg>Klima aus</button>
   </div>
   <div style="margin-top:8px"><button type=button class=btn id=a_setup onclick="handyKoppeln()" style="display:none" disabled>🔗 Steuern einrichten</button></div>
   <div class=actmsg id=actmsg></div>
  </section>
"""

ROUTE_AUF = r"""@@ROUTE_HTML@@"""

LADEN_AUF = r"""<div class=zwei><div>
  <div class=lab>Wallbox zu Hause</div><div id=wb_box class=hint>–</div><div id=wb_msg class=hint></div></div>
  <div><div class=lab>Zu Hause laden · Ladeplan</div>
   <div id=lp_box class=hint>–</div>
   <div class=lab>Strompreis</div><div class=hint id=preis_box>aus · Schalter „Ich habe einen dynamischen Stromtarif“ in den Einstellungen.</div></div></div>"""

KLIMA_AUF = r"""<div class=zwei><div>
  <div class=lab>Temperatur</div>
  <input type=range id=temp min=17 max=33 value=25 oninput="tempZeigen()"><div class=skala><span>17 °C</span><span>25 °C (neutral)</span><span>33 °C</span></div>
  <div class=row2><button type=button class="btn lime big" id=k_heat onclick="cmd('heat')">🔥 Heizen auf <span id=temp_v>25</span> °C</button>
   <button type=button class="btn big" id=k_cool onclick="cmd('cool')" style="display:none">❄️ Kühlen</button>
   <button type=button class="btn big" onclick="cmd('off')">⏹ Klima aus</button></div>
  <div class=hint id=k_hint>Nur bei ausgeschaltetem Auto.</div>
  <div id=k_batt style="display:none"><div class=lab>Batterie</div>
   <div class=row2><button type=button class="btn big" onclick="cmd('batt_on')">🔋 Vorheizen</button><button type=button class="btn big" onclick="cmd('batt_off')">Aus</button></div>
   <div class=hint>Im Winter vor dem Schnellladen: eine warme Batterie lädt schneller.</div></div></div>
  <div>
   <div id=seatP style="display:none"><div class=lab>💺 Sitzheizung</div>
    <div class=sitzz><span>Fahrer</span><div class=seg><button type=button onclick="sitz('f',0)">Aus</button><button type=button onclick="sitz('f',1)">1</button><button type=button onclick="sitz('f',2)">2</button></div></div>
    <div class=sitzz><span>Beifahrer</span><div class=seg><button type=button onclick="sitz('b',0)">Aus</button><button type=button onclick="sitz('b',1)">1</button><button type=button onclick="sitz('b',2)">2</button></div></div>
    <div class=hint>Läuft über Panoptes (ab 0.1.21), nur bei ausgeschaltetem Auto.</div></div>
   <div id=seatC style="display:none"><div class=lab>💺 Sitzheizung (beide vorne)</div>
    <div class=seg id=seat><button type=button onclick="cmd('seat_off')">Aus</button><button type=button onclick="cmd('seat_lo')">1</button><button type=button onclick="cmd('seat_hi')">2</button></div></div>
   <div id=ventC style="display:none"><div class=lab>💨 Sitzbelüftung (beide vorne)</div>
    <div class=seg><button type=button onclick="cmd('vent_off')">Aus</button><button type=button onclick="cmd('vent_lo')">1</button><button type=button onclick="cmd('vent_hi')">2</button></div></div>
   <div id=seatN class=warnb style="display:none">Die Sitzheizung braucht „Steuern einrichten“ (Panoptes ab 0.1.21) oder ein BYD-Konto.</div>
  </div></div>"""

CAMPING_AUF = r"""@@CAMPING_HTML@@"""

BODY_TEIL3 = r"""
  <section class="card t ro" id=t_tuer><div class=kk><h2><svg><use href="#i-door"/></svg>Türen &amp; Fenster</h2><div class=v id=t_tuer_v>–</div><div class=muted id=t_tuer2></div></div></section>
  <section class="card t ro" id=t_reifen><div class=kk><h2><svg><use href="#i-tyre"/></svg>Reifen</h2><div class=v id=t_reifen_v>–</div><div class=muted id=t_reifen2></div></div></section>
  <section class="card t ro" id=t_waech onclick="wmAuf()" style="cursor:pointer"><div class=kk style="cursor:pointer"><h2><svg><use href="#i-eye"/></svg>Wächter<span class=more>Ansehen ›</span></h2><div class=v id=t_waech_v>–</div><div class=muted id=t_waech2></div><div class=wimg id=t_waech_img title="Ansehen"></div></div></section>
  <section class="card t ro" id=t_pos><div class=kk><h2><svg><use href="#i-pin"/></svg>Standort<button type=button class=more onclick="posGross()">⤢ Groß ansehen</button></h2><div class=minimap id=map>–</div><div class=muted id=t_pos2></div></div></section>
  <section class="card t ro" id=t_warn><div class=kk><h2><svg><use href="#i-warn"/></svg>Warnungen</h2><div class=v id=t_warn_v>–</div><div class=muted id=t_warn2></div></div></section>
  <a class="card t alle" id=alle href="__PANOPTES_WEB__/" target="_blank" rel="noopener"><div class=v>Alle Funktionen ↗</div><div class=muted>Fahrten, Ladeplan, Aufnahmen, Einstellungen – in Panoptes</div></a>
 </div>
</div>
<div class=wm id=wm onclick="if(event.target===this)wmZu()"><div class=wmbox>
 <div class=wmtop><b id=wm_titel>Wächter</b><button type=button class=wmbig onclick="wmZu()">✕ Schließen</button></div>
 <div class=wmplay id=wm_play></div>
 <div class=wminfo id=wm_info></div>
 <div class=wmnav><button type=button class=wmbig id=wm_neu onclick="wmGeh(-1)">◀ Neuer</button><button type=button class="wmbig lime" id=wm_abs onclick="wmAbspielen()">▶ Abspielen</button><button type=button class=wmbig id=wm_alt onclick="wmGeh(1)">Älter ▶</button></div>
 <div class=wmstrip id=wm_strip></div>
</div></div>
"""

JS = r"""<script>
const KARTEN_STIL='__KARTENSTIL__',EINW={kartenquelle:'keine'};
let S=null,DATA_TS=0,MSGHOLD=0,HANDY_OK,LADEN_ZEILEN=[],TEMP=25,ROUTE_T=0,LB=null;
const el=id=>document.getElementById(id);
const z=(v,d)=>v==null?'–':Number(v).toFixed(d==null?0:d).replace('.',window.__LANG__==='en'?'.':',');
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function unterwegsVerbinden(b){b.disabled=true;const m=el('wegmsg');m.textContent='⏳';
 try{const r=await (await fetch('/bruecke/einrichten',{method:'POST',body:'{}'})).json();m.textContent=(r.ok?'✅ ':'⚠️ ')+__T(r.text||'');if(r.ok)setTimeout(manualRefresh,800);}
 catch(e){m.textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.');}
 b.disabled=false;}
function sprache(){try{localStorage.setItem('evc_lang',window.__LANG__==='en'?'de':'en');}catch(e){}location.reload();return false;}
function modell(m){m=m||'';const lin=((m.match(/\(([^)]*)\)/)||[])[1]||'').trim();let nm=m.replace(/\([^)]*\)/,'').split('/')[0].trim();
 if(/dolphin surf|seagull/i.test(m))nm='BYD Dolphin Surf';return {nm:nm,lin:lin};}
// Bedien-Kacheln: eine offen, die anderen zu
function kachelUm(k){const t=el('t_'+k),war=t.classList.contains('open');
 document.querySelectorAll('.t.open').forEach(o=>o.classList.remove('open'));
 if(typeof campingStopp==='function')campingStopp();
 if(!war){t.classList.add('open');
  if(k==='camping'&&typeof campingLaden==='function')campingLaden(true);
  if(k==='laden'){wbLaden();lpLaden();}
  if(k==='route'&&S&&typeof rSocVomAuto==='function')rSocVomAuto(S);}}
const WZ={scharf:['scharf','ok'],startet:['startet',''],unterdrueckt:['pausiert (sicherer Ort)',''],aus:['aus','warn'],nicht_gewaehlt:['bitte wählen','warn']};
function zeichne(s){
 S=s;DATA_TS=(s._poll_ts?s._poll_ts*1000:Date.now());
 const en=window.__LANG__==='en',mo=modell(s.pan_modell||s.model);
 el('sub').textContent=[mo.nm+(mo.lin?' ('+mo.lin+')':''),__T('Daten von')+' '+new Date(DATA_TS).toLocaleTimeString(en?'en-GB':'de-AT',{hour:'2-digit',minute:'2-digit'}),
  s.gear==='P'?__T('geparkt'):(s.gear?__T('Gang')+' '+s.gear:'')].filter(Boolean).join(' · ');
 const wz=WZ[s.waechter_zustand],pw=el('pw');
 if(s.panoptes_an){pw.style.display='';el('pwt').textContent=__T('Wächter')+' '+(wz?__T(wz[0]):'–');pw.querySelector('.dot').className='dot '+(wz&&wz[1]||'');}else pw.style.display='none';
 const wb=el('wegband'),wh=s.bruecke_hinweis;
 if(wh==='einrichten'||wh==='neu'){wb.style.display='block';wb.innerHTML=(wh==='neu'?esc(__T('Die Verbindung unterwegs gilt nicht mehr.')):esc(__T('Damit das Cockpit dein Auto auch unterwegs erreicht, einmal verbinden.')))+' <button type=button class="btn lime" onclick="unterwegsVerbinden(this)">'+esc(__T(wh==='neu'?'Neu verbinden':'Unterwegs verbinden'))+'</button><span id=wegmsg style="margin-left:10px"></span>';}else wb.style.display='none';
 el('pqt').textContent=(s.quelle||'–')+(s.weg?' · '+__T(s.weg==='bruecke'?'über Internet':'direkt'):'');
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
 // Laden
 LADEN_ZEILEN=[];
 if(s.charging==='ON'){el('t_laden_v').textContent=__T('lädt')+(s.charge_power!=null?' · '+z(Math.abs(s.charge_power),1)+' kW':'');
  LADEN_ZEILEN.push(s.charge_remaining?__T('Restzeit')+' '+s.charge_remaining:__T('Restzeit meldet Panoptes gerade nicht'));}
 else el('t_laden_v').textContent=lad;
 el('t_laden_m').innerHTML=LADEN_ZEILEN.map(esc).join('<br>');
 // Klima
 el('t_klima_v').textContent=s.klima_on==='ON'?__T('an'):s.klima_on==='OFF'?__T('aus'):__T('unbekannt');
 el('t_klima_m').textContent=[s.temp_out!=null?__T('Außen')+' '+z(s.temp_out,0)+' °C':'',__T('Vorheizen auf')+' '+TEMP+' °C'].filter(Boolean).join(' · ');
 // Camping
 const cp=s.camping||{};el('t_camping').style.display=cp.da?'':'none';
 if(cp.da){el('t_camping_v').textContent=cp.aktiv?__T('läuft'):__T('aus');}
 // Route (Zusammenfassung)
 routeLaden();
 // Tueren, Reifen, Waechter, Standort, Warnungen
 const tz=s.doors_open==='ON'?__T('offen'):s.doors_open==='OFF'?__T('alle zu'):'–';
 el('t_tuer_v').textContent=tz;el('t_tuer_v').className='v '+(s.doors_open==='ON'?'warn':'');
 el('t_tuer2').textContent=s.windows_open==='ON'?__T('Fenster offen'):s.windows_open==='OFF'?__T('Fenster zu'):__T('Fenster meldet Panoptes gerade nicht');
 const ty=['tyre_fl','tyre_fr','tyre_rl','tyre_rr'].map(k=>s[k]).filter(v=>v!=null);
 el('t_reifen_v').innerHTML=ty.length?z(Math.min.apply(null,ty),0)+' <small>kPa</small>':'–';
 el('t_reifen2').textContent=s.reifen&&s.reifen.stufe?(s.reifen.stufe==='gruen'?__T('in Ordnung'):__T('bitte prüfen')):(ty.length?__T('kleinster Wert aller vier Reifen'):'');
 el('t_waech_v').textContent=wz?__T(wz[0]):(s.panoptes_an?'–':__T('nicht verbunden'));el('t_waech_v').className='v '+(wz&&wz[1]||'');
 const w=s.waechter_letzt;el('t_waech2').textContent=w&&w.timestamp?__T('Letztes Ereignis')+' '+rel(w.timestamp):__T('noch kein Ereignis');
 const wi=el('t_waech_img');if(s.weg==='bruecke')wi.style.display='none';else if(w&&w.id&&w.available){wi.style.display='block';if(wi.dataset.id!==w.id){wi.dataset.id=w.id;wi.innerHTML='<img alt="" loading=lazy src="/waechter/bild/'+esc(w.id)+'" onerror="this.remove()"><span>'+esc(rel(w.timestamp))+'</span>';}else{const sp=wi.querySelector('span');if(sp)sp.textContent=rel(w.timestamp);}}else wi.style.display='none';
 el('t_pos2').textContent=s.latitude!=null?z(s.latitude,4)+', '+z(s.longitude,4):__T('Standort unbekannt');
 karte(s);
 const W=[];
 if(s.reifen&&s.reifen.stufe&&s.reifen.stufe!=='gruen')W.push(__T('Reifendruck prüfen'));
 if(s.v12!=null&&s.v12<11.8)W.push(__T('12-V-Batterie schwach'));
 if(s._err)W.push(s._err);if(s.geheim_warnung)W.push(s.geheim_warnung);
 if(s.panoptes_an&&s.panoptes_erreichbar===false)W.push(__T('Panoptes antwortet gerade nicht'));
 el('t_warn_v').textContent=W.length?W.length+' '+__T(W.length>1?'Hinweise':'Hinweis'):__T('keine');el('t_warn_v').className='v '+(W.length?'warn':'');
 el('t_warn2').textContent=W.length?W[0]:'';
 // Schnellknoepfe + Klima-Details
 const F=s.features||{},hy=!!s.handy_an,sicht=(id,an)=>{el(id).style.display=an?'':'none';};
 sicht('a_heat',F.klima||hy);sicht('a_off',F.klima||hy);sicht('a_lock',F.lock||hy);sicht('a_setup',!!s.panoptes_an&&!hy);
 sicht('seatP',hy);sicht('seatC',!hy&&!!F.seat);sicht('ventC',!hy&&!!F.seatvent);sicht('seatN',!hy&&!F.seat);sicht('k_cool',!hy&&!!F.klima);sicht('k_batt',!hy&&!!F.batt);
 el('k_hint').textContent=hy?__T('10 Minuten, nur bei ausgeschaltetem Auto. Läuft über Panoptes.'):(F.klima?__T('Über die BYD-Cloud fest höchstens 31 °C, nur bei ausgeschaltetem Auto.'):__T('Zum Vorheizen erst „Steuern einrichten“ (oben).'));
 el('k_heat').disabled=!(F.klima||hy);
 if(s.panoptes_an&&!hy&&HANDY_OK===undefined){HANDY_OK=null;fetch('/panoptes/handy/pruefen',{method:'POST',body:'{}'}).then(r=>r.json()).then(r=>{HANDY_OK=r.vorhanden;handyKnopf();}).catch(()=>{HANDY_OK=undefined;});}
 handyKnopf();
 if(typeof rSocVomAuto==='function')rSocVomAuto(s);
 if(s._msg&&Date.now()>MSGHOLD)el('actmsg').textContent=s._msg;
 el('alle').style.display=s.panoptes_web?'':'none';
 if(s.update){el('updbar').style.display='block';el('updver').textContent=s.update.version;el('updwas').textContent=s.update.was_neu||'';el('updlink').href=s.update.url;}
 const pb=el('preis_box');if(!s.show_price&&s.tarif_art&&s.tarif_art!=='boerse')pb.textContent=__T(s.tarif_art==='boerse_aus'?'Der Börsentarif ist in Panoptes ausgeschaltet – Börsenpreise werden nicht angezeigt.':'Fester Strompreis laut Panoptes – Börsenpreise werden nicht angezeigt.');
 if(s.show_price&&s.price_now!=null)pb.textContent=__T('jetzt')+' '+z(s.price_now,1)+' ct/kWh · '+__T('günstigste Stunde')+' '+(s.price_cheap_time||'–')+' ('+z(s.price_cheap_ct,1)+' ct)';
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
// Auto-Bild: Modell aus dem Panoptes-Katalog (3D, nur mit Einwilligung), sonst Name; keine frei waehlbare Farbe (Auto ist die Quelle)
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
  const gro=()=>{const w=cv.clientWidth||240,h=cv.clientHeight||88;r.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();};gro();window.addEventListener('resize',gro);
  r.setAnimationLoop(()=>{if(document.hidden)return;pivot.rotation.y+=0.004;r.render(sc,cam);});
  el('cname').innerHTML=esc(modell((S&&(S.pan_modell||S.model))||'').nm||i.name||'')+(i.lackName?' · '+esc(i.lackName):'')+' · 3D: '+esc(i.author||'')+(i.license?', '+esc(String(i.license).replace('-',' ').replace('-',' ')):'')+' · <a href="'+esc(i.lizenzen||'#')+'" target=_blank rel=noopener style="color:inherit" title="'+esc(i.attribution||'')+'">'+esc(__T('Lizenz'))+'</a>';
  AUTO3D.ok=true;
 }catch(e){AUTO3D.ok=false;el('car').innerHTML='<div class=ph>🚗 '+esc(modell(S&&S.model).nm)+'</div>';el('cname').textContent=modell(S&&S.model).nm;}}
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
   m.textContent='';MAPOBJ=new maplibregl.Map({container:'map',style:KARTEN_STIL,center:[s.longitude,s.latitude],zoom:13,interactive:true,attributionControl:false});MAPOBJ.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
   const d=document.createElement('div');d.className='car';MAPOBJ._mk=new maplibregl.Marker({element:d}).setLngLat([s.longitude,s.latitude]).addTo(MAPOBJ);
  }else if(MAPOBJ.setCenter){MAPOBJ.setCenter([s.longitude,s.latitude]);MAPOBJ._mk.setLngLat([s.longitude,s.latitude]);}
 }catch(e){MAPOBJ=0;m.textContent='📍';}}
// Schnellknoepfe: gleiche geprueften Wege wie bisher (/cmd), Panoptes-Weg wenn mit "Steuern einrichten" gekoppelt
function zusperren(){if(confirm(__T('Auto wirklich zusperren?')))cmd('lock');}
function tempZeigen(){TEMP=parseInt(el('temp').value,10)||25;el('temp_v').textContent=TEMP;if(S)el('t_klima_m').textContent=[S.temp_out!=null?__T('Außen')+' '+z(S.temp_out,0)+' °C':'',__T('Vorheizen auf')+' '+TEMP+' °C'].filter(Boolean).join(' · ');}
const SITZ={f:'Fahrer',b:'Beifahrer'};
function sitz(w,n){if(!confirm(__T('Sitzheizung')+' '+__T(SITZ[w])+' → '+(n?__T('Stufe')+' '+n:__T('aus'))+'?'))return;cmd('sitz_'+w+'_'+n);}
async function cmd(a){
 const m=el('actmsg');MSGHOLD=Date.now()+6000;m.textContent='⏳ '+__T('Sende …');
 const bs=[...document.querySelectorAll('.act')];bs.forEach(b=>b.classList.add('busy'));
 try{const r=await fetch('/cmd?a='+encodeURIComponent(a)+(a==='heat'?'&t='+TEMP:''),{method:'POST'});const d=await r.json();if(!r.ok||!d.ok)throw Error(d.error||__T('Befehl abgelehnt'));
  m.textContent='✓ '+__T('Befehl angenommen · Fahrzeugstatus wird aktualisiert');}
 catch(ex){m.textContent='⚠️ '+ex.message;}
 finally{bs.forEach(b=>b.classList.remove('busy'));}
 setTimeout(()=>{MSGHOLD=0;manualRefresh();},2500);}
function handyKnopf(){const b=el('a_setup');if(!b)return;const alt=HANDY_OK===false;b.disabled=false;b.style.opacity=alt?'.6':'';
 b.title=alt?__T('Braucht Panoptes ab 0.1.19.1'):__T('Einmal koppeln, damit das Cockpit über Panoptes zusperren und vorheizen darf.');}
async function handyKoppeln(){
 const m=el('actmsg');MSGHOLD=Date.now()+300000;m.textContent='⏳ …';
 try{const r=await (await fetch('/panoptes/handy/anfrage',{method:'POST',body:'{}'})).json();
  if(!r.ok){m.textContent='⚠️ '+__T(r.error||'Panoptes antwortet nicht. Bitte noch einmal versuchen.');return;}
  m.textContent='🔗 '+__T('In Panoptes (Telegram, Web oder Auto-Display) erlauben. Prüfzahl:')+' '+r.pruefzahl;
  for(let i=0;i<65;i++){await new Promise(zz=>setTimeout(zz,2000));
   const s=await (await fetch('/panoptes/handy/status',{method:'POST',body:'{}'})).json();
   if(s.status==='erlaubt'){m.textContent='✅ '+__T('Gekoppelt. Zusperren und Vorheizen gehen jetzt über Panoptes.');MSGHOLD=0;manualRefresh();return;}
   if(s.status!=='wartet'){m.textContent='⚠️ '+__T(s.error||'Die Kopplung hat nicht geklappt. Bitte noch einmal von vorn.');return;}}
  m.textContent='⚠️ '+__T('Keine Bestätigung in Panoptes. Bitte noch einmal von vorn.');
 }catch(e){m.textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.')+' ('+e+')';}}
// Wallbox (Laden-Kachel): Steuern nur mit Freigabe, bei jedem Klick Rueckfrage (serverseitig erzwungen, wie unter Mehr -> Wallbox)
const WB_FEHLER={nicht_eingerichtet:'Noch nicht eingerichtet',nicht_erreichbar:'Wallbox bzw. Home Assistant nicht erreichbar',anmeldung:'Home Assistant: bitte anmelden (Einstellungen)',
 nicht_unterstuetzt:'Das kann diese Wallbox nicht',wert_ungueltig:'Wert außerhalb des erlaubten Bereichs',nicht_freigegeben:'Steuern ist für diesen Ladepunkt nicht freigegeben',
 ha_nicht_erreichbar:'Home Assistant erreicht die Wallbox gerade nicht',bruecke_gesperrt:'Steuerung an der Wallbox-Brücke gesperrt – bitte dort „Steuern erlaubt“ einschalten',
 keine_wallbox:'Kein Ladepunkt einer Wallbox',tuya_zuordnung_fehlt:'Modell nicht erkannt – erst unter Mehr → Wallbox einrichten'};
async function wbPost(url,b){const o=x=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(x)});
 let r=await fetch(url,o(b)),d=await r.json();
 if(r.status===409&&d.grund==='bestaetigung_noetig'){if(!confirm(__T(d.frage&&d.frage.text||'Wirklich?')))return null;
  r=await fetch(url,o(Object.assign({},b,{bestaetigung:d.bestaetigung})));d=await r.json();}
 return d;}
const WB_QUELLE={ha:'Home Assistant',tuya:'Tuya (lokal)'};
async function wbLaden(){const box=el('wb_box');
 try{const d=await (await fetch('/wallbox/status',{cache:'no-store'})).json();
  const lp=d&&d.ok&&d.quelle&&d.ladepunkte&&d.ladepunkte[0];LB=lp||null;
  if(!lp){box.innerHTML=esc(__T('Keine Wallbox eingerichtet.'))+' <a href="/energie" style="color:var(--aqua)">'+esc(__T('Einrichten'))+'</a>';return lp;}
  const f=lp.faehigkeiten||{},kw=lp.leistungW!=null?z(Math.round(lp.leistungW/100)/10,1)+' kW':'–';
  let h='<div style="color:var(--ink);font-size:14px;margin-bottom:6px"><b>'+esc(lp.titel||'Wallbox')+'</b> · '+esc(lp.erreichbar===false?__T('nicht erreichbar'):lp.laedt?__T('lädt'):__T('bereit'))+' · '+kw+(lp.stromA!=null?' · '+lp.stromA+' A':'')+(typeof lp.zielSoc==='number'?' · '+__T('Ziel')+' '+lp.zielSoc+' %':'')+'</div>';
  if(lp.erreichbar===false){h+='<div class=warnb>'+esc(__T(WB_FEHLER.ha_nicht_erreichbar))+'</div>';}
  else if(f.gesperrt){h+='<div class=warnb>🔒 '+esc(__T(WB_FEHLER.bruecke_gesperrt))+'</div>';}
  else if(!(f.modus||[]).length&&!f.strom){h+='<div class=hint>'+esc(__T('Nur Anzeige – diese Wallbox lässt sich nicht steuern.'))+'</div>';}
  else if(!lp.steuernFrei){h+='<div class=row2><button type=button class=btn onclick="wbTun(\'frei\')">⚙ '+esc(__T('Steuern erlauben'))+'</button></div><div class=hint>'+esc(__T('Danach fragt das Cockpit bei jedem Klick noch einmal nach.'))+'</div>';}
  else{
   h+='<div class=row2>';
   if((f.modus||[]).includes('sofort'))h+='<button type=button class="btn lime" onclick="wbTun(\'modus\',\'sofort\')">▶ '+esc(__T('Laden starten'))+'</button>';
   if((f.modus||[]).includes('aus'))h+='<button type=button class=btn onclick="wbTun(\'modus\',\'aus\')">■ '+esc(__T('Stoppen'))+'</button>';
   if(f.strom){const st=f.strom.stufen||Array.from({length:f.strom.max-f.strom.min+1},(_,k)=>f.strom.min+k);
    h+='<select id=wb_strom onchange="wbTun(\'strom\',+this.value)" aria-label="'+esc(__T('Ladestrom'))+'">'+st.map(i=>'<option value="'+i+'"'+(lp.stromA===i?' selected':'')+'>'+i+' A</option>').join('')+'</select>';}
   h+='<button type=button class=btn onclick="wbTun(\'sperren\')">'+esc(__T('Steuern aus'))+'</button></div><div class=hint>'+esc(__T('Bei jedem Klick fragt das Cockpit noch einmal nach.'))+'</div>';}
  box.innerHTML=h;return lp;
 }catch(e){box.textContent='⚠️ '+e.message;}}
async function wbTun(art,wert){const m=el('wb_msg');if(!LB)return;
 try{let r;
  if(art==='frei'||art==='sperren')r=await wbPost('/wallbox/freigabe',{ladepunkt:LB.id,an:art==='frei'});
  else{m.textContent='⏳ '+__T('Sende an die Wallbox …');r=await wbPost('/wallbox/steuern',{ladepunkt:LB.id,aktion:art,wert:wert});}
  if(!r){m.textContent=__T('Abgebrochen');return wbLaden();}
  if(!r.ok){m.textContent='⚠️ '+__T(WB_FEHLER[r.grund]||r.grund||'Fehler');return wbLaden();}
  if('uebernommen' in r)m.textContent=r.uebernommen===true?'✅ '+__T('Die Wallbox hat übernommen'):r.uebernommen===null?'ℹ️ '+__T('Befehl gesendet – ob die Wallbox ihn umgesetzt hat, meldet sie nicht zurück.'):'⚠️ '+__T('Die Wallbox hat den Wert auch nach 25 Sekunden nicht übernommen. Ist das Auto angesteckt? Bitte kurz warten und noch einmal versuchen.');
  else m.textContent='';
  setTimeout(()=>{wbLaden();load();},800);
 }catch(e){m.textContent='⚠️ '+e.message;}}
// Route: Zusammenfassung der im Planer bereitliegenden Route (Detail-Funktionen stammen aus der alten Ansicht)
async function routeLaden(){if(Date.now()-ROUTE_T<30000)return;ROUTE_T=Date.now();
 try{const d=await (await fetch('/planer/route',{cache:'no-store'})).json();
  if(!d.an){el('t_route_v').textContent=__T('nicht verbunden');el('t_route_m').textContent=__T('Mit dem Routenplaner verbinden: Einstellungen');return;}
  if(!d.route){el('t_route_v').textContent=__T('Ziel eingeben');el('t_route_m').textContent=__T('Noch keine Route im Auto.');return;}
  const r=d.route,h=r.minuten?Math.floor(r.minuten/60)+' h '+String(r.minuten%60).padStart(2,'0')+' min':'';
  el('t_route_v').textContent=r.titel||__T('Route');
  el('t_route_m').textContent=[r.km?Math.round(r.km)+' km':'',h,r.stopps+' '+__T(r.stopps===1?'Ladestopp':'Ladestopps'),r.soc_ankunft!=null?__T('Ankunft')+' '+r.soc_ankunft+' %':''].filter(Boolean).join(' · ');
 }catch(e){}}
// @@ROUTE_JS@@
// @@CAMPING_JS@@
// @@ANP_JS@@
function rKarte(){}   // keine Karte in der Kachel (Ladestopps als Liste)
// Waechter-Fenster: Ereignis im Cockpit ansehen (nur lesend aus Panoptes; kein Sprung zu einer anderen Seite)
let WM={l:[],i:0,offen:false,fehler:''};
const WM_ART={sentry:['👁','Wächter hat etwas bemerkt'],proximity:['🚶','Jemand war nah am Auto']};
const WM_WER={person:['🧍','Person'],car:['🚗','Auto'],vehicle:['🚗','Fahrzeug'],truck:['🚚','Lkw'],bike:['🚲','Fahrrad'],bicycle:['🚲','Fahrrad'],motorcycle:['🏍','Motorrad'],animal:['🐾','Tier'],dog:['🐕','Hund'],cat:['🐈','Katze']};
function wmZeit(ts){const d=new Date(ts),h=new Date(),en=window.__LANG__==='en',t0=new Date(h.getFullYear(),h.getMonth(),h.getDate()).getTime();
 const uhr=d.toLocaleTimeString(en?'en-GB':'de-AT',{hour:'2-digit',minute:'2-digit'});
 if(ts>=t0+172800000)return d.toLocaleDateString(en?'en-GB':'de-AT',{day:'2-digit',month:'2-digit'})+' '+uhr;
 if(ts>=t0+86400000)return __T('Morgen')+' '+uhr;
 if(ts>=t0)return __T('Heute')+' '+uhr;if(ts>=t0-86400000)return __T('Gestern')+' '+uhr;
 return d.toLocaleDateString(en?'en-GB':'de-AT',{day:'2-digit',month:'2-digit'})+' '+uhr;}
function wmOrt(a){const p=a.place;return typeof p==='string'?p:(p&&(p.short||p.medium))||'';}
function wmWer(a){const s=new Set();(a.actors||[]).forEach(x=>{const k=String((x&&x.class)||x||'').toLowerCase();if(WM_WER[k])s.add(k);});
 if(!s.size){if(a.personCount>0)s.add('person');if(a.vehicleCount>0)s.add('vehicle');if(a.bikeCount>0)s.add('bike');if(a.animalCount>0)s.add('animal');}
 return [...s];}
async function wmLaden(){
 WM.fehler='';
 try{const r=await Promise.all(['sentry','proximity'].map(a=>fetch('/waechter/liste?art='+a,{cache:'no-store'}).then(x=>x.json())));
  let l=[];r.forEach(d=>{if(d&&d.ok)l=l.concat(d.aufnahmen||[]);else if(d&&d.grund==='zu_alt')WM.fehler='Dein Panoptes kann die Aufnahmen noch nicht zeigen (ab Version 0.1.9).';else if(d&&d.error)WM.fehler=d.error;});
  l.sort((a,b)=>(b.timestamp||0)-(a.timestamp||0));WM.l=l.slice(0,12);
 }catch(e){WM.fehler='Panoptes antwortet gerade nicht.';WM.l=[];}}
async function wmAuf(){
 const w=el('wm');w.classList.add('on');WM.offen=true;document.body.style.overflow='hidden';
 el('wm_titel').textContent=__T('Wächter');el('wm_play').innerHTML='<div class=leer>⏳</div>';
 await wmLaden();WM.i=0;wmZeige();}
function wmZu(){el('wm').classList.remove('on');WM.offen=false;document.body.style.overflow='';const v=el('wm_play').querySelector('video');if(v){v.pause();v.removeAttribute('src');v.load();}}
function wmGeh(d){const n=WM.i+d;if(n<0||n>=WM.l.length)return;WM.i=n;wmZeige();}
function wmZeige(){
 const a=WM.l[WM.i],pl=el('wm_play'),inf=el('wm_info');
 el('wm_neu').disabled=WM.i<=0;el('wm_alt').disabled=WM.i>=WM.l.length-1;el('wm_abs').disabled=!a||!a.available||!!(S&&S.weg==='bruecke');
 if(!a){pl.innerHTML='<div class=leer>'+esc(__T(WM.fehler||'Noch kein Ereignis.'))+'</div>';inf.innerHTML='';el('wm_strip').innerHTML='';return;}
 const art=WM_ART[a.type]||['🎥',a.type||''];
 const bruecke=!!(S&&S.weg==='bruecke');
 pl.innerHTML=bruecke?'<div class=leer>'+esc(__T('Unterwegs gibt es noch keine Bilder und Videos. Zu Hause im WLAN geht es.'))+'</div>':a.available?'<img alt="" src="/waechter/bild/'+esc(a.id)+'"><button type=button class=gross onclick="wmAbspielen()" aria-label="'+esc(__T('Abspielen'))+'">▶</button>':'<div class=leer>'+esc(__T('Datenträger fehlt – die Aufnahme ist gerade nicht lesbar.'))+'</div>';
 const ch=[ '<span>'+art[0]+' '+esc(__T(art[1]))+'</span>','<span>🕒 '+esc(wmZeit(a.timestamp))+' · '+esc(rel(a.timestamp))+'</span>'];
 wmWer(a).forEach(k=>ch.push('<span>'+WM_WER[k][0]+' '+esc(__T(WM_WER[k][1]))+'</span>'));
 if(a.cameraId!=null)ch.push('<span>📷 '+esc(__T('Kamera'))+' '+(Number(a.cameraId)+1)+'</span>');
 const o=wmOrt(a);if(o)ch.push('<span>📍 '+esc(o)+'</span>');
 inf.innerHTML=ch.join('');
 el('wm_strip').innerHTML=WM.l.map((x,k)=>'<button type=button class="wmth'+(k===WM.i?' on':'')+'" onclick="WM.i='+k+';wmZeige()">'+(x.available?'<img loading=lazy alt="" src="/waechter/bild/'+esc(x.id)+'">':'')+'<div>'+(WM_ART[x.type]||['🎥'])[0]+' '+esc(wmZeit(x.timestamp))+'<small>'+esc(rel(x.timestamp))+'</small></div></button>').join('');}
function wmAbspielen(){const a=WM.l[WM.i];if(!a||!a.available)return;const pl=el('wm_play');
 pl.innerHTML='<video controls autoplay playsinline src="/waechter/clip/'+esc(a.id)+'" poster="/waechter/bild/'+esc(a.id)+'"></video>';
 const v=pl.querySelector('video');v.onerror=()=>{pl.innerHTML='<div class=leer>'+esc(__T('Das Video lässt sich gerade nicht laden. Bitte später noch einmal.'))+'</div>';};}
document.addEventListener('keydown',e=>{if(!WM.offen)return;if(e.key==='Escape')wmZu();else if(e.key==='ArrowLeft')wmGeh(-1);else if(e.key==='ArrowRight')wmGeh(1);});
// Ladeplan (aus Panoptes, nur lesen). "zu alt" nur bei 404; 401/403 = Zugriff fehlt
async function lpLaden(){const b=el('lp_box');if(!b)return;
 try{const d=await (await fetch('/panoptes/ladeplan',{cache:'no-store'})).json();
  if(!d.ok){const T={nicht_gekoppelt:'Erst mit Panoptes verbinden (Mehr → Einstellungen).',zu_alt:'Dein Panoptes kann den Ladeplan noch nicht (ab Version 0.1.20).',
    zugriff:'Panoptes erlaubt dem Cockpit das Lesen des Ladeplans nicht. Bitte das Cockpit unter Mehr → Einstellungen neu mit Panoptes verbinden.',fehler:'Panoptes antwortet gerade nicht.'};
   b.innerHTML='<div class=warnb>'+esc(__T(T[d.grund]||T.fehler))+'</div>'+(d.grund==='zugriff'||d.grund==='nicht_gekoppelt'?'<div class=row2 style="margin-top:8px"><a class="btn lime" href="/setup">🔗 '+esc(__T('Mit Panoptes verbinden'))+'</a></div>':'');return;}
  const e=d.einstellungen||{},z0=d.zustand||{},ab=e.abfahrt||{},wt=ab.werktag||{},we=ab.wochenende||{};
  const an=e.modus&&e.modus!=='aus',zeile=[];
  zeile.push('<span class="pill '+(an?'':'aus')+'"><i class="dot '+(an?'ok':'')+'"></i>'+esc(__T('Ladeplan'))+': '+esc(an?__T('an'):__T('aus'))+'</span>');
  const li=[];
  if(wt.an)li.push('🌅 '+esc(__T('Mo–Fr fertig um'))+' '+esc(wt.zeit)+' · '+esc(wt.ziel)+' %');
  if(we.an)li.push('🌅 '+esc(__T('Sa/So fertig um'))+' '+esc(we.zeit)+' · '+esc(we.ziel)+' %');
  if(e.mindestladung!=null)li.push('🔋 '+esc(__T('Mindestens'))+' '+esc(e.mindestladung)+' %');
  const f=(e.fenster||[])[0];if(f)li.push('🕒 '+esc(__T('Laden zwischen'))+' '+esc(f.von)+' '+esc(__T('und'))+' '+esc(f.bis));
  if(z0.abfahrt&&z0.abfahrt.zeit)li.push('🚗 '+esc(__T('Nächste Abfahrt'))+': '+esc(wmZeit(z0.abfahrt.zeit))+' · '+esc(z0.abfahrt.ziel)+' %');
  const t=d.tarif||{};li.push('💶 '+esc(__T('Strompreis'))+': '+esc(t.art==='fest'?__T('fester Preis'):t.tarifName||t.art||'–'));
  b.innerHTML='<div class=row2>'+zeile.join('')+'</div><div style="margin-top:8px;line-height:1.8">'+li.join('<br>')+'</div><div class=hint style="margin-top:6px">'+esc(__T('Einstellen kommt ins Cockpit; bis dahin im Auto oder in Panoptes.'))+'</div>';
 }catch(x){b.innerHTML='<div class=warnb>'+esc(__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.'))+'</div>';}}
// Standort gross: eigene Karte im Cockpit (Fenster), kein Sprung woanders
let BIGMAP=null;
function posGross(){
 const s=S||{};let w=el('pm');
 if(!w){w=document.createElement('div');w.id='pm';w.className='wm';w.onclick=e=>{if(e.target===w)posZu();};
  w.innerHTML='<div class=wmbox><div class=wmtop><b>'+esc(__T('Standort'))+'</b><button type=button class=wmbig onclick="posZu()">✕ '+esc(__T('Schließen'))+'</button></div><div class=pmg id=pm_karte></div><div class=wminfo id=pm_info></div></div>';
  document.body.appendChild(w);}
 w.classList.add('on');document.body.style.overflow='hidden';
 const k=el('pm_karte'),i=el('pm_info');
 if(s.latitude==null){k.textContent=__T('Standort unbekannt');i.innerHTML='';return;}
 i.innerHTML='<span>📍 '+esc(z(s.latitude,5))+', '+esc(z(s.longitude,5))+'</span>';
 if(!KARTEN_STIL||!window.maplibregl){k.textContent=__T('Die Karte ist aus. Unter Mehr → Einstellungen kannst du sie einschalten.');return;}
 k.textContent='';
 try{if(BIGMAP){BIGMAP.remove();BIGMAP=null;}
  BIGMAP=new maplibregl.Map({container:'pm_karte',style:KARTEN_STIL,center:[s.longitude,s.latitude],zoom:15,attributionControl:false});
  BIGMAP.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
  const d=document.createElement('div');d.className='car';new maplibregl.Marker({element:d}).setLngLat([s.longitude,s.latitude]).addTo(BIGMAP);
 }catch(e){k.textContent='📍 '+z(s.latitude,5)+', '+z(s.longitude,5);}}
function posZu(){const w=el('pm');if(w)w.classList.remove('on');document.body.style.overflow='';if(BIGMAP){try{BIGMAP.remove();}catch(e){}BIGMAP=null;}}
document.addEventListener('keydown',e=>{if(e.key==='Escape')posZu();});
// Laden: Daten holen
let TIMER=null;
async function load(){
 clearTimeout(TIMER);let t=60000;
 try{const s=await (await fetch('/data',{cache:'no-store'})).json();zeichne(s);auto3d(s);
  if(s.abfrage&&s.abfrage.takt_s)t=Math.min(60000,Math.max(5000,s.abfrage.takt_s*500));}catch(e){}
 try{const w=await (await fetch('/wallbox/status',{cache:'no-store'})).json();const lp=w&&w.ok&&w.quelle&&w.ladepunkte&&w.ladepunkte[0];
  const wt=el('t_wallbox');if(lp){wt.style.display='';const kw0=lp.leistungW!=null?z(Math.round(lp.leistungW/100)/10,1)+' kW':'–';
   el('t_wallbox_v').textContent=lp.erreichbar===false?__T('nicht erreichbar'):lp.laedt?__T('lädt')+' · '+kw0:__T('bereit');el('t_wallbox_v').className='v '+(lp.laedt?'ok':lp.erreichbar===false?'warn':'');
   el('t_wallbox_m').textContent=[lp.titel||'Wallbox',lp.stromA!=null?lp.stromA+' A':'',__T('Quelle')+': '+(WB_QUELLE[w.quelle]||w.quelle||'–')].filter(Boolean).join(' · ');}
  else if(w&&w.quelle&&w.ok===false){wt.style.display='';el('t_wallbox_v').textContent=__T('nicht erreichbar');el('t_wallbox_v').className='v warn';el('t_wallbox_m').textContent=__T('Quelle')+': '+(WB_QUELLE[w.quelle]||w.quelle);}else wt.style.display='none';
  if(lp&&S){const k=lp.leistungW!=null?z(Math.round(lp.leistungW/100)/10,1)+' kW':'–';
   const zl=LADEN_ZEILEN.map(esc);
   if(S.charging==='ON'&&typeof lp.zielSoc==='number')zl.push(esc(__T('Ziel'))+' '+lp.zielSoc+' %');
   zl.push('Wallbox: '+esc(lp.erreichbar===false?__T('nicht erreichbar'):lp.laedt?__T('lädt'):__T('bereit'))+' · '+k+(lp.stromA!=null?' · '+lp.stromA+' A':''));
   if(lp.faehigkeiten&&lp.faehigkeiten.gesperrt)zl.push('🔒 '+esc(__T('Steuerung an der Wallbox-Brücke gesperrt')));
   el('t_laden_m').innerHTML=zl.join('<br>');
   if(el('t_laden').classList.contains('open')&&!document.querySelector('#wb_box select:focus'))wbLaden();}}catch(e){}
 TIMER=setTimeout(load,t);}
function manualRefresh(){clearTimeout(TIMER);fetch('/jetzt',{method:'POST'}).catch(function(){}).then(function(){setTimeout(load,1500);});}
document.addEventListener('visibilitychange',()=>{if(!document.hidden){clearTimeout(TIMER);load();}else clearTimeout(TIMER);});
load();
</script></body>"""

HEAD = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Panoptes Cockpit</title>
<meta name=evc-ohne-sprachfeld content=1>
<script type=importmap>{"imports":{"three":"/static/three/three.module.min.js"}}</script>
<style>@@CSS@@</style></head>"""


def _teil(cockpit, anfang, ende):
    """Text zwischen zwei Markern der alten Ansicht (leer, wenn die alte Ansicht nicht uebergeben wurde)."""
    if not cockpit:
        return ""
    a = cockpit.find(anfang)
    b = cockpit.find(ende, a + 1) if a >= 0 else -1
    return cockpit[a:b] if a >= 0 and b > a else ""


def uebernommen(cockpit):
    """(CSS, Route-HTML, Route-JS, Camping-HTML, Camping-JS) aus der alten Ansicht."""
    css = "\n".join(l for l in (cockpit or "").splitlines()
                    if re.match(r"\.(rrow|rfeld|rvor|rrow3|rin|rmut|rsec|rhint|rgo|rmsg|rsum|rstopp|cp[a-z]*)\b", l))
    rh = _teil(cockpit, " <div id=routesect style=\"display:none\">", " <div id=planerbox")
    rh = rh.split(">", 1)[1] if rh else ""
    rh = re.sub(r"<div class=map style=\"margin:12px 0;height:300px\"><div id=rmap style=\"height:100%\"></div></div>", "", rh)
    rh = rh.strip()
    if rh.endswith("</div>"):
        rh = rh[:-6]                      # schliessendes </div> des routesect-Rahmens
    rj = _teil(cockpit, "// --- Route (1.10)", "// --- Waechter-Aufnahmen")
    ch = _teil(cockpit, "   <div id=cp_probe", "   <details class=cpproto>")
    ch += "   <details class=cpproto><summary>Was Panoptes zuletzt geschaltet hat</summary><div id=cp_proto></div></details>" if ch else ""
    cj = _teil(cockpit, "let CP_T=null", "function kacheln(s)")
    return css, rh, rj, ch, cj


WALLBOX_TILE = ("<section class='card t' id='t_wallbox' style='display:none'><div class=kk onclick=\"kachelUm('laden')\">"
                "<h2><svg><use href='#i-flash'/></svg>Wallbox<span class=chev>Bedienen</span></h2><div class=v id=t_wallbox_v>–</div><div class=muted id=t_wallbox_m></div></div></section>")


def seite(karten_stil="", panoptes_web="", cockpit=""):
    css, rh, rj, ch, cj = uebernommen(cockpit)
    route_auf = rh or ROUTE_FALLBACK
    camp_auf = ch or '<div class=hint>Camping</div>'
    camping_sub = '<div class=muted id=cp_sub style="display:none"></div>'
    route_tile = _tile("route", "route", "Route", "t_route_v", "t_route_m", route_auf)
    laden_tile = _tile("laden", "flash", "Laden", "t_laden_v", "t_laden_m", LADEN_AUF)
    klima_tile = _tile("klima", "snow", "Klima", "t_klima_v", "t_klima_m", KLIMA_AUF)
    camp_tile = _tile("camping", "tent", "Camping", "t_camping_v", "t_camping_m", camp_auf)
    html = (HEAD.replace("@@CSS@@", CSS.replace("@@ALT_CSS@@", css)) + BODY_TEIL1 + route_tile + laden_tile + WALLBOX_TILE + klima_tile + camp_tile + BODY_TEIL3
            + JS.replace("// @@ROUTE_JS@@", rj).replace("// @@CAMPING_JS@@", cj)) + "</html>"
    html = html.replace("@@ROUTE_HTML@@", "").replace("@@CAMPING_HTML@@", "")
    html = html.replace("@@ANP_KNOPF@@", anpassen.KNOPF).replace("@@ANP_CSS@@", anpassen.CSS).replace("// @@ANP_JS@@", anpassen.JS)
    html = html.replace("<div class=wm id=wm ", anpassen.FUSS + "<div class=wm id=wm ", 1)
    return html.replace("__KARTENSTIL__", karten_stil).replace("__PANOPTES_WEB__", panoptes_web.rstrip("/"))
