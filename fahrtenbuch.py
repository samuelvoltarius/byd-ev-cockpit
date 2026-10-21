"""Fahrtenbuch im Cockpit: GET /api/trips von Panoptes ueber die Kopplung (lokal, nur lesend).

Nur durchgereicht: nichts an unseren Server, nichts auf Platte. Koordinaten (startLat/endLat ...) werden NIE
weitergegeben - Panoptes liefert keine Ortsnamen, also zeigt das Cockpit Datum, Zeit, km, Dauer, Verbrauch.
CSV entsteht auf Klick im lokalen Cockpit-Server.
"""
import calendar
import datetime as dt
import io
import re
import urllib.error

SEITE = 100
MONAT = re.compile(r"(\d{4})-(\d{2})")


def monat_grenzen(monat):
    """'2026-10' -> (from_ms, to_ms) in Ortszeit dieses Rechners."""
    m = MONAT.fullmatch(monat or "")
    if not m:
        raise ValueError("Monat als JJJJ-MM")
    j, mo = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        raise ValueError("Monat als JJJJ-MM")
    a = dt.datetime(j, mo, 1)
    b = dt.datetime(j, mo, calendar.monthrange(j, mo)[1], 23, 59, 59, 999000)
    return int(a.timestamp() * 1000), int(b.timestamp() * 1000)


def _zahl(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def knapp(t):
    """Eine Fahrt ohne Koordinaten."""
    km, kwh = _zahl(t.get("distanceKm")), _zahl(t.get("energyUsedKwh"))
    return {"id": t.get("id"), "start": t.get("startTime"), "ende": t.get("endTime"),
            "km": round(km, 1) if km is not None else None,
            "dauer_s": t.get("durationSeconds"),
            "kwh": round(kwh, 2) if kwh is not None else None,
            "verbrauch": round(kwh / km * 100, 1) if km and kwh is not None and km > 0.5 else None,
            "soc_start": t.get("socStart"), "soc_ende": t.get("socEnd"),
            "kosten": round(_zahl(t["tripCost"]), 2) if _zahl(t.get("tripCost")) is not None else None,
            "waehrung": t.get("currency") or "", "temp": t.get("extTempC")}


def liste(pv, monat, offset=0, seite=SEITE):
    """Eine Seite Fahrten eines Monats. -> {ok, fahrten, mehr} | {ok:False, grund}"""
    von, bis = monat_grenzen(monat)
    try:
        d = pv._get("/api/trips?from=%d&to=%d&limit=%d&offset=%d" % (von, bis, seite, max(0, int(offset))))
    except urllib.error.HTTPError as e:
        return {"ok": False, "grund": "zu_alt" if e.code in (403, 404) else "fehler"}
    if d.get("_status") == 403:
        return {"ok": False, "grund": "zu_alt"}       # Kopplung darf die Fahrten (noch) nicht lesen
    roh = d.get("trips") or []
    return {"ok": True, "fahrten": [knapp(t) for t in roh if isinstance(t, dict)], "mehr": len(roh) >= seite}


def alle(pv, monat, hoechstens=2000):
    out, offset = [], 0
    while offset < hoechstens:
        d = liste(pv, monat, offset)
        if not d.get("ok"):
            return d
        out += d["fahrten"]
        if not d["mehr"]:
            break
        offset += SEITE
    return {"ok": True, "fahrten": out}


def csv(fahrten, en=False):
    """CSV fuer Tabellenprogramme: deutsch mit ; und Dezimalkomma, englisch mit , und Punkt."""
    trenn, komma = (",", ".") if en else (";", ",")
    zahl = lambda v: "" if v is None else str(v).replace(".", komma)
    kopf = (["date", "start", "end", "km", "duration_min", "kwh", "kwh_per_100km", "soc_start", "soc_end", "cost", "currency", "temp_c"]
            if en else ["Datum", "Start", "Ende", "km", "Dauer_min", "kWh", "kWh_pro_100km", "Ladestand_Start", "Ladestand_Ende",
                        "Kosten", "Waehrung", "Aussentemp_C"])
    f = io.StringIO()
    f.write(trenn.join(kopf) + "\r\n")
    for t in fahrten:
        a = dt.datetime.fromtimestamp((t["start"] or 0) / 1000)
        e = dt.datetime.fromtimestamp((t["ende"] or 0) / 1000) if t.get("ende") else None
        zeile = [a.strftime("%Y-%m-%d"), a.strftime("%H:%M"), e.strftime("%H:%M") if e else "", zahl(t["km"]),
                 zahl(round(t["dauer_s"] / 60) if t.get("dauer_s") else None), zahl(t["kwh"]), zahl(t["verbrauch"]),
                 zahl(t["soc_start"]), zahl(t["soc_ende"]), zahl(t["kosten"]), (t["waehrung"] or "").replace(trenn, " "), zahl(t["temp"])]
        f.write(trenn.join(zeile) + "\r\n")
    return f.getvalue()
