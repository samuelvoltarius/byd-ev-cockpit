# -*- coding: utf-8 -*-
"""1.24: EINE Planer-Ansicht im Cockpit (PLANER_VERTRAG.md, plan-ergebnis/1): Ziel -> planen -> Etappen/Ladestopps (Ladestand, Kosten,
Live-Belegung) -> Ankunft inkl. Verkehr -> "Reicht es noch?" -> grosser Knopf "Ins Auto" (an-auto mit plan_id).

Nachbau statt Einbetten: Der Geraete-Schluessel bleibt im Cockpit-Prozess, der Browser spricht nur mit dem eigenen Python-Teil.
Ratenbremse wie im Vertrag §1: hoechstens 10 Planungen je Minute und nur EINE laufende Planung; nie automatisch, nur auf Tipp.
Antwortet der Planer noch mit der vollen Form (Server-§6 noch nicht gebaut), wird die bisherige Kurzform umgerechnet (plan_id = None,
"Ins Auto" schickt dann wie bisher den Plan mit)."""
import re
import threading
import time

VERTRAG = "plan-ergebnis/1"


def _zahl(v, nachkomma=None):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return round(float(v), nachkomma) if nachkomma is not None else v


def _text(v, n=200):
    return str(v)[:n] if isinstance(v, (str, int, float)) and not isinstance(v, bool) and str(v) != "" else None


def _zeit(v):
    v = str(v or "")
    return v[:30] if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?([+-]\d{2}:?\d{2}|Z)?", v) else None


def _ort(o):
    o = o if isinstance(o, dict) else {}
    return {"name": _text(o.get("name"), 80), "lat": _zahl(o.get("lat"), 6), "lon": _zahl(o.get("lon"), 6)}


def _etappe(e):
    if not isinstance(e, dict):
        return None
    art = e.get("art") if e.get("art") in ("laden", "zwischenziel", "ziel") else "laden"
    bz = e.get("bezahlen") if isinstance(e.get("bezahlen"), dict) else {}
    lv = e.get("live") if isinstance(e.get("live"), dict) else None
    return {"nr": _zahl(e.get("nr")), "art": art, "name": _text(e.get("name"), 80) or ("Ladestopp" if art == "laden" else "Zwischenziel"),
            "lat": _zahl(e.get("lat"), 6), "lon": _zahl(e.get("lon"), 6), "km": _zahl(e.get("km"), 1),
            "ankunft_ca": _zeit(e.get("ankunft_ca")), "abfahrt_ca": _zeit(e.get("abfahrt_ca")),
            "soc_an": _zahl(e.get("soc_an"), 0), "soc_ab": _zahl(e.get("soc_ab"), 0), "lade_min": _zahl(e.get("lade_min"), 0),
            "aufenthalt_min": _zahl(e.get("aufenthalt_min"), 0), "kwh": _zahl(e.get("kwh"), 1), "kw": _zahl(e.get("kw"), 0),
            "cpo": _text(e.get("cpo"), 60), "kosten": _zahl(e.get("kosten"), 2), "waehrung": _text(e.get("waehrung"), 3) or "EUR",
            "karte": _text(bz.get("karte"), 60), "tarif": _text(bz.get("tarif"), 60), "eigene_karte": bz.get("eigene_karte") is True,
            "preis_hinweis": _text(bz.get("hinweis"), 120), "preis_unsicher": e.get("preis_unsicher") is True,
            "live": {"frei": _zahl(lv.get("frei")), "ladepunkte": _zahl(lv.get("ladepunkte")), "stand_min": _zahl(lv.get("stand_min")),
                     "quelle": _text(lv.get("quelle"), 60)} if lv else None,
            "geschlossen": e.get("geoeffnet_bei_ankunft") is False, "umweg_km": _zahl(e.get("umweg_km"), 1)}


def _geo(g):
    out = []
    for p in (g if isinstance(g, list) else [])[:2000]:
        if isinstance(p, (list, tuple)) and len(p) >= 2 and _zahl(p[0]) is not None and _zahl(p[1]) is not None:
            out.append([round(float(p[0]), 5), round(float(p[1]), 5)])
    return out


