# -*- coding: utf-8 -*-
"""1.21: EIN Aussehen fuer alle Unterseiten (Einstellungen, Wallbox & Energie, Panoptes-Einstellungen, Ueber, Laden, Fahrten,
Aufnahmen, Karte ...): dieselben Kacheln, Karten, Knoepfe und Formularfelder wie auf "Mein Auto". Gross, wenig Text, Symbole.
Die Seiten behalten ihre Inhalte und Funktionen; ihr altes <style> wird durch dieses Stylesheet ersetzt (neu())."""
import re

UNI_CSS = r"""<style id=uni>
*{box-sizing:border-box}
:root{--surface:#0A2238;--soft:#0f2c40;--border:#1d4152;--txt:#EAF6F8;--mut:#A9C7CE;--blue:#5FD6E6;--cyan:#5FD6E6;--aqua:#5FD6E6;
 --lime:#B5F23D;--lime-ink:#1d2a00;--amber:#FFC266;--coral:#FF8A6B;--ink:#EAF6F8;--ink-2:#A9C7CE;--ink-3:#6E8E97;--line:rgba(160,230,240,.14);--bg:#071a2b}
html,body{margin:0}
body{color:var(--txt);min-height:100vh;font:16px/1.5 'Manrope',system-ui,sans-serif;padding:0 0 60px}
.w,.wrap{max-width:980px;margin:0 auto;padding:6px 22px 24px}
h1{font:700 26px 'Sora',system-ui,sans-serif;letter-spacing:-.01em;margin:6px 0 4px}
h2{font:700 15px 'Sora',system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);margin:0 0 10px}
h3{font:700 17px 'Sora',system-ui,sans-serif;margin:0 0 6px}
a{color:var(--aqua)}
small,.sub,.h,.hint,.rhint,.lock{color:var(--ink-2)}
.sub{margin:0 0 16px;font-size:15px}
code{background:rgba(4,16,27,.55);padding:1px 6px;border-radius:7px;font-size:13px}
/* Karten */
.card,.panel,.tile,.chk,.nfe,details.akkd,.energy-shell,.energy-card{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:20px;padding:16px 18px;margin:0 0 14px;backdrop-filter:none;position:relative}
.card h2:first-child,.panel h2:first-child{margin-top:0}
.chk{display:flex;align-items:flex-start;gap:14px;margin:10px 0 0;border-radius:16px;padding:14px 16px;cursor:pointer}
.chk:has(input:checked){border-color:var(--lime);background:rgba(181,242,61,.07)}
.chk input{width:26px;height:26px;margin:2px 0 0;flex:0 0 auto;accent-color:#B5F23D}
.chk .h{font:700 17px 'Manrope',system-ui,sans-serif;color:var(--txt);margin:0}
.chk small{display:block;font-size:13.5px;margin-top:3px}
.warn,.warnb{background:rgba(255,194,102,.09);border:1px solid rgba(255,194,102,.5);border-radius:16px;padding:14px 16px;margin:0 0 14px;color:var(--txt)}
.warn b:first-child{color:var(--amber)}
.ok{background:rgba(181,242,61,.07);border:1px solid rgba(181,242,61,.35);border-radius:16px;padding:14px 16px;margin:0 0 14px;color:var(--txt)}
.err{color:var(--amber)}
/* Formulare */
label{display:block;color:var(--ink-2);font-size:13px;font-weight:700;letter-spacing:.03em;margin:14px 0 6px}
.chk label,label.chk{margin:0}
input:not([type=checkbox]):not([type=radio]):not([type=range]):not([type=file]),select,textarea{width:100%;min-height:52px;padding:12px 14px;border-radius:14px;border:1px solid var(--line);
 background:rgba(4,16,27,.55);color:var(--txt);font:600 16px 'Manrope',system-ui,sans-serif}
input[type=file]{width:100%;padding:12px;border-radius:14px;border:1px dashed var(--line);background:rgba(4,16,27,.35);color:var(--ink-2)}
input[type=file]::file-selector-button{background:var(--lime);color:var(--lime-ink);border:0;border-radius:10px;padding:9px 14px;margin-right:12px;font-weight:700;cursor:pointer}
input[type=checkbox],input[type=radio]{accent-color:#B5F23D;width:24px;height:24px}
input[type=range]{width:100%;accent-color:#B5F23D}
input:focus,select:focus,textarea:focus{outline:2px solid rgba(95,214,230,.6);outline-offset:1px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
/* Knoepfe: gross, Limette = die eine Hauptaktion, Glas = alles andere */
button,.btn,a.btn{min-height:52px;padding:12px 22px;border:0;border-radius:16px;background:var(--lime);color:var(--lime-ink);font:700 16px 'Manrope',system-ui,sans-serif;
 cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:9px;text-decoration:none;line-height:1.2}
button.sec,.sec,.rsec,.sbtn,button.zweit,.btn.glas,a.btn.glas,.cpknoepfe button.zweit,.nfe button.nfs{background:rgba(255,255,255,.085);color:var(--txt);border:1px solid var(--line)}
button:hover,.btn:hover{filter:brightness(1.07)}
button.sec:hover,.sec:hover,.rsec:hover{border-color:var(--aqua)}
button:disabled,button[disabled]{opacity:.45;cursor:not-allowed}
.nav{display:flex;justify-content:space-between;gap:12px;margin-top:18px}
.nav button{min-width:150px}
.msg{margin-top:10px;min-height:20px;font-size:14.5px}
/* Fortschritt (Assistent) */
.dots{display:flex;gap:8px;margin:0 0 18px}
.dot2{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;position:relative}
.dot2 i{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,.07);border:1px solid var(--line);display:grid;place-items:center;font:700 16px 'Sora',sans-serif;font-style:normal;color:var(--ink-2);z-index:2}
.dot2 b{font-size:12px;color:var(--ink-2);font-weight:600;text-align:center}
.dot2:not(:last-child):after{content:"";position:absolute;top:20px;left:50%;width:100%;height:2px;background:var(--line);z-index:1}
.dot2.on i{background:var(--lime);color:var(--lime-ink);border-color:transparent}.dot2.on b{color:var(--txt)}
.dot2.done i{background:rgba(181,242,61,.2);border-color:rgba(181,242,61,.55);color:var(--lime)}
.pan{display:none}.pan.on{display:block}
/* Ausklappbares: wie eine Karte */
details{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:18px;padding:0 16px;margin:10px 0}
details>summary{list-style:none;cursor:pointer;padding:15px 0;font:700 16px 'Manrope',system-ui,sans-serif;display:flex;align-items:center;gap:10px;color:var(--txt)}
details>summary::-webkit-details-marker{display:none}
details>summary::after{content:"▾";margin-left:auto;color:var(--aqua)}
details[open]>summary::after{content:"▴"}
details[open]{padding-bottom:14px}
details>summary span{color:var(--ink-2);font-weight:500;font-size:13.5px}
/* Tabellen */
table{border-collapse:collapse;width:100%}
th,td{padding:10px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th{color:var(--ink-2);font-size:12.5px;font-weight:700}th:first-child,td:first-child{text-align:left}
/* Kacheln-Menue (Mehr) */
.hub{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:8px 0 18px}
.hub a{display:flex;flex-direction:column;gap:6px;min-height:118px;padding:16px 18px;border-radius:20px;border:1px solid var(--line);background:rgba(255,255,255,.045);color:var(--txt);text-decoration:none}
.hub a:hover{border-color:var(--aqua)}
.hub a svg{width:30px;height:30px;color:var(--aqua)}
.hub a b{font:700 18px 'Sora',system-ui,sans-serif}
.hub a small{font-size:13.5px}
.hub a.neu{background:linear-gradient(135deg,rgba(11,92,102,.45),rgba(10,34,56,.35))}
@media(max-width:760px){.hub{grid-template-columns:1fr 1fr}.row{grid-template-columns:1fr}}
@media(max-width:480px){.hub{grid-template-columns:1fr}.w,.wrap{padding:6px 14px 24px}.dot2 b{display:none}}
</style>"""

