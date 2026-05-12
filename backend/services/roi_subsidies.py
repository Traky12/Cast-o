# -*- coding: utf-8 -*-
"""
ROI con subvenciones locales — CASTÚO-SYSTEM™ v10.0.
Métricas dinámicas FAO/OCDE/ISO; cálculo por país (PAC UE, USDA, JAS, etc.).
"""
from __future__ import annotations

from typing import Any, Dict

# Subvenciones por código país (€/ha o equivalente; conversión vía exchange)
SUBSIDIES_PER_HA = {
    "ES": 500,
    "FR": 480,
    "DE": 520,
    "US": 300,   # $/ac → se convierte
    "JP": 400,   # ¥/10a
    "BR": 200,   # R$/ha
    "ZA": 150,   # ZAR/ha
    "CL": 180,
    "AR": 160,
    "AU": 220,
    "NZ": 200,
}


def get_base_roi(farm_id: str) -> float:
    """Obtiene ROI base sin subvenciones (desde BD o API interna)."""
    # Stub: en producción consultar reporting o analytics
    return 1.5


def get_local_currency_exchange(country_code: str) -> float:
    """Tipo de cambio a EUR para expresar subsidio en moneda local equivalente."""
    rates = {
        "ES": 1.0, "FR": 1.0, "DE": 1.0,
        "US": 0.92, "JP": 0.0062, "BR": 0.17, "ZA": 0.051, "CL": 0.0010,
        "AR": 0.0010, "AU": 0.60, "NZ": 0.55,
    }
    return rates.get(country_code.upper(), 1.0)


def calculate_roi(farm_id: str, country_code: str) -> Dict[str, Any]:
    """
    Calcula ROI considerando subvenciones locales (PAC 2027, USDA, JAS, Pronaf, DAFF, etc.).
    """
    base_roi = get_base_roi(farm_id)
    subsidy = SUBSIDIES_PER_HA.get(country_code.upper(), 0)
    exchange = get_local_currency_exchange(country_code)
    roi_with_subsidy = base_roi + (subsidy / 1000.0) * exchange  # factor escala
    return {
        "farm_id": farm_id,
        "country_code": country_code,
        "base_roi": base_roi,
        "subsidy_per_ha": subsidy,
        "exchange_to_eur": exchange,
        "roi_with_subsidy": round(roi_with_subsidy, 4),
    }
