"""Optional evcc energy backend.

evcc owns charger/PV control and its safety (phases, current limits). EV-Cockpit reads evcc's
local API and - only for loadpoints the user explicitly unlocked, default off - may set the
charge mode (off/now/minpv/pv) and the charge limit through evcc. Nothing else is ever written.
No dependency on evcc is required when this adapter is unused.
"""
from __future__ import annotations

import json
import urllib.error
from network_safety import open_lan_url, private_ziel


def validate_evcc_address(host: str, port: int = 7070) -> str:
    """WALLBOX_VERTRAG §2: private IPv4 (RFC 1918, 100.64/10) oder ein Name, der nur privat aufloest."""
    schema, ziel = private_ziel(host, "evcc host")
    if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
        raise ValueError("Invalid evcc port")
    return f"{schema}://{ziel}:{port}"


def modus_von(mode, always_charge):
    """Lademodus wie gesendet (off/now/minpv/pv). Neues evcc meldet 'smart': pv = smart + alwaysCharge off,
    minpv = smart + alwaysCharge on/once. Aeltere evcc melden pv/minpv direkt. Unklar -> None."""
    if mode == "smart":
        if always_charge in ("on", "once", True):
            return "minpv"
        if always_charge in ("off", False):
            return "pv"
        return None
    return mode if mode in MODES else None


def art_von(point):
    """Nur 'wallbox' ist steuerbar. Waermepumpe/Heizstab: limitSoc ist dort eine Temperatur."""
    if point.get("chargerFeatureHeating"):
        return "heizung"
    if point.get("chargerFeatureIntegratedDevice") and not point.get("vehicleName"):
        return "geraet"
    return "wallbox"


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _nested_power(state, current_key, legacy_key):
    current = state.get(current_key)
    if isinstance(current, dict):
        value = _number(current.get("power"))
        if value is not None:
            return value
    return _number(state.get(legacy_key))


def normalize_loadpoints(state):
    """Expose only stable, display-relevant fields from evcc loadpoints."""
    points = state.get("loadpoints") or []
    if not isinstance(points, list):
        return []
    allowed = (
        "name", "title", "vehicleName", "vehicleTitle", "vehicleSoc",
        "vehicleRange", "connected", "charging", "chargePower", "mode",
        "phasesActive", "sessionSolarPercentage", "chargedEnergy",
        "chargeDuration", "effectiveLimitSoc", "limitSoc", "vehicleOdometer", "alwaysCharge",
    )
    return [dict({key: point.get(key) for key in allowed if key in point},
                 art=art_von(point), modus=modus_von(point.get("mode"), point.get("alwaysCharge")))
            for point in points if isinstance(point, dict)]


def get_evcc_state(host: str, port: int = 7070, timeout: float = 3.0) -> dict:
    """Return a normalized energy snapshot with source data for diagnostics.

    State key availability depends on evcc version/configuration.
    Missing values remain null rather than being guessed.
    """
    base = validate_evcc_address(host, port)
    with open_lan_url(base + "/api/state", timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"evcc HTTP {response.status}")
        raw = response.read(524289)
    if len(raw) > 524288:
        raise ValueError("evcc response too large")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid evcc state")
    # evcc has used both a wrapped and an unwrapped state response.
    state = data.get("result", data)
    if not isinstance(state, dict):
        raise ValueError("Invalid evcc result")
    from vehicle_registry import normalize_vehicles
    return {
        "backend": "evcc",
        "vehicles": normalize_vehicles(state),
        "site": {
            "title": str(state.get("siteTitle") or ""),
            "grid_w": _nested_power(state, "grid", "gridPower"),
            "pv_w": _number(state.get("pvPower")) if _number(state.get("pvPower")) is not None
                    else _nested_power(state, "pv", "pvPower"),
            "battery_w": _nested_power(state, "battery", "batteryPower"),
            "battery_soc": _number(state.get("battery", {}).get("soc"))
                           if isinstance(state.get("battery"), dict) else None,
            "home_w": _number(state.get("homePower")),
            "tariff_grid": _number(state.get("tariffGrid")),
            "tariff_feed_in": _number(state.get("tariffFeedIn")),
            "green_share_home": _number(state.get("greenShareHome")),
        },
        "loadpoints": normalize_loadpoints(state),
    }