def ergebnis(d):
    """plan-ergebnis/1 -> was die Ansicht zeigt. Unbekanntes bleibt None (Vertrag: ehrlich, nie geraten)."""
    z = d.get("zeit") if isinstance(d.get("zeit"), dict) else {}
    a = d.get("akku") if isinstance(d.get("akku"), dict) else {}
    k = d.get("kosten") if isinstance(d.get("kosten"), dict) else {}
    v = d.get("verkehr") if isinstance(d.get("verkehr"), dict) else None
    nf = d.get("nicht_fahrbar") if isinstance(d.get("nicht_fahrbar"), dict) else None
    sp = d.get("sperren") if isinstance(d.get("sperren"), dict) else {}
    pid = d.get("plan_id")
    return {"vertrag": VERTRAG, "plan_id": pid if re.fullmatch(r"p_[A-Za-z0-9_-]{4,80}", str(pid or "")) else None,
            "gueltig_bis": _zeit(d.get("gueltig_bis")), "start": _ort(d.get("start")), "ziel": _ort(d.get("ziel")),
            "fahrzeug": _text((d.get("fahrzeug") or {}).get("name") if isinstance(d.get("fahrzeug"), dict) else None, 80),
            "km": _zahl(d.get("km"), 1),
            "zeit": {"abfahrt_ca": _zeit(z.get("abfahrt_ca")), "ankunft_ca": _zeit(z.get("ankunft_ca")), "fahr_min": _zahl(z.get("fahr_min"), 0),
                     "lade_min": _zahl(z.get("lade_min"), 0), "aufenthalt_min": _zahl(z.get("aufenthalt_min"), 0),
                     "gesamt_min": _zahl(z.get("gesamt_min"), 0), "verkehr_min": _zahl(z.get("verkehr_min"), 0),
                     "inkl_verkehr": z.get("inkl_verkehr") is True},
            "akku": {"soc_start": _zahl(a.get("soc_start"), 0), "soc_ankunft": _zahl(a.get("soc_ankunft"), 0), "reserve": _zahl(a.get("reserve"), 0)},
            "fahrbar": d.get("fahrbar") is not False and nf is None,
            "nicht_fahrbar": {"text": _text(nf.get("text"), 300), "von_km": _zahl(nf.get("von_km"), 0), "bis_km": _zahl(nf.get("bis_km"), 0)} if nf else None,
            "etappen": [x for x in (_etappe(e) for e in (d.get("etappen") or [])[:40]) if x],
            "kosten": {"summe": _zahl(k.get("summe"), 2), "sicher": _zahl(k.get("sicher"), 2), "unsicher": _zahl(k.get("unsicher"), 2),
                       "ohne_preis": _zahl(k.get("ohne_preis"), 0), "waehrung": _text(k.get("waehrung"), 3) or "EUR"},
            "verkehr": {"verzoegerung_min": _zahl(v.get("verzoegerung_min"), 0), "eingerechnet": v.get("eingerechnet") is True,
                        "quelle": _text(v.get("quelle"), 60),
                        "meldungen": [{"titel": _text(m.get("titel"), 80), "km": _zahl(m.get("km"), 1), "verzoegerung_min": _zahl(m.get("verzoegerung_min"), 0)}
                                      for m in (v.get("meldungen") or [])[:10] if isinstance(m, dict)]} if v else None,
            "sperren": {"meldungen_n": _zahl(sp.get("meldungen_n")), "voll_gesperrt_n": _zahl(sp.get("voll_gesperrt_n"))},
            "warnungen": [w for w in (_text(x, 300) for x in (d.get("warnungen") or [])[:8]) if w],
            "hinweise": [w for w in (_text(x, 300) for x in (d.get("hinweise") or [])[:8]) if w],
            "quellen": [w for w in (_text(x, 80) for x in (d.get("quellen") or [])[:12]) if w],
            "geometrie": _geo(d.get("geometrie")),
            # Planer 754c099: Rueckfall-Routing (z. B. Ziel in einer Fussgaengerzone) -> nur ein Hinweis, kein Fehler; der Satz steht in warnungen
            "routing_rueckfall": bool((d.get("route") or {}).get("routing_rueckfall")) if isinstance(d.get("route"), dict) else False}


