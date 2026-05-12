# -*- coding: utf-8 -*-
"""
API REST para dashboard hidropónico remoto (CTAEX): zonas, sensores, actuadores, parámetros.
Autenticación: Keycloak JWT (mismo flujo que compliance) o AUTH_DISABLED en laboratorio.
"""
from __future__ import annotations

import os

from backend.services.edge_service import EdgeService
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.api.security.keycloak import TokenData, get_current_user
from backend.security.ot_actuator_guard import (
    OTActuatorPolicyError,
    check_actuator_command,
    check_emergency_stop,
    record_denial,
)
from backend.services.hydro_zone_store import ZoneManager, get_zone_manager


router = APIRouter(tags=["Hidroponía remota CTAEX"])


def _auth_disabled() -> bool:
    return os.getenv("AUTH_DISABLED", "").strip().lower() in {"1", "true", "yes"}


async def require_hydro_viewer(user: TokenData = Depends(get_current_user)) -> TokenData:
    if _auth_disabled():
        return user
    allowed = {"viewer", "technician", "admin", "owner", "dpo"}
    if not any(r in allowed for r in user.roles):
        raise HTTPException(403, detail="Rol insuficiente para consultar zonas")
    return user


async def require_hydro_operator(user: TokenData = Depends(get_current_user)) -> TokenData:
    if _auth_disabled():
        return user
    allowed = {"technician", "admin", "owner"}
    if not any(r in allowed for r in user.roles):
        raise HTTPException(403, detail="Rol insuficiente para control de actuadores")
    return user


class ActuatorControlBody(BaseModel):
    actuator_id: str
    actuator_type: str = Field(description="Etiqueta lógica: valvula_agua, ventilador, etc.")
    state: bool
    duration: int = Field(0, ge=0, le=86400)
    zone_id: str = Field("zone_cannabis_1", description="Zona objetivo")
    intensity: Optional[float] = Field(None, ge=0, le=100, description="Solo luz_led, 0-100")


class ParameterUpdate(BaseModel):
    parameter: str
    value: float


class SensorReadingIn(BaseModel):
    sensor_id: str
    value: float
    unit: str = "unknown"


@router.get("/api/zones/{zone_id}")
async def get_zone(zone_id: str, zm: ZoneManager = Depends(get_zone_manager), _: TokenData = Depends(require_hydro_viewer)):
    z = zm.get_zone_status(zone_id)
    if not z:
        raise HTTPException(404, "Zona no encontrada")
    return z


@router.post("/api/actuators/control")
async def control_actuator(
    body: ActuatorControlBody,
    zm: ZoneManager = Depends(get_zone_manager),
    user: TokenData = Depends(require_hydro_operator),
):
    roles = list(user.roles or [])
    subject = user.sub or user.email or "hydro_operator"
    try:
        check_actuator_command(
            body.zone_id,
            body.actuator_id,
            body.state,
            roles=roles,
            subject=subject,
        )
    except OTActuatorPolicyError as e:
        record_denial(e.code)
        raise HTTPException(status_code=403, detail={"code": e.code, "message": e.detail}) from e
    try:
        out = zm.control_actuator(
            body.zone_id,
            body.actuator_id,
            body.state,
            body.duration,
            intensity=body.intensity,
        )
        if os.getenv("OT_EDGE_FORWARD", "").strip().lower() in {"1", "true", "yes"}:
            try:
                cmd, val = EdgeService.map_bool_to_command(body.state, body.intensity)
                EdgeService.validate_forward_payload(
                    body.zone_id,
                    body.actuator_id,
                    energize=body.state,
                    command=cmd,
                    value=val,
                )
                EdgeService.send_to_actuator(
                    body.actuator_id,
                    cmd,
                    val,
                    os.getenv("OT_EDGE_DEFAULT_PROTOCOL", "mqtt"),
                    os.getenv(
                        "OT_EDGE_DEFAULT_TOPIC",
                        f"castuo/{body.zone_id}/{body.actuator_id}/cmd",
                    ),
                    zone_id=body.zone_id,
                )
                out["edge_forward"] = "stub"
            except ValueError as ev:
                raise HTTPException(status_code=403, detail=str(ev)) from ev
        return out
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e


@router.post("/api/zones/{zone_id}/actuators/emergency_stop")
async def emergency_stop(
    zone_id: str,
    zm: ZoneManager = Depends(get_zone_manager),
    user: TokenData = Depends(require_hydro_operator),
):
    subject = user.sub or user.email or "hydro_operator"
    try:
        check_emergency_stop(subject=subject)
    except OTActuatorPolicyError as e:
        record_denial(e.code)
        raise HTTPException(status_code=403, detail={"code": e.code, "message": e.detail}) from e
    try:
        return zm.emergency_stop(zone_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e


@router.get("/api/sensors/{zone_id}/readings")
async def sensor_readings(
    zone_id: str,
    sensor_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=2000),
    zm: ZoneManager = Depends(get_zone_manager),
    _: TokenData = Depends(require_hydro_viewer),
):
    try:
        sid, rows = zm.get_readings(zone_id, sensor_id, limit)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
    return {"zone_id": zone_id, "sensor_id": sid or sensor_id, "readings": rows}


@router.post("/api/sensors/{zone_id}/readings")
async def post_sensor_reading(
    zone_id: str,
    reading: SensorReadingIn,
    zm: ZoneManager = Depends(get_zone_manager),
    _: TokenData = Depends(require_hydro_operator),
):
    try:
        zm.add_sensor_reading(zone_id, reading.sensor_id, reading.value, reading.unit)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
    return {"status": "ok", "sensor_id": reading.sensor_id, "zone_id": zone_id}


@router.post("/api/zones/{zone_id}/parameters")
async def update_parameter(
    zone_id: str,
    body: ParameterUpdate,
    zm: ZoneManager = Depends(get_zone_manager),
    _: TokenData = Depends(require_hydro_operator),
):
    try:
        zm.update_ideal_parameter(zone_id, body.parameter, body.value)
    except ValueError as e:
        msg = str(e)
        code = 400 if "Parámetro no válido" in msg else 404
        raise HTTPException(code, detail=msg) from e
    z = zm.get_zone_status(zone_id)
    return {"status": "success", "zone_id": zone_id, "parametros_ideales": z.get("parametros_ideales") if z else {}}