ICONS = r"""<svg width="0" height="0" style="position:absolute">
 <symbol id="n-gear" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
 <symbol id="n-flash" viewBox="0 0 24 24"><path d="M13 2 4 14h7l-1 8 9-12h-7z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
 <symbol id="n-plug" viewBox="0 0 24 24"><path d="M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
 <symbol id="n-book" viewBox="0 0 24 24"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3zM5 17a3 3 0 0 1 3-3h11M9 8h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
 <symbol id="n-eye" viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="n-map" viewBox="0 0 24 24"><path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2zM9 4v14M15 6v14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></symbol>
 <symbol id="n-sat" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M6 12a6 6 0 0 1 6-6M3 12a9 9 0 0 1 9-9M18 12a6 6 0 0 1-6 6M21 12a9 9 0 0 1-9 9" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
 <symbol id="n-info" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 11v6M12 7.5v.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
 <symbol id="n-globe" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
 <symbol id="n-bell" viewBox="0 0 24 24"><path d="M6 17V11a6 6 0 0 1 12 0v6l1.5 2h-15zM10 21h4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></symbol>
 <symbol id="n-card" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3 10h18M7 15h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
 <symbol id="n-coin" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M14.5 9a3 3 0 0 0-5 1.5c0 3 5 1.5 5 4.5a3 3 0 0 1-5 1.5M12 6.5v1.5M12 16v1.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></symbol>
</svg>"""