def aus_alt(k, start_name="", ziel_name=""):
    """Bisherige Kurzform (route_planer.kurz, volle Planer-Antwort) -> dieselbe Form wie ergebnis(); plan_id fehlt."""
    fp = k.get("fahrtplan") or {}
    et = []
    for s in k.get("stopps") or []:
        et.append({"art": "laden", "name": s.get("name"), "lat": s.get("lat"), "lon": s.get("lon"), "km": s.get("km"), "ankunft_ca": s.get("ankunft_ca"),
                   "soc_an": s.get("soc_an"), "soc_ab": s.get("soc_ab"), "lade_min": s.get("dauer_min"), "kwh": s.get("kwh"), "kw": s.get("kw"),
                   "cpo": s.get("betreiber"), "kosten": s.get("preis"), "bezahlen": {"karte": s.get("karte"), "hinweis": s.get("preis_quelle")},
                   "geoeffnet_bei_ankunft": False if s.get("geschlossen") else None})
    for z in k.get("zwischenziele") or []:
        et.append({"art": "zwischenziel", "name": z.get("name"), "km": z.get("km_auf_route"), "ankunft_ca": z.get("ankunft_ca"),
                   "abfahrt_ca": z.get("abfahrt_ca"), "soc_an": z.get("soc_ankunft"), "aufenthalt_min": z.get("aufenthalt_min")})
    et.sort(key=lambda e: e.get("km") if isinstance(e.get("km"), (int, float)) else 1e9)
    for i, e in enumerate(et):
        e["nr"] = i + 1
    d = {"plan_id": None, "start": {"name": start_name}, "ziel": {"name": ziel_name}, "fahrzeug": {"name": k.get("fahrzeug")}, "km": k.get("km"),
         "zeit": {"abfahrt_ca": fp.get("abfahrt_ca"), "ankunft_ca": fp.get("ankunft_ca"), "fahr_min": fp.get("fahr_min") or k.get("minuten"),
                  "lade_min": fp.get("lade_min") if fp else k.get("lade_min"), "aufenthalt_min": fp.get("aufenthalt_min"), "gesamt_min": fp.get("gesamt_min")},
         "akku": {"soc_start": k.get("soc_start"), "soc_ankunft": k.get("soc_ankunft")}, "etappen": et,
         "kosten": {"summe": k.get("kosten")}, "warnungen": k.get("warnungen") or [], "hinweise": [fp.get("hinweis")] if fp.get("hinweis") else [],
         "geometrie": k.get("geometrie") or []}
    r = ergebnis(d)
    r["vertrag"] = None
    return r


def reicht(e):
    """'Reicht es noch?' in einem Satz (REGEL 50+). ja = ankommen ueber der Reserve, knapp = darunter, nein = so nicht fahrbar."""
    if not e.get("fahrbar"):
        t = (e.get("nicht_fahrbar") or {}).get("text") or "Mit den Ladesäulen auf dieser Strecke kommst du so nicht ans Ziel."
        return {"stufe": "nein", "satz": t}
    an = (e.get("akku") or {}).get("soc_ankunft")
    res = (e.get("akku") or {}).get("reserve")
    n = sum(1 for x in e.get("etappen") or [] if x.get("art") == "laden")
    if an is None:
        return {"stufe": "unbekannt", "satz": "Der Routenplaner sagt nicht, mit wie viel Akku du ankommst."}
    stopps = "ohne Ladestopp" if n == 0 else ("mit einem Ladestopp" if n == 1 else "mit %d Ladestopps" % n)
    if res is not None and an < res:
        return {"stufe": "knapp", "an": an, "res": res, "n": n,
                "satz": "Knapp: Du kommst %s mit etwa %d %% an. Das ist unter deiner Reserve von %d %%." % (stopps, an, res)}
    return {"stufe": "ja", "an": an, "res": res, "n": n, "satz": "Ja, das reicht. Du kommst %s mit etwa %d %% an." % (stopps, an)}


class Bremse:
    """PLANER_VERTRAG §1: plan 10/min je IP, nur auf Tipp, hoechstens 1 laufende Planung je Geraet."""

    def __init__(self, je_minute=10, uhr=time.time):
        self.je_minute, self.uhr, self.zeiten, self.lock = je_minute, uhr, [], threading.Lock()

    def los(self):
        """-> None (darf planen; danach fertig() rufen) oder ein Satz, warum nicht."""
        if not self.lock.acquire(blocking=False):
            return "Es läuft schon eine Planung. Bitte warten, bis sie fertig ist."
        jetzt = self.uhr()
        self.zeiten = [t for t in self.zeiten if jetzt - t < 60]
        if len(self.zeiten) >= self.je_minute:
            self.lock.release()
            return "Zu viele Planungen in kurzer Zeit – bitte eine Minute warten."
        self.zeiten.append(jetzt)
        return None

    def fertig(self):
        self.lock.release()


