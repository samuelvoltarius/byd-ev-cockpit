"""Optional read-only evcc energy backend.

evcc owns charger/PV control. EV-Cockpit only reads evcc's local API.
No dependency on evcc is required when this adapter is unused.
"""
from __future__ import annotations

import ipaddress
import json
import urllib.request


def validate_evcc_address(host: str, port: int = 7070) -> str:
    ip = ipaddress.ip_address(host.strip())
    if ip.version != 4 or not ip.is_private or ip.is_loopback or ip.is_link_local:
        raise ValueError("Use a private IPv4 address for your evcc instance")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Invalid evcc port")
    return f"http://{ip}:{port}"


def get_evcc_state(host: str, port: int = 7070, timeout: float = 3.0) -> dict:
    """Return a normalized energy snapshot with source data for diagnostics.

    State key availability depends on evcc version/configuration.
    Missing values remain null rather than being guessed.
    """
    base = validate_evcc_address(host, port)
    with urllib.request.urlopen(base + "/api/state", timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"evcc HTTP {response.status}")
        raw = response.read(262145)
    if len(raw) > 262144:
        raise ValueError("evcc response too large")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid evcc state")
    # evcc versions expose state as an object; retain raw state for future adapters.
    state = data.get("result", data)
    if not isinstance(state, dict):
        raise ValueError("Invalid evcc result")
    from vehicle_registry import normalize_vehicles
    return {
        "backend": "evcc",
        "vehicles": normalize_vehicles(state),
        "site": {
            "grid_w": state.get("gridPower"),
            "pv_w": state.get("pvPower"),
            "battery_w": state.get("batteryPower"),
            "home_w": state.get("homePower"),
        },
        "loadpoints": state.get("loadpoints", []),
        "raw": state,
    }
