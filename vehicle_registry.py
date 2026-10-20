"""Normalize multiple vehicles from evcc, independently of car manufacturer.

EV-Cockpit's native BYD view stays intact. evcc vehicles are external,
read-only profiles and may represent Audi, VW, BYD or other supported makes.
"""
def normalize_vehicles(state):
    configured = state.get("vehicles") or {}
    points = state.get("loadpoints") or []
    vehicles = {}
    if isinstance(configured, dict):
        for key, value in configured.items():
            if not isinstance(value, dict):
                continue
            vehicles[str(key)] = {
                "id": str(key), "title": value.get("title") or str(key),
                "source": "evcc", "soc": value.get("soc"),
                "capacity_kwh": value.get("capacity"),
                "range_km": value.get("range"), "icon": value.get("icon"),
                "connected": False, "charging": False, "loadpoint": None,
                "charge_power_w": None,
            }
    if isinstance(points, list):
        for i, point in enumerate(points):
            if not isinstance(point, dict) or not point.get("vehicleName"):
                continue
            name = str(point["vehicleName"])
            v = vehicles.setdefault(name, {
                "id": name, "title": point.get("vehicleTitle") or name,
                "source": "evcc", "soc": None, "capacity_kwh": None,
                "range_km": None, "icon": None, "connected": False,
                "charging": False, "loadpoint": None, "charge_power_w": None,
            })
            v.update({
                "title": point.get("vehicleTitle") or v["title"],
                "soc": point.get("vehicleSoc") if point.get("vehicleSoc") is not None else v["soc"],
                "range_km": point.get("vehicleRange") if point.get("vehicleRange") is not None else v["range_km"],
                "connected": bool(point.get("connected")),
                "charging": bool(point.get("charging")),
                "loadpoint": point.get("title") or f"Ladepunkt {i+1}",
                "charge_power_w": point.get("chargePower"),
            })
    return list(vehicles.values())