SEITE = """<!doctype html><html lang=de><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>EV-Cockpit — Route planen</title>
<meta name=evc-neu content=1>
<style>x</style></head><body><div class=w>
<h1>Route planen</h1>
<div class=sub>Ziel eingeben, planen lassen, ins Auto schicken. Ladestopps sucht der Routenplaner selbst.</div>
<div class=card id=p_nicht style="display:none" data-collapse=off><h3>Noch nicht verbunden</h3>
 <div class=sub>Das Cockpit muss einmal mit dem Routenplaner verbunden werden.</div><a class=btn href="/setup">Mit dem Routenplaner verbinden</a></div>
<div class=card id=p_eingabe data-collapse=off>
 <label for=p_ziel>Wohin?</label><input id=p_ziel autocomplete=off placeholder="Ort oder Adresse, z. B. Graz">
 <div id=p_vorschlag class=pvor></div>
 <div class=sub id=p_start style="margin-top:12px"></div>
 <details id=p_andersd><summary>Anderer Start</summary><input id=p_startein autocomplete=off placeholder="Ort oder Adresse"><div id=p_startvor class=pvor></div></details>
 <button type=button id=p_los onclick="planen()" style="width:100%;margin-top:14px;min-height:60px;font-size:18px">Route berechnen</button>
 <div class=msg id=p_msg></div>
</div>
<div id=p_erg style="display:none">
 <div class="card preicht" id=p_reicht data-collapse=off><div class=prgross id=p_reichtsatz></div>
  <div class=pzahlen id=p_zahlen></div>
  <button type=button id=p_auto onclick="insAuto()" style="width:100%;min-height:64px;font-size:19px;margin-top:14px">🚗 Ins Auto</button>
  <div class=msg id=p_automsg></div></div>
 <div class=card id=p_kartek><h3>Karte</h3><div id=p_karte></div></div>
 <div class=card id=p_etk><h3>Etappen<span class=abzustand id=p_etz></span></h3><div id=p_etappen></div></div>
 <div class=card id=p_vk><h3>Verkehr<span class=abzustand id=p_vz></span></h3><div id=p_verkehr></div></div>
 <div class=card id=p_hk><h3>Hinweise<span class=abzustand id=p_hz></span></h3><div id=p_hinweise></div></div>
 <div class=sub id=p_quellen style="font-size:12.5px"></div>
</div>
</div>
<style>
.pvor{display:flex;flex-direction:column;gap:6px;margin-top:6px}.pvor button{justify-content:flex-start;text-align:left;min-height:48px;background:rgba(255,255,255,.085);color:var(--txt);border:1px solid var(--line)}
.preicht{border-width:2px}.preicht.ja{border-color:var(--lime)}.preicht.knapp{border-color:var(--amber)}.preicht.nein{border-color:var(--coral)}
.prgross{font:700 22px 'Sora',system-ui,sans-serif;line-height:1.3}
.pzahlen{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:14px}
.pzahlen div{background:rgba(4,16,27,.45);border:1px solid var(--line);border-radius:14px;padding:10px 12px}.pzahlen small{display:block;color:var(--ink-2);font-size:12.5px}
.pzahlen b{font:700 20px 'Sora',sans-serif}
.pet{display:flex;gap:12px;border-top:1px solid var(--line);padding:12px 2px}.pet:first-child{border-top:0}
.pet i{font-style:normal;flex:0 0 34px;height:34px;border-radius:50%;display:grid;place-items:center;background:rgba(181,242,61,.18);color:var(--lime);font-weight:700}
.pet.zz i{background:rgba(95,214,230,.16);color:var(--aqua)}.pet b{font-size:16.5px}.pet .z{color:var(--ink-2);font-size:14px;margin-top:3px}.pet .w{color:var(--amber);font-size:14px;margin-top:3px}
#p_karte svg{width:100%;height:auto;background:#071a2b;border-radius:14px;border:1px solid var(--line)}
</style>
<script>
const el=id=>document.getElementById(id);let ZIEL=null,START=null,T={},PLANT=false,PLAN=null;
function esc(t){return String(t==null?'':t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function uhr(z){if(!z)return '–';const d=new Date(z);return isNaN(d)?'–':d.toLocaleTimeString(window.__LANG__==='en'?'en-GB':'de-AT',{hour:'2-digit',minute:'2-digit'})+(new Date().toDateString()!==d.toDateString()?' ('+d.toLocaleDateString(window.__LANG__==='en'?'en-GB':'de-AT',{weekday:'short'})+')':'');}
function dauer(m){if(m==null)return '–';m=Math.round(m);return m>=60?Math.floor(m/60)+' h '+String(m%60).padStart(2,'0')+' min':m+' min';}
function geld(v,w){return v==null?__T('Preis unbekannt'):v.toLocaleString(window.__LANG__==='en'?'en-GB':'de-AT',{minimumFractionDigits:2,maximumFractionDigits:2})+' '+(w==='EUR'||!w?'€':w);}
// Ortssuche: erst ab 3 Zeichen und 300 ms Pause (Vertrag §1, orte 120/min)
function suche(feld,box,setzen){el(feld).addEventListener('input',()=>{const q=el(feld).value.trim();setzen(null);clearTimeout(T[feld]);el(box).innerHTML='';if(q.length<3)return;
 T[feld]=setTimeout(async()=>{try{const d=await (await fetch('/route/orte',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({q:q})})).json();
  el(box).innerHTML='';(d.orte||[]).forEach(o=>{const b=document.createElement('button');b.type='button';b.textContent=o.name;b.onclick=()=>{el(feld).value=o.name;setzen(o);el(box).innerHTML='';};el(box).appendChild(b);});
  if(d.ok===false)el(box).textContent=__T(d.error||'');}catch(e){}},300);});}
suche('p_ziel','p_vorschlag',o=>ZIEL=o);suche('p_startein','p_startvor',o=>START=o);
async function vorgaben(){try{const v=await (await fetch('/rp/vorgaben')).json();
 if(!v.verbunden){el('p_nicht').style.display='';el('p_eingabe').style.display='none';return;}
 el('p_start').textContent=v.auto?__T('Start: Mein Auto')+(v.soc!=null?' · '+__T('Ladestand')+' '+v.soc+' %':'')+(v.fahrzeug?' · '+v.fahrzeug:''):__T('Die Position des Autos ist gerade unbekannt. Bitte unten einen Start eingeben.');
 if(!v.auto)el('p_andersd').open=true;}catch(e){}}
async function planen(){if(PLANT)return;const m=el('p_msg');
 if(!ZIEL){m.textContent='⚠️ '+__T('Bitte ein Ziel aus der Liste antippen.');return;}
 if(el('p_andersd').open&&el('p_startein').value.trim()&&!START){m.textContent='⚠️ '+__T('Bitte den Start aus der Liste antippen.');return;}
 PLANT=true;el('p_los').disabled=true;m.textContent='⏳ '+__T('Ich plane die Route. Das kann bis zu einer Minute dauern.');
 const ab=new AbortController(),tt=setTimeout(()=>ab.abort(),250000);
 try{const r=await (await fetch('/rp/plan',{method:'POST',signal:ab.signal,headers:{'Content-Type':'application/json'},
   body:JSON.stringify({ziel:[ZIEL.lat,ZIEL.lon],ziel_name:ZIEL.name,start:START?[START.lat,START.lon]:null,start_name:START?START.name:''})})).json();
  if(!r.ok){m.textContent='⚠️ '+__T(r.error||'Das hat nicht geklappt.');}else{m.textContent='';PLAN=r.plan;zeige(r.plan,r.reicht);}}
 catch(e){m.textContent='⚠️ '+__T(e.name==='AbortError'?'Der Routenplaner hat zu lange gebraucht. Bitte noch einmal.':'Das Cockpit erreicht sich selbst nicht – bitte neu starten.');}
 clearTimeout(tt);PLANT=false;el('p_los').disabled=false;}
// 'Reicht es noch?' als Satz mit Zahlen (uebersetzbar); Stufe und Zahlen rechnet der Cockpit-Server (planer_ansicht.reicht)
function reichtSatz(r){if(r.stufe!=='ja'&&r.stufe!=='knapp')return __T(r.satz);
 const st=r.n===0?__T('ohne Ladestopp'):r.n===1?__T('mit einem Ladestopp'):__T('mit {n} Ladestopps').replace('{n}',r.n);
 return __T(r.stufe==='ja'?'Ja, das reicht. Du kommst {stopps} mit etwa {an} % an.':'Knapp: Du kommst {stopps} mit etwa {an} % an. Das ist unter deiner Reserve von {res} %.').replace('{stopps}',st).replace('{an}',r.an).replace('{res}',r.res);}
function zeige(p,rc){el('p_erg').style.display='';el('p_automsg').textContent='';
 const k=el('p_reicht');k.className='card preicht '+rc.stufe;el('p_reichtsatz').textContent=(rc.stufe==='ja'?'✅ ':rc.stufe==='nein'?'⛔ ':'⚠️ ')+reichtSatz(rc);
 const z=p.zeit||{},v=[];
 v.push(['Ankunft ca.',uhr(z.ankunft_ca),z.inkl_verkehr?__T('inkl. Verkehr')+(z.verkehr_min?' (+'+z.verkehr_min+' min)':''):__T('ohne Verkehr')]);
 v.push(['Strecke',p.km!=null?Math.round(p.km)+' km':'–',dauer(z.gesamt_min!=null?z.gesamt_min:z.fahr_min)]);
 const nl=(p.etappen||[]).filter(e=>e.art==='laden').length,lst=nl+' '+(nl===1?__T('Ladestopp'):__T('Ladestopps'));
 v.push(['Laden',dauer(z.lade_min),lst]);
 const ko=p.kosten||{};v.push(['Kosten ca.',ko.summe!=null?geld(ko.summe,ko.waehrung):'–',ko.unsicher?__T('davon unsicher')+' '+geld(ko.unsicher,ko.waehrung):(ko.ohne_preis?ko.ohne_preis+' '+__T('ohne Preis'):'')]);
 el('p_zahlen').innerHTML=v.map(x=>'<div><small>'+esc(__T(x[0]))+'</small><b>'+esc(x[1])+'</b><small>'+esc(x[2]||'')+'</small></div>').join('');
 el('p_auto').disabled=!p.fahrbar;
 const et=p.etappen||[];el('p_etz').textContent=lst;
 el('p_etappen').innerHTML=et.length?et.map(e=>{const zz=e.art!=='laden',z=[];
  if(e.km!=null)z.push(__T('bei km')+' '+Math.round(e.km));if(e.ankunft_ca)z.push(__T('Ankunft')+' '+uhr(e.ankunft_ca));
  if(!zz){z.push((e.soc_an!=null?e.soc_an+' %':'?')+' → '+(e.soc_ab!=null?e.soc_ab+' %':'?'));if(e.lade_min!=null)z.push(dauer(e.lade_min));if(e.kw)z.push(e.kw+' kW');}
  else if(e.aufenthalt_min)z.push(__T('Aufenthalt')+' '+dauer(e.aufenthalt_min));
  const z2=[];if(!zz){z2.push(geld(e.kosten,e.waehrung)+(e.karte?' · '+e.karte:'')+(e.preis_unsicher?' · '+__T('Preis unsicher'):''));
   if(e.live&&e.live.ladepunkte)z2.push(__T('Jetzt frei')+': '+(e.live.frei!=null?e.live.frei:'?')+'/'+e.live.ladepunkte+(e.live.stand_min!=null?' ('+__T('Stand vor')+' '+e.live.stand_min+' min)':''));}
  return '<div class="pet'+(zz?' zz':'')+'"><i>'+(zz?'📍':esc(e.nr))+'</i><div><b>'+esc(e.name)+(e.cpo&&e.cpo!==e.name?' · '+esc(e.cpo):'')+'</b><div class=z>'+esc(z.join(' · '))+'</div>'
   +(z2.length?'<div class=z>'+esc(z2.join(' · '))+'</div>':'')+(e.geschlossen?'<div class=w>⚠️ '+esc(__T('Bei Ankunft vermutlich geschlossen'))+'</div>':'')+'</div></div>';}).join(''):'<div class=sub>'+esc(__T('Kein Ladestopp nötig.'))+'</div>';
 const vk=p.verkehr;el('p_vz').textContent=vk?(vk.verzoegerung_min?'+'+vk.verzoegerung_min+' min':__T('frei')):__T('unbekannt');
 el('p_verkehr').innerHTML=vk?((vk.meldungen||[]).map(x=>'<div class=pet><i>⚠️</i><div><b>'+esc(x.titel||'')+'</b><div class=z>'+esc((x.km!=null?__T('bei km')+' '+Math.round(x.km):'')+(x.verzoegerung_min?' · +'+x.verzoegerung_min+' min':''))+'</div></div></div>').join('')||'<div class=sub>'+esc(__T('Keine Staus gemeldet.'))+'</div>')
  +(vk.quelle?'<div class=sub style="font-size:12.5px">'+esc(vk.quelle)+'</div>':''):'<div class=sub>'+esc(__T('Zum Verkehr gibt es gerade keine Daten. Die Ankunft ist ohne Stau gerechnet.'))+'</div>';
 const hw=(p.warnungen||[]).map(x=>'ⓘ '+x).concat(p.hinweise||[]);if(p.routing_rueckfall&&!(p.warnungen||[]).length)hw.unshift('ⓘ '+__T('Das letzte Stück ist vereinfacht berechnet, zum Beispiel weil das Ziel in einer Fußgängerzone liegt.'));el('p_hz').textContent=hw.length?String(hw.length):'';
 el('p_hinweise').innerHTML=hw.length?hw.map(x=>'<div class=pet><div>'+esc(x)+'</div></div>').join(''):'<div class=sub>'+esc(__T('Keine.'))+'</div>';
 el('p_quellen').textContent=(p.quellen||[]).length?__T('Daten')+': '+p.quellen.join(' · '):'';
 karte(p);el('p_reicht').scrollIntoView({block:'start',behavior:'smooth'});}
// Einfache Karte ohne Kartenkacheln (keine fremden Server): Strecke als Linie, Ladestopps nummeriert
function karte(p){const g=(p.geometrie||[]).slice(),pk=[];(p.etappen||[]).forEach(e=>{if(e.lat!=null&&e.lon!=null)pk.push(e);});
 [p.start,p.ziel].forEach(o=>{if(o&&o.lat!=null)g.push([o.lat,o.lon]);});pk.forEach(e=>g.push([e.lat,e.lon]));
 const box=el('p_karte');if(g.length<2){el('p_kartek').style.display='none';return;}el('p_kartek').style.display='';
 let a=Infinity,b=-Infinity,c=Infinity,d=-Infinity;g.forEach(q=>{a=Math.min(a,q[0]);b=Math.max(b,q[0]);c=Math.min(c,q[1]);d=Math.max(d,q[1]);});
 const k=Math.cos((a+b)/2*Math.PI/180),W=600,H=Math.max(220,Math.min(520,W*((b-a)||.01)/(((d-c)||.01)*k))),pad=24;
 const sx=(W-2*pad)/(((d-c)*k)||.01),sy=(H-2*pad)/((b-a)||.01),s=Math.min(sx,sy);
 const P=q=>[(pad+((q[1]-c)*k)*s).toFixed(1),(H-pad-(q[0]-a)*s).toFixed(1)];
 const linie=(p.geometrie||[]).length>1?'<polyline fill=none stroke="#5FD6E6" stroke-width=4 stroke-linejoin=round points="'+p.geometrie.map(q=>P(q).join(',')).join(' ')+'"/>':'';
 const pkt=(q,f,t)=>{const x=P(q);return '<circle cx='+x[0]+' cy='+x[1]+' r=11 fill="'+f+'" stroke="#071a2b" stroke-width=2/><text x='+x[0]+' y='+(+x[1]+4)+' text-anchor=middle font-size=11 font-weight=700 fill="#071a2b">'+esc(t)+'</text>';};
 box.innerHTML='<svg viewBox="0 0 '+W+' '+H.toFixed(0)+'" role=img aria-label="'+esc(__T('Strecke'))+'">'+linie+(p.start&&p.start.lat!=null?pkt([p.start.lat,p.start.lon],'#EAF6F8','S'):'')
  +pk.map(e=>pkt([e.lat,e.lon],e.art==='laden'?'#B5F23D':'#5FD6E6',e.art==='laden'?e.nr:'•')).join('')+(p.ziel&&p.ziel.lat!=null?pkt([p.ziel.lat,p.ziel.lon],'#FFC266','Z'):'')+'</svg>';}
async function insAuto(){const m=el('p_automsg'),b=el('p_auto');b.disabled=true;m.textContent='⏳';
 try{const r=await (await fetch('/rp/an-auto',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).json();
  m.textContent=r.ok?'✓ '+__T('Gesendet. Im Auto erscheint „Route übernehmen?“ – dort einmal tippen.'):'⚠️ '+__T(r.error||'Das hat nicht geklappt.');}
 catch(e){m.textContent='⚠️ '+__T('Das Cockpit erreicht sich selbst nicht – bitte neu starten.');}
 b.disabled=false;}
el('p_ziel').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();planen();}});
vorgaben();
</script></body></html>"""