def neu(html):
    """Altes <style> der Seite durch das gemeinsame neue Stylesheet ersetzen (nur das erste im <head>)."""
    return re.sub(r"<style>.*?</style>", lambda m: "", html, count=1, flags=re.S)


# --- Seiten, die aus der alten Ansicht (/klassisch) hervorgehen: jede zeigt GENAU EINEN Bereich, im neuen Look ---------------
# (Skript und Markup der alten Ansicht bleiben die Quelle, damit keine Funktion verloren geht; nur der gewuenschte Bereich ist sichtbar.)
SEITEN = {
    # pfad: (titel, sichtbare Bereiche, aufzuklappende Bereiche)
    "/laden":      ("Laden & Kosten", ("kt_laden", "kt_wb", "d_ladungen"), ("d_ladungen",)),
    "/fahrten":    ("Fahrtenbuch", ("fbbox",), ("fbdet",)),
    "/aufnahmen":  ("Wächter-Aufnahmen", ("kt_waechter", "aufnbox"), ("aufndet",)),
    "/karte":      ("Karte & Ladesäulen", ("d_karte",), ("d_karte",)),
    "/energie":    ("Wallbox & Energie", ("d_energie", "kt_wb"), ("d_energie",)),
    "/takt":       ("Abfrage & Meldungen", ("taktseite",), ()),
}
ALLE_BEREICHE = ("overview", "kt_waechter", "kt_route", "kt_laden", "kt_wb", "d_klima", "d_karte", "d_camping", "d_energie",
                 "aufnbox", "fbbox", "d_ladungen", "taktseite")

