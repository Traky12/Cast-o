"""Sinergia híbrida: excedente solar prioriza intercambiador geotérmico; COP y ósmosis."""
from __future__ import annotations

from backend.geothermal_engine import (
    estimate_heat_pump_cop,
    osmosis_inlet_thermal_advisory,
    solar_surplus_kw_estimate,
    calculate_thermal_exchange,
)

from .models import FederatedMetricsEnvelope, SensorNormalized


def enrich_envelope_with_geothermal_solar(
    env: FederatedMetricsEnvelope,
    sn: SensorNormalized,
) -> FederatedMetricsEnvelope:
    surplus = solar_surplus_kw_estimate(sn.irradiance_wm2, sn.solar_ghi_kwh_m2)
    cop: float | None = None
    q_wm2: float | None = None
    prio = False
    osmosis: dict | None = None
    if sn.ground_temperature_10m is not None:
        v = 0.55
        if sn.delta_t_fluid is not None:
            v = max(0.15, min(2.8, 0.35 + abs(sn.delta_t_fluid) / 14.0))
        exch = calculate_thermal_exchange(10.0, sn.ground_temperature_10m, v)
        q_wm2 = float(exch["heat_flux_w_m2"])
        cop = estimate_heat_pump_cop(sn.ground_temperature_10m)
        hp = (sn.heat_pump_status or "").lower()
        idle_like = hp in ("", "idle", "off", "standby", "none")
        prio = surplus > 5.0 and (idle_like or hp == "heating")
        if sn.water_inlet_temp_c is not None:
            osmosis = osmosis_inlet_thermal_advisory(
                sn.water_inlet_temp_c,
                sn.ground_temperature_10m,
                10.0,
                v,
            )
    lue = env.land_use_efficiency
    if lue is None and sn.panel_tilt_deg is not None and sn.albedo is not None:
        lue = round(1.0 + (sn.panel_tilt_deg / 90.0) * 0.12 * (1.0 - sn.albedo), 3)
    return env.model_copy(
        update={
            "cop_geothermal": cop,
            "thermal_exchange_w_m2": q_wm2,
            "solar_surplus_kw_est": surplus,
            "prioritize_geothermal_exchanger": bool(prio) if sn.ground_temperature_10m is not None else None,
            "osmosis_inlet_advisory": osmosis,
            "lue_land_use_efficiency": lue,
        }
    )
