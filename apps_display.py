# -*- coding: utf-8 -*-
"""1.23: Bereich "Apps & Display" wie in Panoptes 0.1.38 (UI_AUFBAU_HANDY_VORGABE.md §3):
  - "Was zeigt der Tacho?"  (TACHO_AUSWAHL_API.md, Recht "tacho")
  - "Launcher einrichten"   (LAUNCHER_LAYOUT_API.md §2/§3/§8, Recht "launcher": Raster, Apps, Leiste, Hintergrund, "Oeffnen")

Nur ueber die Kopplung (Art handy oder cockpit); beide Rechte schaltet NUR der Besitzer in Panoptes unter "Gekoppelte Geraete" ein,
das Cockpit bittet nie selbst darum. Fehlt ein Recht, zeigt die Seite den Satz von Panoptes (403 {grund nicht_erlaubt, recht, text}).
Nie ein Fahrzeugbefehl, nie etwas aussen am Auto (REGEL A+): Tacho und Launcher wirken nur auf den Bildschirmen im Auto.
An Panoptes geht nur, was hier fest steht: genau diese Pfade, beim Launcher-Stand genau {"aktion": "oeffnen"}."""
import json
import re
import urllib.error

TACHO_PFAD, TACHO_NORMAL = "/api/tacho/auswahl", "/api/tacho/normal"
LAYOUT_PFAD = "/api/launcher/v1/layout"
APPS_PFAD = LAYOUT_PFAD + "/apps"
STANDARD_PFAD = LAYOUT_PFAD + "/standard"
STAND_PFAD = "/api/appupdate/launcher"
MAX_LAYOUT = 64 * 1024
ID_MUSTER = re.compile(r"^(normal|design:[a-z]{2,20}|app:[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+)$")

TACHO_GRUENDE = {
    "nicht_freigegeben": "Erst am Auto freigeben.",
    "nur_im_stand": "Nur in P möglich.",
    "hinweis_noetig": "Bitte einmal am Auto den Hinweis bestätigen.",
    "nicht_installiert": "Die App ist nicht mehr installiert.",
    "ungueltige_auswahl": "Das geht nicht.",
}
TACHO_SONST = "Auf diesem Auto nicht möglich."
DESIGNS = {"klar": "Klar", "sport": "Sport", "nacht": "Nacht", "horizont": "Horizont", "route": "Route"}

TEXT_ALT = "Dein Panoptes kann das noch nicht. Bitte Panoptes aktualisieren (ab Version 0.1.38)."
TEXT_KOPPLUNG = ("Dafür braucht das Cockpit die Kopplung „Steuern einrichten“ (Startseite). "
                 "Danach in Panoptes unter „Gekoppelte Geräte“ das Recht einschalten.")
TEXT_WEG = "Das Auto antwortet gerade nicht. Bitte später noch einmal."
TEXT_ABGELAUFEN = "Die Verbindung zu Panoptes ist abgelaufen. Bitte unter Mehr → Einstellungen neu verbinden."
TEXT_NEUER = "Am Auto wurde gerade etwas geändert. Sie sehen jetzt den neuesten Stand."


def tacho_satz(grund):
    g = str(grund or "")
    return TACHO_GRUENDE.get(g, TACHO_SONST) if g else ""


def _anfrage(pv, pfad, daten=None, methode=None):
    """(Status, dict) ueber die Kopplung. 401 -> einmal neu anmelden (wie Panoptes._get); weitere 401 -> Ausnahme."""
    import panoptes_source as ps
    if not pv.jwt:
        pv._anmelden()

    def einmal():
        try:
            d = pv.http(pv.url + pfad, daten, jwt=pv.jwt, methode=methode)
        except urllib.error.HTTPError as e:
            try:
                d = json.loads(e.read().decode("utf-8") or "{}")
            except Exception:
                d = {}
            d = d if isinstance(d, dict) else {}
            d["_status"] = e.code
        d = d if isinstance(d, dict) else {}
        return int(d.pop("_status", 200) or 200), d
    try:
        return einmal()
    except ps.NichtAngemeldet:
        pv._anmelden()
        return einmal()


def _fehler(status, d):
    """Einheitliche Antwort an die Seite, wenn Panoptes nicht 200 sagt."""
    if status == 403 and d.get("grund") == "nicht_erlaubt":
        return {"ok": False, "recht": str(d.get("recht") or "")[:20],
                "text": str(d.get("text") or "In Panoptes unter „Gekoppelte Geräte“ das Recht einschalten.")[:300]}
    if status == 403:
        return {"ok": False, "text": TEXT_KOPPLUNG}
    if status in (404, 405):
        return {"ok": False, "alt": True, "text": TEXT_ALT}
    return {"ok": False, "text": TEXT_WEG}


def _sicher(fn):
    """Netz- und Anmeldefehler werden zu einem Satz (die Seite zeigt ihn), nie zu einer Ausnahme im Webserver."""
    def w(pv, *a):
        import panoptes_source as ps
        if pv is None:
            return {"ok": False, "text": "Erst mit Panoptes verbinden (Mehr → Einstellungen)."}
        try:
            return fn(pv, *a)
        except ps.NichtAngemeldet:
            return {"ok": False, "text": TEXT_ABGELAUFEN}
        except Exception:
            return {"ok": False, "text": TEXT_WEG}
    w.__name__ = fn.__name__
    return w


# ---------------------------------------------------------------- Tacho

