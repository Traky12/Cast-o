# -*- coding: utf-8 -*-
"""
Huella de carbono por región — CASTÚO Global v9.0 (ISO 14064).
Factores de emisión por país/región (kg CO₂/kWh) para cálculo estandarizado.
"""
from __future__ import annotations

from typing import Any, Dict

# Factores de emisión por país/región (kg CO2/kWh) — mix energético típico
EMISSION_FACTORS: Dict[str, float] = {
    "ES": 0.25,   # España
    "FR": 0.05,   # Francia (nuclear)
    "DE": 0.40,   # Alemania
    "IT": 0.35,
    "PT": 0.30,
    "US": 0.45,   # EE.UU.
    "CL": 0.35,   # Chile
    "AR": 0.40,   # Argentina
    "BR": 0.20,   # Brasil (hidroeléctrica)
    "JP": 0.50,   # Japón
    "CN": 0.70,   # China
    "IN": 0.80,   # India
    "KR": 0.55,   # Corea del Sur
    "ZA": 0.90,   # Sudáfrica
    "MA": 0.65,   # Marruecos
    "AU": 0.60,   # Australia
    "NZ": 0.15,   # Nueva Zelanda (renovables)
}
DEFAULT_FACTOR = 0.5


def get_energy_use(farm_id: str) -> float:
    """Obtiene consumo energético (kWh) para la finca. En producción: API IoT/ERP."""
    # Stub: en producción consultar sensores o base de datos
    return 0.0


def calculate_carbon_footprint(
    farm_id: str,
    country_code: str,
    energy_kwh: float | None = None,
) -> Dict[str, Any]:
    """
    Calcula huella de carbono según ISO 14064 y factores locales (kg CO₂).

    Args:
        farm_id: Identificador de finca.
        country_code: Código ISO 3166-1 alpha-2 (ES, US, JP, etc.).
        energy_kwh: Consumo en kWh (opcional; si no se pasa, se usa get_energy_use).

    Returns:
        dict: country_code, energy_kwh, emission_factor, co2_kg, standard.
    """
    code = (country_code or "").upper()[:2]
    factor = EMISSION_FACTORS.get(code, DEFAULT_FACTOR)
    energy = energy_kwh if energy_kwh is not None else get_energy_use(farm_id)
    co2_kg = energy * factor
    return {
        "farm_id": farm_id,
        "country_code": code or "XX",
        "energy_kwh": round(energy, 2),
        "emission_factor_kg_co2_per_kwh": factor,
        "co2_kg": round(co2_kg, 2),
        "standard": "ISO 14064-1",
    }
