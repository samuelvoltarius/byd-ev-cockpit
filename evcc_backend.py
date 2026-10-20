"""Optional read-only evcc energy backend.

evcc owns charger/PV control. EV-Cockpit only reads evcc's local API.
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
        "phasesActive", "sessionSolarPercentage",
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
            "grid_w": _nested_power(state, "grid", "gridPower"),
            "pv_w": _number(state.get("pvPower")) if _number(state.get("pvPower")) is not None
                    else _nested_power(state, "pv", "pvPower"),
            "battery_w": _nested_power(state, "battery", "batteryPower"),
            "battery_soc": _number(state.get("battery", {}).get("soc"))
                           if isinstance(state.get("battery"), dict) else None,
            "home_w": _number(state.get("homePower")),
        },
        "loadpoints": normalize_loadpoints(state),
    }
