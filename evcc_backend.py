"""Optional evcc energy backend.

evcc owns charger/PV control and its safety (phases, current limits). EV-Cockpit reads evcc's
local API and - only for loadpoints the user explicitly unlocked, default off - may set the
charge mode (off/now/minpv/pv) and the charge limit through evcc. Nothing else is ever written.
No dependency on evcc is required when this adapter is unused.
"""
from __future__ import annotations

import json
from network_safety import open_lan_url, private_ipv4


def validate_evcc_address(host: str, port: int = 7070) -> str:
    ip = private_ipv4(host, "evcc host")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Invalid evcc port")
    return f"http://{ip}:{port}"


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
        "chargeDuration", "effectiveLimitSoc", "limitSoc", "vehicleOdometer",
    )
    return [{key: point.get(key) for key in allowed if key in point}
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
        raw = response.read(262145)
    if len(raw) > 262144:
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


MODES = ("off", "now", "minpv", "pv")


def set_loadpoint(host: str, port: int, lp: int, mode=None, limit_soc=None, timeout: float = 4.0,
                  read_state=None) -> dict:
    """Set mode OR charge limit of loadpoint ``lp`` (1-based, as in evcc's API), then read it back.

    Returns {"ok": bool, "mode", "limit_soc"} with the values evcc reports AFTER the change.
    """
    base = validate_evcc_address(host, port)
    if not isinstance(lp, int) or isinstance(lp, bool) or not 1 <= lp <= 20:
        raise ValueError("Invalid loadpoint")
    if (mode is None) == (limit_soc is None):
        raise ValueError("Set either mode or limit_soc")
    if mode is not None:
        if mode not in MODES:
            raise ValueError("Invalid mode")
        path = f"/api/loadpoints/{lp}/mode/{mode}"
    else:
        if not isinstance(limit_soc, int) or isinstance(limit_soc, bool) or not 20 <= limit_soc <= 100:
            raise ValueError("Charge limit must be 20-100 %")
        path = f"/api/loadpoints/{lp}/limitsoc/{limit_soc}"
    with open_lan_url(base + path, timeout=timeout, method="POST") as response:
        if response.status != 200:
            raise ValueError(f"evcc HTTP {response.status}")
    state = (read_state or get_evcc_state)(host, port)
    points = state.get("loadpoints") or []
    if len(points) < lp:
        raise ValueError("Loadpoint not found after change")
    point = points[lp - 1]
    now_mode, now_limit = point.get("mode"), point.get("limitSoc")
    ok = (now_mode == mode) if mode is not None else (now_limit == limit_soc)
    return {"ok": ok, "mode": now_mode, "limit_soc": now_limit}