SEK_CSS = r"""<style id=sek>
.top,#statuszeile,#schnell,#schnellmsg,#wbhinweis,.quicknav,.akk>div>.sect,#taktbox{display:none!important}
.kgrid{display:block}.kspalte{display:block}.akk{display:block}
.ktile,.akk>details,.akk #aufndet,.akk #fbdet{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:20px;padding:16px 18px;margin:0 0 14px}
.khead{display:flex;justify-content:space-between;align-items:center;gap:10px;font:700 15px 'Sora',system-ui,sans-serif;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-2);margin:0 0 12px}
.khead a{letter-spacing:0;text-transform:none;font:600 14px 'Manrope',sans-serif;color:var(--aqua);text-decoration:none}
.ksub,.sect{color:var(--ink-2);font:700 13px 'Sora',sans-serif;letter-spacing:.06em;text-transform:uppercase;margin:16px 2px 8px}
.grid{display:grid;gap:12px}.tile{padding:14px 16px;margin:0}.tile .k{color:var(--ink-3);font:700 12px 'Sora',sans-serif;letter-spacing:.08em}
.tile .v{font:700 26px 'Sora',sans-serif;letter-spacing:-.02em;margin-top:4px}.tile .v small{font-size:14px;color:var(--ink-2)}
.lkz{display:flex;justify-content:space-between;gap:10px;border-top:1px solid var(--line);padding:11px 2px;font-size:16px}.lkz:first-child{border-top:0}
.lkz .m{color:var(--ink-2);font-size:14px;text-align:right}
.lkk{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}.lkk b{font:700 36px 'Sora',sans-serif}.lkk b small{font-size:16px;color:var(--ink-2)}
.lkk .lkkl,.lkk2{color:var(--ink-2);font-size:14px}.lkk select{width:auto;min-height:44px}.lkunv,#lk_nachfrage,#lk_nachfrage a,.lkk2 a{color:var(--amber)}
.nfe{margin:6px 0 10px;padding:14px}.nfz{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:10px}
.nfe select{flex:1 1 200px;width:auto}.nfe input.nfp{width:110px}.nfe input.nfn{flex:1 1 180px;width:auto}.nfmsg{color:var(--ink-2);font-size:13px}
.rhint{font-size:13.5px;line-height:1.5;margin-top:8px}.rmsg{font-size:14.5px;margin-top:8px}.rmsg-laut{color:var(--amber);font-weight:700}
.rsec{margin-top:12px;display:inline-flex;align-items:center;justify-content:center;min-height:52px;padding:0 20px;border-radius:16px;font:700 16px 'Manrope',sans-serif;text-decoration:none;cursor:pointer}.rgo{background:var(--lime);color:var(--lime-ink);min-height:56px;padding:0 24px;border:0;border-radius:16px;font:700 17px 'Manrope',sans-serif;cursor:pointer}
#taktbox{background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:20px;padding:18px 20px;font-size:16px}#taktbox b{font:700 18px 'Sora',sans-serif}#taktbox p{color:var(--ink-2)}
.top .on{padding:0}
.fbtab{min-width:560px;font-size:15px}.fbtab tfoot td{font-weight:700;border-top:2px solid var(--line)}.fbtab tr.ladmon td{text-align:left;font-weight:700;padding-top:16px;white-space:normal}
.aufnfilter{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 6px}.aufnfilter select{width:auto;flex:1 1 170px}
.aufngrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin-top:12px}
.aufn{border:1px solid var(--line);border-radius:16px;overflow:hidden;cursor:pointer;background:var(--soft);font-size:14px}
.aufn img,.aufn .leer{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;background:#071a2b}.aufn .leer{display:flex;align-items:center;justify-content:center;color:var(--ink-2)}
.aufn .t{padding:9px 11px;line-height:1.35}.aufn .t b{display:block;font-size:15px}.aufn.weg{opacity:.5;cursor:default}
.bars{display:flex;align-items:flex-end;gap:3px;height:120px;margin-top:12px;padding:14px 10px 0;background:rgba(4,16,27,.45);border:1px solid var(--line);border-radius:16px}
.bar{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;position:relative}
.bar i{display:block;width:100%;border-radius:4px 4px 0 0;background:rgba(160,230,240,.35)}
.bar.now i{background:var(--aqua)}.bar.cheap i{background:var(--lime)}
.bar b{font-size:10px;color:var(--ink-2);margin-top:4px;font-weight:500}.bar.now b,.bar.cheap b{color:var(--txt);font-weight:700}
.bar span.t{position:absolute;top:-14px;font-size:10px;color:var(--ink-2);white-space:nowrap}
.pschalter{font-size:14px;margin:8px 2px 0}.pschalter a{color:var(--aqua)}
.map{border:1px solid var(--line);border-radius:20px;overflow:hidden;height:420px;position:relative;z-index:0}
#lmap{width:100%;height:100%;background:#071a2b}
.chg{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:13px 6px;border-bottom:1px solid var(--line)}
.chg:last-child{border-bottom:0}.chg .nm{font-size:16px;font-weight:600}.chg .sub{color:var(--ink-2);font-size:13.5px;margin-top:2px}.chg .km{color:var(--aqua);font:700 17px 'Sora',sans-serif;white-space:nowrap}.chg a{color:inherit;text-decoration:none}
.leaflet-tile{filter:grayscale(.55) brightness(.72) contrast(1.06)}.leaflet-container{background:#071a2b;font:inherit}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:#0A2238;color:#EAF6F8}.leaflet-popup-content b{color:#5FD6E6}
.leaflet-control-attribution{background:rgba(10,17,32,.8)!important;color:#A9C7CE!important}.leaflet-control-attribution a{color:#A9C7CE!important}
.leaflet-bar a{background:#0A2238!important;color:#EAF6F8!important;border-color:rgba(160,230,240,.2)!important}
.mk-car{width:22px;height:22px;border-radius:50%;background:var(--aqua);border:2px solid #EAF6F8;box-shadow:0 0 0 6px rgba(95,214,230,.28)}
.mk-chg{width:20px;height:20px;border-radius:50%;background:var(--lime);border:2px solid #071a2b;display:flex;align-items:center;justify-content:center;font-size:11px;color:#04101b;font-weight:700}
.wbzeile .wbk{display:flex;flex-wrap:wrap;gap:8px 28px;align-items:center}.wbzeile .wbk div{min-width:96px}.wbzeile small{display:block;color:var(--ink-2);font-size:13px}.wbzeile b{font:700 22px 'Sora',sans-serif}.wbzeile .gesp{color:var(--amber);font-weight:600}
.chips{display:flex;gap:10px;flex-wrap:wrap}.chip{border:1px solid var(--line);border-radius:999px;padding:8px 14px;font-size:14px;background:rgba(255,255,255,.04)}
.pill{display:inline-flex;align-items:center;gap:8px;min-height:52px;padding:0 20px;border-radius:16px;border:1px solid var(--line);background:rgba(255,255,255,.085);font-weight:700;cursor:pointer;color:var(--txt)}
.altband,.hinweis{margin:0 0 14px;padding:12px 16px;border-radius:14px;border:1px solid rgba(255,194,102,.55);background:rgba(255,194,102,.08);color:var(--amber);font-weight:600}
.err{background:rgba(255,138,107,.1);border:1px solid rgba(255,138,107,.45);border-radius:14px;padding:12px 16px;color:var(--coral);margin-bottom:14px;display:none}
#updbar{display:none!important}
#d_energie,#d_karte{background:none;border:0;padding:0;margin:0}#d_energie>summary,#d_karte>summary{display:none}
.sekleer{display:none}
.sekleer.on{display:block}
.sekleer .grosz{font-size:42px;line-height:1}
#kt_takt label{display:flex;justify-content:space-between;align-items:center;gap:14px;margin:12px 0}
#kt_takt select{width:auto;min-width:160px}
#glocke{display:inline-flex;align-items:center;gap:10px;min-height:56px;padding:0 20px;border-radius:16px;border:1px solid var(--line);background:rgba(255,255,255,.085);font-size:22px;cursor:pointer;opacity:1}
#glocke.an{background:var(--lime);color:var(--lime-ink)}
</style>"""

