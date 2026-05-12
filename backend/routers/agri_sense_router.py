"""API del núcleo AGRI-SENSE-CORE: ciclo de control, estado y auditoría."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agri_sense.schemas import UltraPrecisionSchema
from backend.system_orchestrator import (
    control_cycle,
    get_audit_tail,
    get_state,
    manual_intervention,
)

router = APIRouter(prefix="/api/agri-sense", tags=["AGRI-SENSE-CORE"])


class ControlCycleResponse(BaseModel):
    audit_id: str
    state: dict[str, Any]
    cycle_duration_s: float


class ManualInterventionRequest(BaseModel):
    action: str = Field(..., description="force_ozone_cycle | set_cop_geothermal | set_geothermal_setpoint")
    cop: float | None = None
    temp_c: float | None = None


@router.post("/control-cycle", response_model=ControlCycleResponse)
async def post_control_cycle(sensors: UltraPrecisionSchema) -> ControlCycleResponse:
    """Ejecuta un ciclo del bucle de retroalimentación negativa (atómico)."""
    result = await control_cycle(sensors)
    return ControlCycleResponse(
        audit_id=result["audit_id"],
        state=result["state"],
        cycle_duration_s=result["cycle_duration_s"],
    )


@router.get("/state")
async def get_agri_sense_state() -> dict[str, Any]:
    """Estado actual del orquestador para dashboard/telemetría."""
    s = get_state()
    return {
        "npk_valve_closed": s.npk_valve_closed,
        "heat_pump_flow_factor": s.heat_pump_flow_factor,
        "ozone_injection_enabled": s.ozone_injection_enabled,
        "cop_geothermal": s.cop_geothermal,
        "last_ground_temp_c": s.last_ground_temp_c,
        "last_conductivity_ms_cm": s.last_conductivity_ms_cm,
        "irrigation_demand_factor": s.irrigation_demand_factor,
        "root_cause_last": s.root_cause_last,
        "quantum_confidence_score": s.quantum_confidence_score,
        "energy_alloc_ro_kw": s.energy_alloc_ro_kw,
        "energy_alloc_geo_kw": s.energy_alloc_geo_kw,
        "energy_alloc_o3_kw": s.energy_alloc_o3_kw,
        "quantum_backend_last": s.quantum_backend_last,
        "last_irradiance_wm2": s.last_irradiance_wm2,
    }


@router.get("/audit")
async def get_agri_sense_audit(n: int = 10) -> list[dict[str, Any]]:
    """Últimos n eventos de auditoría (código de colores por severity)."""
    return get_audit_tail(min(100, max(1, n)))


@router.post("/manual-intervention")
async def post_manual_intervention(body: ManualInterventionRequest) -> dict[str, Any]:
    """Intervención manual: forzar ciclo Ozono o ajustar COP/setpoint geotérmico."""
    kwargs: dict[str, Any] = {}
    if body.cop is not None:
        kwargs["cop"] = body.cop
    if body.temp_c is not None:
        kwargs["temp_c"] = body.temp_c
    out = manual_intervention(body.action, **kwargs)
    if "error" in out:
        raise HTTPException(status_code=400, detail=out)
    return out
