"""Dashboard de sinergia: reglas maestras Solar ↔ Agua ↔ Química ↔ Geotermia ↔ Audit."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.geothermal_engine import calculate_thermal_exchange, solar_surplus_kw_estimate

router = APIRouter(prefix="/api/synergy", tags=["Synergy Master"])


class SynergyMasterState(BaseModel):
    """Estado agregado para el tablero Gran Maestro (7 dimensiones)."""

    model_config = ConfigDict(extra="allow")

    solar_surplus_kw: float | None = Field(
        default=None,
        ge=0,
        description="Si null, se estima desde irradiancia/GHI",
    )
    tank_level_pct: float = Field(ge=0, le=100, default=50)
    water_inlet_temp_c: float | None = None
    ground_temperature_10m: float | None = Field(default=None, description="°C a 10 m")
    ph: float | None = Field(default=None, ge=0, le=14)
    ec_ms_cm: float | None = Field(default=None, ge=0, description="Conductividad eléctrica")
    nitrate_ppm: float | None = None
    potassium_ppm: float | None = None
    ozone_generator_temp_c: float | None = None
    heat_pump_status: str | None = None
    delta_t_fluid: float | None = None
    irrigation_pressure_bar: float | None = None
    flow_m3_h: float | None = None
    solar_ghi_kwh_m2: float | None = None
    irradiance_wm2: float | None = None


def evaluate_synergy_rules(state: SynergyMasterState) -> dict[str, Any]:
    """Relaciones causa-efecto entre actuadores (no solo números aislados)."""
    alerts: list[dict[str, Any]] = []
    actuators: list[dict[str, Any]] = []
    ghi = state.solar_ghi_kwh_m2 or 1500.0
    solar_ex = (
        float(state.solar_surplus_kw)
        if state.solar_surplus_kw is not None
        else solar_surplus_kw_estimate(state.irradiance_wm2, ghi)
    )

    if solar_ex > 5.0 and state.tank_level_pct < 20.0:
        actuators.append(
            {
                "id": "osmosis_inverse",
                "reason": "Sinergia energética: excedente solar y depósito bajo",
                "priority": "high",
                "solar_surplus_kw": solar_ex,
            }
        )
    if state.ph is not None and state.ph > 7.5:
        alerts.append(
            {
                "id": "nutrient_manager_nitrate_lock",
                "severity": "warning",
                "message": "pH > 7.5: riesgo de bloqueo de nitratos; revisar dosificación N/K",
                "action": "hold_nitrate_dose_until_ph_below_7.2",
            }
        )
    if state.water_inlet_temp_c is not None and state.ground_temperature_10m is not None:
        v = 0.6 if not state.delta_t_fluid else max(0.2, min(2.0, 0.3 + abs(state.delta_t_fluid) / 15.0))
        geo = calculate_thermal_exchange(10.0, state.ground_temperature_10m, v)
        if state.water_inlet_temp_c < 18.0:
            actuators.append(
                {
                    "id": "geothermal_preheat_ro",
                    "heat_flux_w_m2": geo["heat_flux_w_m2"],
                    "target_band_c": [20, 25],
                }
            )
    if state.ozone_generator_temp_c is not None and state.ozone_generator_temp_c > 35:
        alerts.append(
            {
                "id": "ozone_stability",
                "message": "O3 más estable en frío; considerar sumidero geotérmico de calor",
                "severity": "info",
            }
        )
    return {
        "solar_surplus_kw_est": solar_ex,
        "alerts": alerts,
        "recommended_actuators": actuators,
        "audit_context": "synergy_master_v1",
    }


@router.post("/master-dashboard")
async def post_master_dashboard(state: SynergyMasterState) -> dict[str, Any]:
    """Relaciones entre Solar_Excedent, depósito, pH, geotermia y ósmosis (Gran Maestro)."""
    return evaluate_synergy_rules(state)