LEER_TEXT = {
    "/laden": ("🔌", "Hier erscheinen Kosten, Ladungen und Ladekarten, sobald dein Auto Daten liefert.",
               "Dafür braucht es Panoptes im Auto (Einstellungen → Panoptes verbinden)."),
    "/fahrten": ("📖", "Das Fahrtenbuch kommt direkt von Panoptes im Auto.", "Verbinde das Cockpit zuerst mit Panoptes (Einstellungen)."),
    "/aufnahmen": ("👁️", "Die Wächter-Aufnahmen kommen von Panoptes im Auto.", "Verbinde das Cockpit zuerst mit Panoptes (Einstellungen)."),
    "/karte": ("🗺️", "Die Karte mit Ladesäulen braucht einen Standort deines Autos.", "Sobald das Auto Daten liefert, erscheint sie hier."),
}


def sektion_html(cockpit, pfad):
    """Alte Ansicht -> eine Seite mit genau einem Bereich im neuen Look (Skript bleibt vollstaendig, nur andere Bereiche sind verborgen)."""
    titel, sicht, auf = SEITEN[pfad]
    h = cockpit.replace("<title>EV-Cockpit</title>", "<title>EV-Cockpit — %s</title>\n<meta name=evc-neu content=1>" % titel.replace("&", "&amp;"), 1)
    regeln = "".join("#%s{display:none!important}" % i for i in ALLE_BEREICHE if i not in sicht and i != "taktseite")
    if "taktseite" in sicht:
        regeln += ("#taktbox{display:block!important;position:static!important;max-width:none!important;margin:0 0 14px!important}"
                   ".top{display:block!important;margin:0}.top>div:first-child,.top .on>*:not(#glocke){display:none!important}"
                   "#glocke::after{content:' Meldung, wenn das Laden fertig ist';font-size:16px;font-weight:700}")
    else:
        regeln += "#taktbox{display:none!important}"
    leer = ""
    if pfad in LEER_TEXT:
        ic, a, b = LEER_TEXT[pfad]
        leer = '<div class="card sekleer" id=sekleer><div class=grosz>%s</div><h3>%s</h3><div class=sub>%s</div></div>' % (ic, a, b)
    kopf = '<style id=sekregeln>%s</style>' % regeln
    h = h.replace("<body>", "<body>" + SEK_CSS + kopf, 1)
    h = h.replace("<div class=wrap>", "<div class=wrap>" + leer, 1)
    if auf:
        # aufklappen erst NACH dem Skript (ontoggle ruft Funktionen, die erst am Seitenende stehen)
        h = h.replace("</body>", "<script>window.addEventListener('load',function(){%r.forEach(function(i){var e=document.getElementById(i);if(e)e.open=true;});});</script></body>" % (list(auf),), 1)
    if pfad in LEER_TEXT:
        js = ("<script>setTimeout(function(){var ids=%r,s=false;ids.forEach(function(i){var e=document.getElementById(i);if(e&&e.offsetHeight>0)s=true;});"
              "if(!s){var l=document.getElementById('sekleer');if(l)l.classList.add('on');}},6000);</script>") % (list(sicht),)
        h = h.replace("</body>", js + "</body>", 1)
    return h


