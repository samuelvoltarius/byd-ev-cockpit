"""Read-only go-eCharger diagnostics for EV-Cockpit.

This module intentionally never sends charging or phase-switch commands.
It reads the go-e local HTTP API v2, validates input and returns a compact
snapshot for comparing charger behaviour with an independent grid meter.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from network_safety import open_lan_url, private_ipv4


@dataclass(frozen=True)
class GoESnapshot:
    charging_state: int | None
    phases_raw: Any
    total_power_w: float | None
    raw: dict[str, Any]


def _safe_host(host: str) -> str:
    """Accept LAN IP addresses only; never proxy arbitrary URLs."""
    return private_ipv4(host, "go-e IP")


def fetch_goe_snapshot(host: str, timeout: float = 3.0) -> GoESnapshot:
    """Read go-e API v2 status. Does not modify charger settings.

    Typical go-e status keys: car (state), nrg (meter values), pha (phase bits).
    nrg[11] is total charging power in kW on supported API v2 firmwares.
    Check the firmware's API mapping before relying on this value.
    """
    host = _safe_host(host)
    if not 0 < timeout <= 10:
        raise ValueError("timeout must be between 0 and 10 seconds")
    url = f"http://{host}/api/status?filter=car,nrg,pha"
    with open_lan_url(url, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"go-e returned HTTP {response.status}")
        data = response.read(65537)
    if len(data) > 65536:
        raise ValueError("go-e response too large")
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError("invalid go-e status response")
    nrg = payload.get("nrg")
    power = None
    if isinstance(nrg, list) and len(nrg) > 11:
        value = nrg[11]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            power = float(value) * 1000
    car = payload.get("car")
    return GoESnapshot(
        charging_state=car if isinstance(car, int) and not isinstance(car, bool) else None,
        phases_raw=payload.get("pha"),
        total_power_w=power,
        raw=payload,
    )