def _eintrag(e):
    if not isinstance(e, dict) or not ID_MUSTER.match(str(e.get("id") or "")):
        return None
    art = "design" if e.get("art") == "design" else "app"
    name = DESIGNS.get(str(e.get("design") or ""), "") if art == "design" else ""
    name = name or str(e.get("name") or e.get("paket") or "")[:40]
    w = e.get("waehlbar") is True
    return {"id": e["id"], "art": art, "name": name, "waehlbar": w, "gewaehlt": e.get("gewaehlt") is True,
            "fahrt": e.get("fahrt") is True, "video": e.get("video") is True, "navi": e.get("navi") is True,
            "satz": "" if w else tacho_satz(e.get("grund") or "sonst")}


@_sicher
def tacho_lesen(pv):
    st, d = _anfrage(pv, TACHO_PFAD)
    if st != 200 or d.get("ok") is False:
        return _fehler(st, d)
    jetzt = d.get("jetzt") if isinstance(d.get("jetzt"), dict) else {}
    eintraege = [x for x in (_eintrag(e) for e in (d.get("eintraege") or [])[:60]) if x]
    return {"ok": True, "angeboten": d.get("angeboten") is not False,
            "satz": "" if d.get("angeboten") is not False else tacho_satz(d.get("grund") or "sonst"),
            "hinweis": d.get("hinweisVerstanden") is False,
            "jetzt": str(jetzt.get("id") or "normal")[:120], "eintraege": eintraege}


@_sicher
def tacho_waehlen(pv, kennung):
    kennung = str(kennung or "")
    if not ID_MUSTER.match(kennung):
        return {"ok": False, "text": TACHO_GRUENDE["ungueltige_auswahl"]}
    st, d = _anfrage(pv, TACHO_PFAD, {"id": kennung})
    if st == 200 and d.get("ok") is not False:
        return {"ok": True}
    if st in (400, 409):
        return {"ok": False, "text": tacho_satz(d.get("grund") or "sonst")}
    return _fehler(st, d)


@_sicher
def tacho_normal(pv):
    st, d = _anfrage(pv, TACHO_NORMAL, {}, "POST")
    if st == 200 and d.get("ok") is not False:
        return {"ok": True}
    return _fehler(st, d) if st != 409 else {"ok": False, "text": TACHO_SONST}


# ---------------------------------------------------------------- Launcher

@_sicher
def launcher_lesen(pv):
    st, d = _anfrage(pv, LAYOUT_PFAD)
    if st != 200:
        return _fehler(st, d)
    if not isinstance(d.get("layout"), dict):
        return {"ok": False, "text": TEXT_WEG}
    sa, a = _anfrage(pv, APPS_PFAD)
    apps = []
    for x in (a.get("apps") or [])[:400] if sa == 200 else []:
        if isinstance(x, dict) and re.match(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$", str(x.get("paket") or "")):
            apps.append({"paket": x["paket"][:200], "name": str(x.get("name") or x["paket"])[:40], "video": x.get("video") is True})
    return {"ok": True, "layout": d["layout"], "geaendert": d.get("geaendert") or 0, "standard": d.get("standard") is True,
            "apps": apps, "stand": launcher_stand(pv)}


def launcher_stand(pv):
    """Ist der Launcher am Auto installiert? (gleiches Recht). Fehler -> {} (Karte zeigt dann nichts)."""
    try:
        st, d = _anfrage(pv, STAND_PFAD)
    except Exception:
        return {}
    if st != 200:
        return {}
    return {"installiert": d.get("installiert") not in (None, False, 0, "")}


def layout_pruefen(layout):
    """Grobe Pruefung vor dem Senden (die genaue macht Panoptes: LauncherLayoutPruefung, bereinigt statt ablehnen)."""
    if not isinstance(layout, dict) or layout.get("format") != "panoptes-launcher-layout" or layout.get("version") != 1:
        return False
    if not isinstance(layout.get("seiten"), list) or not isinstance(layout.get("dock", []), list):
        return False
    return len(json.dumps(layout, ensure_ascii=False).encode("utf-8")) < MAX_LAYOUT - 200


@_sicher
def launcher_speichern(pv, layout, basis):
    if not layout_pruefen(layout):
        return {"ok": False, "text": "Das geht nicht."}
    try:
        basis = int(basis)
    except (TypeError, ValueError):
        return {"ok": False, "text": "Das geht nicht."}
    st, d = _anfrage(pv, LAYOUT_PFAD, {"layout": layout, "basis": basis}, "PUT")
    if st == 200 and d.get("ok") is not False and isinstance(d.get("layout"), dict):
        return {"ok": True, "layout": d["layout"], "geaendert": d.get("geaendert") or 0, "bereinigt": int(d.get("bereinigt") or 0)}
    if st == 409 and isinstance(d.get("layout"), dict):
        return {"ok": False, "neuer": True, "layout": d["layout"], "geaendert": d.get("geaendert") or 0, "text": TEXT_NEUER}
    if st in (400, 413):
        return {"ok": False, "text": "Panoptes hat das nicht angenommen. Die Seite lädt den Stand neu."}
    return _fehler(st, d)


@_sicher
def launcher_standard(pv):
    st, d = _anfrage(pv, STANDARD_PFAD, {}, "POST")
    if st == 200 and isinstance(d.get("layout"), dict):
        return {"ok": True, "layout": d["layout"], "geaendert": d.get("geaendert") or 0}
    return _fehler(st, d)


@_sicher
def launcher_oeffnen(pv):
    """Startet den Launcher am Bildschirm im Auto (nie als Standard-Startbildschirm). Nur am Display sichtbar (REGEL A+ erlaubt das)."""
    st, d = _anfrage(pv, STAND_PFAD, {"aktion": "oeffnen"})
    if st == 200 and d.get("ok") is True:
        return {"ok": True, "text": "Der Launcher ist jetzt am Bildschirm im Auto offen."}
    if st == 200 and d.get("grund") == "nicht_installiert":
        return {"ok": False, "text": "Der Launcher ist im Auto noch nicht installiert. Das geht nur am Auto."}
    if st == 200:
        return {"ok": False, "text": "Das hat nicht geklappt. Bitte noch einmal versuchen."}
    return _fehler(st, d)


LAUNCHER_NUR_AM_AUTO = "Das Launcher-Update geht im Moment nur am Auto."


@_sicher
def launcher_update_stand(pv):
    """Karte "Updates": Stand des Launchers (Recht launcher). Ein Update aus der Ferne gibt Panoptes 0.1.38 Kopplungen noch nicht frei
    (nur {"aktion":"oeffnen"}); darum hier nur lesen und den Satz zeigen, bis der Vertrag UPDATE_API_CLIENTS.md steht."""
    st, d = _anfrage(pv, STAND_PFAD)
    if st != 200:
        return _fehler(st, d)
    v = d.get("verfuegbar") if isinstance(d.get("verfuegbar"), dict) else {}
    inst = d.get("installiert")
    if inst in (None, False, 0, ""):
        return {"ok": True, "installiert": False, "text": "Der Launcher ist im Auto noch nicht installiert. Das geht nur am Auto."}
    if d.get("neuer") is True and v.get("version"):
        return {"ok": True, "installiert": True, "neu": str(v["version"])[:20], "text": LAUNCHER_NUR_AM_AUTO}
    return {"ok": True, "installiert": True, "text": "Der Launcher ist aktuell."}


# ---------------------------------------------------------------- Seiten

TACHO_SEITE = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Tacho</title>
<meta name=evc-neu content=1>
<style>x</style></head><body><div class=w>
<h1>Was zeigt der Tacho?</h1>
<div class=sub>Wähle, was hinter dem Lenkrad zu sehen ist. Das ändert nur die Anzeige, nicht das Auto.</div>
<div class=card id=t_fehl style="display:none"><div id=t_fehltext></div></div>
<div id=t_box style="display:none">
 <div class=warn id=t_hinweis style="display:none">Bitte einmal am Auto den Hinweis bestätigen.</div>
 <div class=card><button type=button class=sec id=t_normal onclick="normal()" style="width:100%">↺ Tacho wieder normal</button>
  <div class=msg id=t_msg></div></div>
 <h2>Aussehen</h2><div class=tgrid id=t_designs></div>
 <h2 id=t_appsk>Apps</h2><div class=tgrid id=t_apps></div>
</div>
<div class=sub id=t_lade>⏳ Frage das Auto …</div>
</div>
<style>
.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin:0 0 18px}
.tk{display:flex;flex-direction:column;align-items:flex-start;gap:6px;min-height:104px;padding:16px;border-radius:18px;border:1px solid var(--line);
 background:rgba(255,255,255,.045);color:var(--txt);font:700 18px 'Sora',system-ui,sans-serif;cursor:pointer;text-align:left}