KACHELN = (
    # (Pfad, Symbol, Titel, Untertitel)
    ("/setup", "gear", "Einstellungen", "Datenquelle, Panoptes verbinden, Aussehen"),
    ("/panoptes", "sat", "Panoptes", "Einstellungen aus dem Auto"),
    ("/energie", "plug", "Wallbox & Energie", "Wallbox, Solar, evcc"),
    ("/laden", "coin", "Laden & Kosten", "Kosten, Ladungen, Ladekarten"),
    ("/fahrten", "book", "Fahrtenbuch", "Fahrten ansehen, als CSV"),
    ("/aufnahmen", "eye", "Wächter", "Aufnahmen ansehen"),
    ("/karte", "map", "Karte", "Ladesäulen in der Nähe"),
    ("/takt", "bell", "Abfrage & Meldungen", "Wie oft nachfragen, Laden fertig"),
    ("/about", "info", "Über", "Lizenzen, Datenschutz, Version"),
)


def hub_html(version=""):
    """Seite "Mehr": grosse Kacheln mit Symbol, wenig Text (REGEL DAU)."""
    nl = chr(10)
    k = "".join('<a href="%s"><svg><use href="#n-%s"/></svg><b>%s</b><small>%s</small></a>' % (p, i, t.replace("&", "&amp;"), u) for p, i, t, u in KACHELN)
    k += ('<a href="#" onclick="try{localStorage.setItem(' + "'evc_lang'" + ',window.__LANG__===' + "'en'" + '?' + "'de'" + ':' + "'en'" +
          ');}catch(e){}location.reload();return false"><svg><use href="#n-globe"/></svg><b>Deutsch / English</b><small>Sprache wechseln</small></a>')
    return nl.join(["<!doctype html><html lang=de><head><meta charset=utf-8>",
                    '<meta name=viewport content="width=device-width,initial-scale=1">',
                    "<title>EV-Cockpit — Mehr</title>", "<meta name=evc-neu content=1>", "<style>x</style></head><body><div class=w>",
                    "<h1>Mehr</h1><div class=hub>%s</div><div class=sub>Panoptes Cockpit %s</div></div></body></html>" % (k, version)])
