# -*- coding: utf-8 -*-
"""API para control de drones (MAVLink/ArduPilot) y telemetría."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..dronica import missions

router = APIRouter(prefix="/drones", tags=["drones"])


class StartMissionBody(BaseModel):
    mission_id: Optional[int] = None
    drone_id: Optional[str] = None
    mission_type: str = "mapping"
    waypoints: List[Dict[str, Any]] = []


class TelemetryBody(BaseModel):
    lat: float
    lon: float
    alt: float
    battery: float


@router.post("/{drone_id}/start_mission")
async def start_mission(drone_id: int, body: StartMissionBody):
    """Inicia una misión en el drone (Odoo llama aquí; delegamos a dronica)."""
    mission_id = str(body.mission_id or 0)
    waypoints = body.waypoints or []
    try:
        missions.run_mission(mission_id, str(drone_id), waypoints)
        return {"status": "success", "mission_id": mission_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{drone_id}/telemetry")
async def update_telemetry(drone_id: int, body: TelemetryBody):
    """Recibe telemetría del drone y la reenvía a Odoo (si está configurado)."""
    odoo_url = __import__("os").environ.get("ODOO_URL", "")
    if odoo_url:
        try:
            import urllib.request
            import json
            data = json.dumps(
                {
                    "lat": body.lat,
                    "lon": body.lon,
                    "alt": body.alt,
                    "battery": body.battery,
                }
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{odoo_url}/castu/drones/{drone_id}/telemetry",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
    return {"status": "success"}