EN = {
    "Route planen": "Plan a route", "Ziel eingeben, planen lassen, ins Auto schicken. Ladestopps sucht der Routenplaner selbst.":
        "Enter a destination, let it plan, send it to the car. The route planner finds charging stops itself.",
    "Noch nicht verbunden": "Not connected yet", "Das Cockpit muss einmal mit dem Routenplaner verbunden werden.": "The Cockpit has to be connected to the route planner once.",
    "Mit dem Routenplaner verbinden": "Connect to the route planner", "Wohin?": "Where to?", "Anderer Start": "Different start",
    "Route berechnen": "Calculate route", "🚗 Ins Auto": "🚗 To the car", "Karte": "Map", "Etappen": "Stages", "Verkehr": "Traffic", "Hinweise": "Notes",
    "Preis unbekannt": "Price unknown", "Start: Mein Auto": "Start: my car", "Ladestand": "Charge",
    "Die Position des Autos ist gerade unbekannt. Bitte unten einen Start eingeben.": "The car's position is unknown right now. Please enter a start below.",
    "Bitte ein Ziel aus der Liste antippen.": "Please tap a destination in the list.", "Bitte den Start aus der Liste antippen.": "Please tap the start in the list.",
    "Ich plane die Route. Das kann bis zu einer Minute dauern.": "Planning the route. This can take up to a minute.",
    "Der Routenplaner hat zu lange gebraucht. Bitte noch einmal.": "The route planner took too long. Please try again.",
    "Ankunft ca.": "Arrival approx.", "inkl. Verkehr": "incl. traffic", "ohne Verkehr": "without traffic", "Strecke": "Distance", "Laden": "Charging",
    "Ladestopp": "charging stop", "Kosten ca.": "Cost approx.", "davon unsicher": "of which uncertain", "ohne Preis": "without price", "Ladestopps": "charging stops",
    "bei km": "at km", "Preis unsicher": "price uncertain", "Jetzt frei": "Free now", "Stand vor": "updated",
    "Bei Ankunft vermutlich geschlossen": "Probably closed on arrival", "Kein Ladestopp nötig.": "No charging stop needed.", "frei": "clear",
    "unbekannt": "unknown", "Keine Staus gemeldet.": "No traffic jams reported.",
    "Zum Verkehr gibt es gerade keine Daten. Die Ankunft ist ohne Stau gerechnet.": "There is no traffic data right now. Arrival is calculated without jams.",
    "Keine.": "None.", "Daten": "Data",
    "Das letzte Stück ist vereinfacht berechnet, zum Beispiel weil das Ziel in einer Fußgängerzone liegt.": "The last part is calculated in a simplified way, for example because the destination is in a pedestrian zone.",
    "Gesendet. Im Auto erscheint „Route übernehmen?“ – dort einmal tippen.": "Sent. The car shows “Take over route?” – tap it there once.",
    "Mit den Ladesäulen auf dieser Strecke kommst du so nicht ans Ziel.": "With the chargers on this route you will not reach the destination like this.",
    "Der Routenplaner sagt nicht, mit wie viel Akku du ankommst.": "The route planner does not say how much battery you will arrive with.",
    "Es läuft schon eine Planung. Bitte warten, bis sie fertig ist.": "A route is already being planned. Please wait until it is done.",
    "Zu viele Planungen in kurzer Zeit – bitte eine Minute warten.": "Too many plans in a short time – please wait a minute.",
    "ohne Ladestopp": "without a charging stop", "mit einem Ladestopp": "with one charging stop", "mit {n} Ladestopps": "with {n} charging stops",
    "Ja, das reicht. Du kommst {stopps} mit etwa {an} % an.": "Yes, that is enough. You arrive {stopps} with about {an} %.",
    "Knapp: Du kommst {stopps} mit etwa {an} % an. Das ist unter deiner Reserve von {res} %.":
        "Tight: you arrive {stopps} with about {an} %. That is below your reserve of {res} %.",
}
