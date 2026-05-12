"""Reexport del núcleo agrivoltaico + hibridación geotérmica (COP, excedente solar)."""
from __future__ import annotations

from typing import Any

from backend.agrivoltaic.models import SensorNormalized
from backend.agrivoltaic.service import compute_demo_metrics as _compute_demo_metrics
from backend.agrivoltaic.strategies import DemoAgrivoltaicStrategy
from backend.geothermal_engine import calculate_thermal_exchange, estimate_heat_pump_cop

__all__ = [
    "compute_demo_metrics",
    "compute_hybrid_agrivoltaic_geothermal",
    "calculate_thermal_exchange",
    "estimate_heat_pump_cop",
]


def compute_demo_metrics(solar: float, humidity: float, temp: float) -> dict[str, Any]:
    return _compute_demo_metrics(solar, humidity, temp)


def compute_hybrid_agrivoltaic_geothermal(
    solar_ghi_kwh_m2: float,
    humidity: float,
    temp_c: float,
    *,
    ground_temperature_10m: float | None = None,
    heat_pump_status: str | None = None,
    delta_t_fluid: float | None = None,
    water_inlet_temp_c: float | None = None,
    irradiance_wm2: float | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Métricas agrivoltaicas con COP geotérmico y priorización si hay excedente solar."""
    sn = SensorNormalized(
        solar_ghi_kwh_m2=float(solar_ghi_kwh_m2),
        humidity_pct=float(humidity),
        temp_celsius=float(temp_c),
        irradiance_wm2=irradiance_wm2,
        ground_temperature_10m=ground_temperature_10m,
        heat_pump_status=heat_pump_status,
        delta_t_fluid=delta_t_fluid,
        water_inlet_temp_c=water_inlet_temp_c,
    )
    return DemoAgrivoltaicStrategy().demo_dict(sn)
