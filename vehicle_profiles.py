"""Local multi-vehicle profiles. No credentials stored or returned.

BYD legacy configuration remains unchanged; external manufacturer data comes
from evcc. Profiles are metadata only and cannot send vehicle commands.
"""
import json
import os
import re
from pathlib import Path

SUPPORTED_SOURCES = ("evcc", "byd")
MAX_PROFILES = 32


def normalize_profile(data):
    if not isinstance(data, dict):
        raise ValueError("Profile must be an object")
    ident = str(data.get("id", "")).strip()
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", ident):
        raise ValueError("Invalid profile ID")
    title = str(data.get("title", "")).strip()
    brand = str(data.get("brand", "")).strip()
    source = str(data.get("source", "evcc")).strip()
    external_id = str(data.get("external_id", "")).strip()
    if not title or len(title) > 100 or len(brand) > 60:
        raise ValueError("Invalid vehicle name or brand")
    if source not in SUPPORTED_SOURCES:
        raise ValueError("Unsupported vehicle source")
    if len(external_id) > 128:
        raise ValueError("External ID too long")
    return {"id": ident, "title": title, "brand": brand,
            "source": source, "external_id": external_id}


def read_profiles(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or len(raw) > MAX_PROFILES:
        raise ValueError("Invalid profile file")
    profiles = [normalize_profile(item) for item in raw]
    if len({p["id"] for p in profiles}) != len(profiles):
        raise ValueError("Duplicate vehicle IDs")
    return profiles


def write_profiles(path, profiles):
    if not isinstance(profiles, list) or len(profiles) > MAX_PROFILES:
        raise ValueError("Too many profiles")
    normalized = [normalize_profile(p) for p in profiles]
    if len({p["id"] for p in normalized}) != len(normalized):
        raise ValueError("Duplicate vehicle IDs")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as file:
        json.dump(normalized, file, ensure_ascii=False, indent=2)
        file.flush()
        os.fsync(file.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return normalized


def combine_profiles(saved, evcc_vehicles, legacy_byd=None):
    """Return per-vehicle details with explicit supported capabilities."""
    by_id = {}
    for item in evcc_vehicles:
        if not isinstance(item, dict):
            continue
        key = str(item.get("id", ""))
        if not key:
            continue
        by_id[key] = item
    profiles = list(saved)
    referenced = {p["external_id"] or p["id"] for p in profiles if p["source"] == "evcc"}
    for external in by_id.values():
        key = str(external["id"])
        if key not in referenced:
            profiles.append({"id": key, "title": str(external.get("title") or key),
                             "brand": "", "source": "evcc", "external_id": key})

    result = []
    for profile in profiles:
        source = profile["source"]
        if source == "byd":
            live = legacy_byd or {}
            details = {"soc": live.get("soc"), "range_km": live.get("real_range_km"),
                       "charging": live.get("charging") == "ON"}
            features = live.get("_features") if isinstance(live.get("_features"), dict) else {}
            has_telemetry = any(live.get(key) is not None
                                for key in ("soc", "real_range_km", "charging", "odometer"))
            capabilities = {"telemetry": has_telemetry,
                            "remote_commands": any(bool(value) for value in features.values())}
        else:
            live = by_id.get(profile["external_id"] or profile["id"], {})
            details = {k: live.get(k) for k in ("soc", "range_km", "charging",
                                               "connected", "loadpoint", "charge_power_w")}
            capabilities = {"telemetry": bool(live), "remote_commands": False}
        result.append({**profile, **details, "capabilities": capabilities,
                       "online": bool(live)})
    return result
