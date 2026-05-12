"""Intercambio térmico geotérmico y sinergia con ósmosis (LSS) y bomba de calor.

La temperatura estable del agua de entrada (≈20–25 °C) reduce presión en membranas RO
y evita choque térmico radicular al mezclar con nutrición (N/K).
"""
from __future__ import annotations

import math
from typing import Any, Literal

RO_OPTIMAL_MIN_C = 20.0
RO_OPTIMAL_MAX_C = 25.0


def calculate_thermal_exchange(
    depth: float,
    ground_temp: float,
    fluid_velocity: float,
    *,
    fluid_specific_heat_j_kgk: float = 4180.0,
    density_kg_m3: float = 1025.0,
    characteristic_length_m: float = 0.15,
) -> dict[str, Any]:
    """Flujo térmico efectivo por m² de intercambiador (modelo compacto para control en tiempo real).

    Profundidad modula estabilidad térmica del suelo; velocidad del fluido escala convección.
    """
    depth_m = max(1.0, float(depth))
    tg = float(ground_temp)
    v = max(0.05, min(3.0, float(fluid_velocity)))
    ntu = 1.0 - math.exp(-0.12 * depth_m * v)
    delta_t_drive = max(0.5, abs(tg - 10.0))
    q_wm2 = density_kg_m3 * fluid_specific_heat_j_kgk * v * characteristic_length_m * ntu * (delta_t_drive / 25.0)
    q_wm2 = round(min(8000.0, max(5.0, q_wm2)), 2)
    return {
        "heat_flux_w_m2": q_wm2,
        "effective_ntu": round(ntu, 4),
        "depth_m": round(depth_m, 2),
        "ground_temp_c": tg,
        "fluid_velocity_m_s": round(v, 3),
    }


def estimate_heat_pump_cop(
    source_temp_c: float,
    sink_temp_c: float = 35.0,
    *,
    carnot_fraction: float = 0.42,
) -> float:
    """COP efectivo acotado (bomba de calor geotérmica)."""
    tc = max(1.0, source_temp_c + 273.15)
    th = sink_temp_c + 273.15
    if th <= tc:
        return 4.2
    cop_carnot = th / (th - tc)
    cop = min(6.5, max(2.2, carnot_fraction * cop_carnot))
    return round(cop, 2)


def osmosis_inlet_thermal_advisory(
    water_inlet_temp_c: float,
    ground_temp_10m_c: float,
    depth_m: float,
    fluid_velocity_m_s: float,
) -> dict[str, Any]:
    """Vincula T entrada RO con geotermia: pre-calentar si T < óptimo; estabilizar ozono en verano."""
    tw = float(water_inlet_temp_c)
    tg = float(ground_temp_10m_c)
    exch = calculate_thermal_exchange(depth_m, tg, fluid_velocity_m_s)
    q = exch["heat_flux_w_m2"]
    delta_lift_c = min(8.0, q / 420.0)
    est_after_preheat = min(RO_OPTIMAL_MAX_C + 2, tw + delta_lift_c)
    action: Literal["none", "geothermal_preheat", "geothermal_cooling_sink", "maintain_band"]
    ro_energy_saving_pct: float
    if tw < RO_OPTIMAL_MIN_C:
        action = "geothermal_preheat"
        ro_energy_saving_pct = round(15.0 + min(5.0, (RO_OPTIMAL_MIN_C - tw) * 0.8), 1)
    elif tw > 28.0 and tg < tw - 3:
        action = "geothermal_cooling_sink"
        ro_energy_saving_pct = 8.0
    elif RO_OPTIMAL_MIN_C <= tw <= RO_OPTIMAL_MAX_C:
        action = "maintain_band"
        ro_energy_saving_pct = 0.0
    else:
        action = "none"
        ro_energy_saving_pct = 5.0
    return {
        "action": action,
        "water_inlet_temp_c": tw,
        "target_ro_band_c": [RO_OPTIMAL_MIN_C, RO_OPTIMAL_MAX_C],
        "estimated_temp_after_geothermal_c": round(est_after_preheat, 2),
        "ro_pressure_energy_saving_pct_est": ro_energy_saving_pct,
        "heat_flux_w_m2": q,
        "nutrient_absorption_note": "Nitrato/potasio: evitar salto termico > 6 C vs solucion radicular.",
    }


def solar_surplus_kw_estimate(
    irradiance_wm2: float | None,
    solar_ghi_kwh_m2_annual: float,
    assumed_array_m2: float = 48.0,
    baseline_load_kw: float = 2.5,
) -> float:
    """Estimación de excedente solar instantáneo (kW) para priorizar carga del intercambiador."""
    if irradiance_wm2 is not None and irradiance_wm2 > 0:
        gross_kw = (irradiance_wm2 / 1000.0) * assumed_array_m2 * 0.18
    else:
        peak_factor = min(1.0, solar_ghi_kwh_m2_annual / 1800.0)
        gross_kw = 12.0 * peak_factor
    return round(max(0.0, gross_kw - baseline_load_kw), 2)