# Fester Code-Schalter (Koordination): Steuern war AUS bis zum Praxistest gegen demo.evcc.io (WALLBOX_VERTRAG §7/§8).
# Auch jetzt nur fuer Ladepunkte, die der Nutzer einzeln freigegeben hat, mit Bestaetigung und Protokoll.
STEUERN_FREIGEGEBEN = True      # Praxistest demo.evcc.io gruen (22.10.2026, WALLBOX_COCKPIT_TESTNACHWEIS.json)

MODES = ("off", "now", "minpv", "pv")


def _post(base, path, timeout):
    try:
        with open_lan_url(base + path, timeout=timeout, method="POST") as response:
            if response.status != 200:
                raise ValueError(f"evcc HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise ValueError("evcc verlangt eine Anmeldung - Steuern geht mit diesem evcc noch nicht") from exc
        raise ValueError(f"evcc HTTP {exc.code}") from exc


def _punkt(state, lp):
    points = state.get("loadpoints") or []
    if len(points) < lp:
        raise ValueError("Ladepunkt nicht gefunden")
    return points[lp - 1]


def pruefe_wert(mode=None, limit_soc=None):
    """Werte VOR der Rueckfrage pruefen (WALLBOX_VERTRAG §5.2.4)."""
    if (mode is None) == (limit_soc is None):
        raise ValueError("Set either mode or limit_soc")
    if mode is not None and mode not in MODES:
        raise ValueError("Invalid mode")
    if limit_soc is not None and (not isinstance(limit_soc, int) or isinstance(limit_soc, bool) or not 20 <= limit_soc <= 100):
        raise ValueError("Charge limit must be 20-100 %")


def set_loadpoint(host: str, port: int, lp: int, mode=None, limit_soc=None, timeout: float = 4.0,
                  read_state=None) -> dict:
    """Set mode OR charge limit of loadpoint ``lp`` (1-based, as in evcc's API), then read it back.

    Returns {"ok": bool, "mode", "mode_roh", "limit_soc"} with the values evcc reports AFTER the change.
    """
    if not STEUERN_FREIGEGEBEN:
        raise PermissionError("Wallbox steuern kommt nach dem Praxistest")
    base = validate_evcc_address(host, port)
    if not isinstance(lp, int) or isinstance(lp, bool) or not 1 <= lp <= 20:
        raise ValueError("Invalid loadpoint")
    pruefe_wert(mode, limit_soc)
    lies = read_state or get_evcc_state
    vorher = _punkt(lies(host, port), lp)
    if (vorher.get("art") or art_von(vorher)) != "wallbox":
        raise PermissionError("Dieser Ladepunkt ist keine Wallbox (Heizung/Gerät) und wird nie gesteuert")
    if mode is not None:
        _post(base, f"/api/loadpoints/{lp}/mode/{mode}", timeout)
        if mode in ("pv", "minpv") and "alwaysCharge" in vorher:
            # Neues evcc: sonst bliebe ein altes 'on' stehen und pv wuerde als minpv zurueckgelesen
            _post(base, f"/api/loadpoints/{lp}/alwayscharge/{'on' if mode == 'minpv' else 'off'}", timeout)
    else:
        _post(base, f"/api/loadpoints/{lp}/limitsoc/{limit_soc}", timeout)
    point = _punkt(lies(host, port), lp)
    now_mode = point.get("modus", modus_von(point.get("mode"), point.get("alwaysCharge")))
    now_limit = point.get("limitSoc")
    ok = (now_mode == mode) if mode is not None else (now_limit == limit_soc)
    return {"ok": ok, "mode": now_mode, "mode_roh": point.get("mode"), "limit_soc": now_limit}