.tk.an{border-color:var(--lime);background:rgba(181,242,61,.09)}
.tk:disabled{opacity:.5;cursor:not-allowed}
.tk small{font:500 13.5px 'Manrope',system-ui,sans-serif;color:var(--ink-2)}
.tk i{font-style:normal;display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:rgba(95,214,230,.16);color:var(--aqua);font-size:18px}
</style>
<script>
const el=id=>document.getElementById(id);let BUSY=false;
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function kachel(e){const b=document.createElement('button');b.type='button';b.className='tk'+(e.gewaehlt?' an':'');b.disabled=!e.waehlbar;
 const z=[];if(e.gewaehlt)z.push(__T('Jetzt gewählt'));if(e.art==='app'&&!e.fahrt)z.push(__T('Nur in P'));if(e.video)z.push(__T('Video-App'));if(e.satz)z.push(__T(e.satz));
 b.innerHTML='<i>'+(e.art==='design'?'◐':esc((e.name||'?').charAt(0).toUpperCase()))+'</i>'+esc(__T(e.name))+'<small>'+esc(z.join(' · '))+'</small>';
 b.onclick=()=>waehle(e.id);return b;}
async function laden(){
 try{const d=await (await fetch('/tacho/daten')).json();el('t_lade').style.display='none';
  if(!d.ok){el('t_box').style.display='none';el('t_fehl').style.display='';el('t_fehltext').textContent=__T(d.text);return;}
  el('t_fehl').style.display='none';el('t_box').style.display='';
  if(!d.angeboten){el('t_box').style.display='none';el('t_fehl').style.display='';el('t_fehltext').textContent=__T(d.satz||'Auf diesem Auto nicht möglich.');return;}
  el('t_hinweis').style.display=d.hinweis?'':'none';
  const ds=el('t_designs'),as=el('t_apps');ds.innerHTML='';as.innerHTML='';
  d.eintraege.forEach(e=>(e.art==='design'?ds:as).appendChild(kachel(e)));
  el('t_appsk').style.display=as.children.length?'':'none';}
 catch(e){el('t_lade').textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.');}}
async function waehle(id){if(BUSY)return;BUSY=true;el('t_msg').textContent='⏳';
 try{const r=await (await fetch('/tacho/waehlen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:id})})).json();
  el('t_msg').textContent=r.ok?'✓ '+__T('Erledigt.'):'⚠️ '+__T(r.text||'Das hat nicht geklappt.');}catch(e){el('t_msg').textContent='⚠️';}
 BUSY=false;laden();}
async function normal(){if(BUSY)return;BUSY=true;el('t_msg').textContent='⏳';
 try{const r=await (await fetch('/tacho/normal',{method:'POST',body:'{}'})).json();
  el('t_msg').textContent=r.ok?'✓ '+__T('Der Tacho zeigt wieder die normale Anzeige.'):'⚠️ '+__T(r.text||'Das hat nicht geklappt.');}catch(e){el('t_msg').textContent='⚠️';}
 BUSY=false;laden();}
laden();setInterval(()=>{if(document.visibilityState==='visible'&&!BUSY)laden();},10000);
</script></body></html>"""

LAUNCHER_SEITE = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Launcher einrichten</title>
<meta name=evc-neu content=1>
<style>x</style></head><body><div class=w>
<h1>Launcher einrichten</h1>
<div class=sub>So sieht die Startseite des Panoptes-Launchers im Auto aus. Jede Änderung gilt sofort im Auto.</div>
<div class=card id=l_fehl style="display:none"><div id=l_fehltext></div></div>
<div class=sub id=l_lade>⏳ Frage das Auto …</div>
<div id=l_box style="display:none">
 <div class=card id=l_standkarte style="display:none"><h3>Launcher im Auto</h3>
  <div class=sub id=l_standtext></div>
  <button type=button id=l_oeffnen onclick="oeffnen()">▶ Am Auto öffnen</button><div class=msg id=l_oeffnenmsg></div></div>
 <div class=card><h3>Startseite</h3>
  <div class=lseiten id=l_seiten></div>
  <div class=lschirm id=l_schirm></div>
  <div class=sub id=l_tipp>Tippe eine Kachel an. Dann tippe auf ein helles Feld, um sie dorthin zu legen.</div>
  <div class=lwahl id=l_wahl style="display:none">
   <button type=button class=sec id=l_groesse onclick="groesse()">⤢ Größe ändern</button>
   <button type=button class=sec onclick="entfernen()">✕ Entfernen</button>
   <button type=button onclick="waehle(null)">Fertig</button></div>
  <div class=row style="margin-top:12px">
   <select id=l_kneu onchange="kachelNeu(this.value)"></select>
   <select id=l_aneu onchange="appNeu(this.value)"></select></div>
 </div>
 <div class=card><h3>Leiste unten</h3>
  <div class=sub>Ganz links ist immer das Haus (zurück zum BYD-Startbildschirm).</div>
  <div id=l_dock></div><select id=l_dneu onchange="dockNeu(this.value)" style="margin-top:12px"></select></div>
 <div class=card><h3>Hintergrund</h3><div class=lknoepfe id=l_hg></div>
  <div class=sub>Ein eigenes Bild oder Video wählst du am Auto aus. Ein Video läuft nur in P.</div></div>
 <div class=card><h3>Anzeige</h3><div id=l_schalter></div></div>
 <div class=card><button type=button class=sec onclick="standard()">↺ Auf Standard zurücksetzen</button></div>
 <div class=msg id=l_msg></div>
</div>
</div>
<style>
.lseiten{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.lseiten button{min-height:48px;padding:8px 16px}
.lseiten button.an{background:var(--lime);color:var(--lime-ink)}
.lschirm{display:grid;grid-template-columns:repeat(6,1fr);grid-template-rows:repeat(3,1fr);gap:6px;aspect-ratio:16/7;padding:8px;border-radius:18px;
 background:linear-gradient(135deg,#0b3a52,#071a2b);border:1px solid var(--line)}
.lschirm.dunkel{background:#05101a}
.lzelle{border-radius:10px;border:1px dashed rgba(160,230,240,.12)}
.lzelle.frei{position:relative;z-index:2;background:rgba(181,242,61,.22);border:1px solid var(--lime);cursor:pointer}
@media(max-width:620px){.lschirm{aspect-ratio:16/10;gap:4px;padding:6px}.lel{font-size:12.5px}}
.lel{position:relative;z-index:1;border-radius:12px;background:#17405a;border:1px solid var(--line);color:var(--txt);display:flex;flex-direction:column;align-items:center;
 justify-content:center;gap:2px;font:700 14px 'Manrope',system-ui,sans-serif;cursor:pointer;padding:4px;text-align:center;min-height:0;min-width:0;overflow:hidden}
.lel small{font-weight:500;font-size:11.5px;color:var(--ink-2)}
.lel.an{outline:3px solid var(--lime)}
.lwahl{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.lknoepfe{display:flex;flex-wrap:wrap;gap:10px}.lknoepfe button.an{background:var(--lime);color:var(--lime-ink)}
.ldock{display:flex;align-items:center;gap:8px;border-top:1px solid var(--line);padding:8px 2px}.ldock:first-child{border-top:0}
.ldock b{flex:1;font-weight:600}.ldock button{min-height:48px;min-width:52px;padding:6px 12px}
</style>
<script>
const el=id=>document.getElementById(id);
const K={fahrzeug:'Fahrzeug',akku:'Akku',navi:'Navigation',musik:'Musik',waechter:'Wächter',uhr:'Uhr'};
const GR=[[1,1],[2,1],[2,2],[2,3],[3,2],[3,3],[4,2],[4,3],[6,3]];
const HG=[['panoptes','Panoptes'],['cockpit','Dunkel'],['bild','Eigenes Bild'],['video','Eigenes Video']];
const SCH=[['nebeneinander',false,'Apps neben dem Launcher öffnen'],['zeigeKlima',true,'Klima unten anzeigen'],
 ['zeigeStatus',true,'Obere Zeile mit Uhrzeit anzeigen'],['zeigeReiter',true,'Reiterzeile anzeigen'],['zeige3d',true,'Fahrzeug in 3D zeigen']];
let L=null,BASIS=0,APPS=[],SEITE=0,SEL=null,TIMER=null,SENDET=false,NOCHMAL=false;
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function msg(t){el('l_msg').textContent=t?__T(t):'';}
const FEST={'at.greenchili.surfmate':'Panoptes','com.byd.androidauto':'Android Auto','com.byd.carplay.ui':'CarPlay'};
function appName(p){const a=APPS.find(x=>x.paket===p);return a?a.name:(FEST[p]||p);}
function alle(){return L.seiten.reduce((a,s)=>a.concat(s),[]);}
function passt(s,x,y,b,h,ohne){if(x<0||y<0||x+b>6||y+h>3)return false;return !s.some(e=>e.id!==ohne&&x<e.x+e.b&&e.x<x+b&&y<e.y+e.h&&e.y<y+h);}
function frei(s,b,h){for(let y=0;y<=3-h;y++)for(let x=0;x<=6-b;x++)if(passt(s,x,y,b,h))return [x,y];return null;}
function neueId(v){L.zaehler=(L.zaehler||0)+1;return v+L.zaehler;}
function finde(id){for(let i=0;i<L.seiten.length;i++){const e=L.seiten[i].find(x=>x.id===id);if(e)return [i,e];}return null;}
function zeichne(){
 if(SEITE>=L.seiten.length)SEITE=L.seiten.length-1;
 const sb=el('l_seiten');sb.innerHTML='';
 L.seiten.forEach((s,i)=>{const b=document.createElement('button');b.type='button';b.className='sec'+(i===SEITE?' an':'');b.textContent=__T('Seite')+' '+(i+1);b.onclick=()=>{SEITE=i;SEL=null;zeichne();};sb.appendChild(b);});
 if(L.seiten.length<5){const b=document.createElement('button');b.type='button';b.className='sec';b.textContent='+ '+__T('Seite');b.onclick=()=>{L.seiten.push([]);SEITE=L.seiten.length-1;SEL=null;geaendert();};sb.appendChild(b);}
 if(L.seiten.length>1){const b=document.createElement('button');b.type='button';b.className='sec';b.textContent=__T('Seite entfernen');
  b.onclick=()=>{if(!confirm(__T('Diese Seite mit allem darauf entfernen?')))return;L.seiten.splice(SEITE,1);SEITE=Math.max(0,SEITE-1);SEL=null;geaendert();};sb.appendChild(b);}
 const s=L.seiten[SEITE]||[],sch=el('l_schirm');sch.innerHTML='';sch.className='lschirm'+(L.hintergrund==='cockpit'?' dunkel':'');
 const sel=SEL?finde(SEL):null;
 for(let y=0;y<3;y++)for(let x=0;x<6;x++){const z=document.createElement('div');z.className='lzelle';z.style.gridColumn=(x+1);z.style.gridRow=(y+1);
  if(sel&&!(sel[0]===SEITE&&sel[1].x===x&&sel[1].y===y)&&passt(s,x,y,sel[1].b,sel[1].h,SEL)){z.classList.add('frei');z.onclick=()=>verschiebe(x,y);}sch.appendChild(z);}
 s.forEach(e=>{const d=document.createElement('div');d.className='lel'+(e.id===SEL?' an':'');d.style.gridColumn=(e.x+1)+' / span '+e.b;d.style.gridRow=(e.y+1)+' / span '+e.h;
  const t=e.typ==='widget'?__T(K[e.kachel]||e.kachel):e.typ==='ordner'?'📁 '+(e.name||__T('Ordner')):appName(e.paket);
  d.innerHTML=esc(t)+(e.typ==='ordner'?'<small>'+(e.apps||[]).length+' '+esc(__T('Apps'))+'</small>':e.typ==='widget'&&e.b*e.h>1?'<small>'+e.b+'×'+e.h+'</small>':'');
  d.onclick=()=>waehle(e.id===SEL?null:e.id);sch.appendChild(d);});
 el('l_wahl').style.display=SEL?'':'none';el('l_tipp').style.display=SEL?'none':'';
 el('l_groesse').style.display=sel&&sel[1].typ==='widget'?'':'none';
 const kn=el('l_kneu');kn.innerHTML='';kn.appendChild(new Option('+ '+__T('Kachel hinzufügen'),''));
 Object.keys(K).filter(k=>!alle().some(e=>e.typ==='widget'&&e.kachel===k)).forEach(k=>kn.appendChild(new Option(__T(K[k]),k)));
 kn.disabled=kn.options.length<2;
 const an=el('l_aneu');an.innerHTML='';an.appendChild(new Option('+ '+__T('App hinzufügen'),''));APPS.forEach(a=>an.appendChild(new Option(a.name,a.paket)));an.disabled=!APPS.length;
 const dk=el('l_dock');dk.innerHTML='';(L.dock||[]).forEach((p,i)=>{const r=document.createElement('div');r.className='ldock';
  r.innerHTML='<b>'+esc(appName(p))+'</b>';[['←',-1],['→',1],['✕',0]].forEach(([t,w])=>{const b=document.createElement('button');b.type='button';b.className='sec';b.textContent=t;
   b.setAttribute('aria-label',w===0?__T('Entfernen'):w<0?__T('Nach links'):__T('Nach rechts'));
   b.onclick=()=>{if(w===0)L.dock.splice(i,1);else{const j=i+w;if(j<0||j>=L.dock.length)return;L.dock.splice(i,1);L.dock.splice(j,0,p);}geaendert();};r.appendChild(b);});dk.appendChild(r);});
 const dn=el('l_dneu');dn.innerHTML='';const voll=(L.dock||[]).length>=8;
 dn.appendChild(new Option(voll?__T('Die Leiste ist voll (höchstens 8 Apps).'):'+ '+__T('App in die Leiste'),''));
 if(!voll)APPS.filter(a=>!(L.dock||[]).includes(a.paket)).forEach(a=>dn.appendChild(new Option(a.name,a.paket)));dn.disabled=voll;
 const hg=el('l_hg');hg.innerHTML='';HG.forEach(([w,t])=>{const b=document.createElement('button');b.type='button';b.className='sec'+(L.hintergrund===w?' an':'');b.textContent=__T(t);
  b.onclick=()=>{L.hintergrund=w;geaendert();};hg.appendChild(b);});
 const sc=el('l_schalter');sc.innerHTML='';SCH.forEach(([k,std,t])=>{const lb=document.createElement('label');lb.className='chk';const i=document.createElement('input');i.type='checkbox';
  i.checked=L[k]===undefined?std:!!L[k];i.onchange=()=>{L[k]=i.checked;geaendert();};const s2=document.createElement('span');s2.className='h';s2.textContent=__T(t);lb.appendChild(i);lb.appendChild(s2);sc.appendChild(lb);});}
function waehle(id){SEL=id;zeichne();}
function verschiebe(x,y){const f=finde(SEL);if(!f)return;const [i,e]=f;L.seiten[i]=L.seiten[i].filter(z=>z.id!==SEL);e.x=x;e.y=y;L.seiten[SEITE].push(e);geaendert();}
function groesse(){const f=finde(SEL);if(!f||f[1].typ!=='widget')return;const [i,e]=f;let k=GR.findIndex(g=>g[0]===e.b&&g[1]===e.h);
 for(let n=1;n<=GR.length;n++){const g=GR[(k+n)%GR.length];if(passt(L.seiten[i],e.x,e.y,g[0],g[1],e.id)){e.b=g[0];e.h=g[1];geaendert();return;}}msg('Dafür ist hier kein Platz.');}
function entfernen(){const f=finde(SEL);if(!f)return;L.seiten[f[0]]=L.seiten[f[0]].filter(z=>z.id!==SEL);SEL=null;geaendert();}
function kachelNeu(k){if(!k)return;const s=L.seiten[SEITE];let p=frei(s,2,1),b=2;if(!p){p=frei(s,1,1);b=1;}
 if(!p){msg('Auf dieser Seite ist kein Platz mehr.');zeichne();return;}s.push({id:neueId('w'),typ:'widget',kachel:k,x:p[0],y:p[1],b:b,h:1});geaendert();}
function appNeu(pk){if(!pk)return;const s=L.seiten[SEITE],p=frei(s,1,1);if(!p){msg('Auf dieser Seite ist kein Platz mehr.');zeichne();return;}
 s.push({id:neueId('a'),typ:'app',paket:pk,x:p[0],y:p[1],b:1,h:1});geaendert();}
function dockNeu(pk){if(!pk)return;L.dock=L.dock||[];if(L.dock.length<8&&!L.dock.includes(pk))L.dock.push(pk);geaendert();}
function geaendert(){msg('');zeichne();clearTimeout(TIMER);TIMER=setTimeout(senden,600);}
async function senden(){if(SENDET){NOCHMAL=true;return;}SENDET=true;msg('⏳ Speichere …');
 try{const r=await (await fetch('/launcher/speichern',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({layout:L,basis:BASIS})})).json();
  if(r.ok){BASIS=r.geaendert;if(!NOCHMAL)L=r.layout;msg(r.bereinigt?'✓ Gespeichert. Panoptes hat ein paar Dinge passend gemacht.':'✓ Gespeichert.');}
  else if(r.neuer){L=r.layout;BASIS=r.geaendert;NOCHMAL=false;SEL=null;msg(r.text);}
  else{msg('⚠️ '+__T(r.text||'Das hat nicht geklappt.'));NOCHMAL=false;await laden(true);}}
 catch(e){msg('⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.'));}
 SENDET=false;zeichne();if(NOCHMAL){NOCHMAL=false;senden();}}
async function standard(){if(!confirm(__T('Alles auf den Standard zurücksetzen? Deine Anordnung geht dabei verloren.')))return;msg('⏳');
 try{const r=await (await fetch('/launcher/standard',{method:'POST',body:'{}'})).json();if(r.ok){L=r.layout;BASIS=r.geaendert;SEL=null;SEITE=0;msg('✓ Zurückgesetzt.');zeichne();}
  else msg('⚠️ '+__T(r.text||'Das hat nicht geklappt.'));}catch(e){msg('⚠️');}}
async function oeffnen(){const m=el('l_oeffnenmsg');m.textContent='⏳';
 try{const r=await (await fetch('/launcher/oeffnen',{method:'POST',body:'{}'})).json();m.textContent=(r.ok?'✓ ':'⚠️ ')+__T(r.text||'');}catch(e){m.textContent='⚠️';}}
async function laden(still){
 try{const d=await (await fetch('/launcher/daten')).json();el('l_lade').style.display='none';
  if(!d.ok){el('l_box').style.display='none';el('l_fehl').style.display='';el('l_fehltext').textContent=__T(d.text);return;}
  el('l_fehl').style.display='none';el('l_box').style.display='';L=d.layout;BASIS=d.geaendert;APPS=d.apps||[];
  ['seiten','dock'].forEach(k=>{if(!Array.isArray(L[k]))L[k]=k==='seiten'?[[]]:[];});if(!L.seiten.length)L.seiten=[[]];
  if(d.stand&&d.stand.installiert!==undefined){el('l_standkarte').style.display='';
   el('l_standtext').textContent=__T(d.stand.installiert?'Der Launcher ist im Auto installiert.':'Der Launcher ist im Auto noch nicht installiert. Das geht nur am Auto.');
   el('l_oeffnen').style.display=d.stand.installiert?'':'none';}
  zeichne();}
 catch(e){el('l_lade').textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.');}}
laden();
</script></body></html>"""

UPDATES_SEITE = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Updates</title>
<meta name=evc-neu content=1>
<style>x</style></head><body><div class=w>
<h1>Updates</h1>
<div class=sub>Hier sehen Sie, ob es neue Versionen gibt. Installiert wird nur, wenn Sie es bestätigen.</div>
<div class=card><h3>Panoptes im Auto</h3><div class=sub id=u_ptext>⏳ Frage das Auto …</div><div id=u_pknopf></div></div>
<div class=card><h3>Panoptes-Launcher</h3><div class=sub id=u_ltext>⏳ Frage das Auto …</div></div>
<div class=card><h3>EV-Cockpit</h3><div class=sub id=u_ctext></div><div id=u_cknopf></div></div>
</div>
<script>
const el=id=>document.getElementById(id);let UV='',UT=null;
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function pZeigen(r){const t=el('u_ptext'),k=el('u_pknopf');k.innerHTML='';
 if(!r||!r.sichtbar){t.textContent=__T('Dafür braucht das Cockpit die Kopplung „Steuern einrichten“ (Startseite) und Panoptes ab 0.1.26.1.');return;}
 UV=r.version||'';t.textContent=(r.zustand==='laeuft'?'⏳ ':'')+__T(r.text||'');
 if(r.knopf)k.innerHTML='<button type=button onclick="pFrage()">⬆️ '+esc(__T('Panoptes aktualisieren'))+'</button>';}
function pFrage(){el('u_pknopf').innerHTML='<div class=warn><b>'+esc(__T('Panoptes wird jetzt aktualisiert. Wächter und Verbindung sind ca. 3–8 Minuten weg.'))+'</b></div>'
 +'<button type=button onclick="pStart()">'+esc(__T('Ja, jetzt aktualisieren'))+'</button> <button type=button class=sec onclick="pLaden()">'+esc(__T('Abbrechen'))+'</button>';}
async function pStart(){el('u_pknopf').innerHTML='';el('u_ptext').textContent='⏳ '+__T('Sende …');
 try{const r=await (await fetch('/panoptes/update/starten',{method:'POST',body:JSON.stringify({version:UV})})).json();
  el('u_ptext').textContent=(r.ok?'⬆️ ':'⚠️ ')+__T(r.text||'');clearTimeout(UT);UT=setTimeout(pLaden,r.ok?12000:8000);}
 catch(e){el('u_ptext').textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.');}}
async function pLaden(){let r=null;try{r=await (await fetch('/panoptes/update')).json();pZeigen(r);}catch(e){}
 clearTimeout(UT);if(r&&r.zustand==='laeuft')UT=setTimeout(pLaden,12000);}
async function lLaden(){try{const r=await (await fetch('/launcher/stand')).json();el('u_ltext').textContent=(r.neu?__T('Neue Version')+' '+r.neu+' '+__T('ist da.')+' ':'')+__T(r.text||'');}catch(e){el('u_ltext').textContent='⚠️';}}
async function cLaden(){try{const r=await (await fetch('/updates/cockpit')).json();
 el('u_ctext').textContent=r.neu?__T('Neue Version')+' '+r.neu+' '+__T('ist da.')+' '+(r.was_neu||''):(r.pruefen?__T('Das Cockpit ist aktuell')+' ('+r.version+').':__T('Version')+' '+r.version+'. '+__T('Die Suche nach Updates ist aus (Einstellungen).'));
 el('u_cknopf').innerHTML=r.neu?'<a class=btn href="'+esc(r.url)+'" target=_blank rel=noopener>'+esc(__T('Herunterladen'))+' →</a>':'';}catch(e){}}
pLaden();lLaden();cLaden();
</script></body></html>"""


EN = {
    "Was zeigt der Tacho?": "What does the instrument display show?",
    "Wähle, was hinter dem Lenkrad zu sehen ist. Das ändert nur die Anzeige, nicht das Auto.":
        "Choose what you see behind the steering wheel. This only changes the display, not the car.",
    "↺ Tacho wieder normal": "↺ Normal instrument display", "Tacho wieder normal": "Normal instrument display",
    "Aussehen": "Look", "Apps": "Apps", "⏳ Frage das Auto …": "⏳ Asking the car …",
    "Jetzt gewählt": "Selected now", "Nur in P": "Only in P", "Video-App": "Video app", "Erledigt.": "Done.",
    "Der Tacho zeigt wieder die normale Anzeige.": "The instrument display is back to normal.",
    "Klar": "Clear", "Nacht": "Night", "Horizont": "Horizon",
    "Erst am Auto freigeben.": "Allow it in the car first.", "Nur in P möglich.": "Only possible in P.",
    "Bitte einmal am Auto den Hinweis bestätigen.": "Please confirm the notice once in the car.",
    "Die App ist nicht mehr installiert.": "The app is no longer installed.", "Das geht nicht.": "That is not possible.",
    "Auf diesem Auto nicht möglich.": "Not possible on this car.",
    "Dein Panoptes kann das noch nicht. Bitte Panoptes aktualisieren (ab Version 0.1.38).":
        "Your Panoptes cannot do this yet. Please update Panoptes (version 0.1.38 or newer).",
    TEXT_KOPPLUNG: "The Cockpit needs the “Set up control” pairing for this (home page). Then switch on the permission in Panoptes under “Paired devices”.",
    "Das Auto antwortet gerade nicht. Bitte später noch einmal.": "The car is not answering right now. Please try again later.",
    TEXT_ABGELAUFEN: "The connection to Panoptes has expired. Please reconnect under More → Settings.",
    TEXT_NEUER: "Something was just changed in the car. You now see the latest version.",
    "In Panoptes unter „Gekoppelte Geräte“ das Recht einschalten.": "Switch on the permission in Panoptes under “Paired devices”.",
    "Launcher einrichten": "Set up launcher",
    "So sieht die Startseite des Panoptes-Launchers im Auto aus. Jede Änderung gilt sofort im Auto.":
        "This is the home screen of the Panoptes launcher in the car. Every change applies in the car right away.",
    "Launcher im Auto": "Launcher in the car", "▶ Am Auto öffnen": "▶ Open in the car", "Startseite": "Home screen",
    "Tippe eine Kachel an. Dann tippe auf ein helles Feld, um sie dorthin zu legen.":
        "Tap a tile. Then tap a highlighted spot to put it there.",
    "⤢ Größe ändern": "⤢ Change size", "✕ Entfernen": "✕ Remove", "Fertig": "Done", "Leiste unten": "Bottom bar",
    "Ganz links ist immer das Haus (zurück zum BYD-Startbildschirm).": "The house on the far left always stays (back to the BYD home screen).",
    "Hintergrund": "Background", "Ein eigenes Bild oder Video wählst du am Auto aus. Ein Video läuft nur in P.":
        "You choose your own picture or video in the car. A video only plays in P.",
    "Anzeige": "Display", "↺ Auf Standard zurücksetzen": "↺ Reset to default",
    "Fahrzeug": "Vehicle", "Akku": "Battery", "Navigation": "Navigation", "Musik": "Music", "Wächter": "Guard", "Uhr": "Clock",
    "Dunkel": "Dark", "Eigenes Bild": "Own picture", "Eigenes Video": "Own video",
    "Apps neben dem Launcher öffnen": "Open apps next to the launcher", "Klima unten anzeigen": "Show climate at the bottom",
    "Obere Zeile mit Uhrzeit anzeigen": "Show top row with time", "Reiterzeile anzeigen": "Show tab row", "Fahrzeug in 3D zeigen": "Show vehicle in 3D",
    "Seite": "Page", "Seite entfernen": "Remove page", "Diese Seite mit allem darauf entfernen?": "Remove this page and everything on it?",
    "Ordner": "Folder", "Kachel hinzufügen": "Add tile", "App hinzufügen": "Add app", "App in die Leiste": "App to the bar",
    "Die Leiste ist voll (höchstens 8 Apps).": "The bar is full (at most 8 apps).", "Entfernen": "Remove",
    "Nach links": "Move left", "Nach rechts": "Move right", "Dafür ist hier kein Platz.": "There is no room for that here.",
    "Auf dieser Seite ist kein Platz mehr.": "There is no more room on this page.", "⏳ Speichere …": "⏳ Saving …",
    "✓ Gespeichert.": "✓ Saved.", "✓ Gespeichert. Panoptes hat ein paar Dinge passend gemacht.": "✓ Saved. Panoptes adjusted a few things to fit.",
    "Panoptes hat das nicht angenommen. Die Seite lädt den Stand neu.": "Panoptes did not accept that. The page reloads the current state.",
    "Alles auf den Standard zurücksetzen? Deine Anordnung geht dabei verloren.": "Reset everything to the default? Your arrangement will be lost.",
    "✓ Zurückgesetzt.": "✓ Reset.", "Der Launcher ist im Auto installiert.": "The launcher is installed in the car.",
    "Der Launcher ist im Auto noch nicht installiert. Das geht nur am Auto.": "The launcher is not installed in the car yet. That can only be done in the car.",
    "Der Launcher ist jetzt am Bildschirm im Auto offen.": "The launcher is now open on the car screen.",
    "Das hat nicht geklappt. Bitte noch einmal versuchen.": "That did not work. Please try again.",
    "Das Cockpit erreicht sich selbst nicht – bitte neu starten.": "The Cockpit cannot reach itself – please restart it.",
    "Das hat nicht geklappt.": "That did not work.",
    "Updates": "Updates", "Panoptes im Auto": "Panoptes in the car", "Panoptes-Launcher": "Panoptes launcher", "EV-Cockpit": "EV-Cockpit",
    "Hier sehen Sie, ob es neue Versionen gibt. Installiert wird nur, wenn Sie es bestätigen.":
        "Here you can see whether there are new versions. Nothing is installed unless you confirm it.",
    "Dafür braucht das Cockpit die Kopplung „Steuern einrichten“ (Startseite) und Panoptes ab 0.1.26.1.":
        "The Cockpit needs the “Set up control” pairing (home page) and Panoptes 0.1.26.1 or newer for this.",
    "Panoptes aktualisieren": "Update Panoptes", "Ja, jetzt aktualisieren": "Yes, update now", "Abbrechen": "Cancel", "Sende …": "Sending …",
    "Panoptes wird jetzt aktualisiert. Wächter und Verbindung sind ca. 3–8 Minuten weg.":
        "Panoptes will now be updated. Guard and connection are gone for about 3–8 minutes.",
    LAUNCHER_NUR_AM_AUTO: "The launcher update is only possible in the car at the moment.", "Der Launcher ist aktuell.": "The launcher is up to date.",
    "Neue Version": "New version", "ist da.": "is available.", "Das Cockpit ist aktuell": "The Cockpit is up to date", "Version": "Version",
    "Die Suche nach Updates ist aus (Einstellungen).": "Checking for updates is off (Settings).", "Herunterladen": "Download",
    "Erst mit Panoptes verbinden (Mehr → Einstellungen).": "Connect to Panoptes first (More → Settings).",
}
