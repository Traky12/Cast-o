# -*- coding: utf-8 -*-
"""Cálculo de huella de carbono y ahorro vs materiales convencionales (kg CO₂e)."""
from datetime import datetime
from typing import Optional

# kg CO₂e por kg de material
EMISSION_FACTORS = {
    "hemp_composite": 0.5,
    "pla_starch": 1.2,
    "cellulose_nano": 0.8,
    "magnesium_alloy": 2.0,
    "conventional_plastic": 3.5,
    "aluminum": 8.2,
    "steel": 1.85,
}

CONVENTIONAL_ALTERNATIVE = {
    "hemp_composite": "conventional_plastic",
    "pla_starch": "conventional_plastic",
    "cellulose_nano": "aluminum",
    "magnesium_alloy": "steel",
}


def get_material_type(material_id: int, type_from_odoo: Optional[str] = None) -> str:
    """Obtiene el tipo de material (desde Odoo o por defecto)."""
    if type_from_odoo and type_from_odoo in EMISSION_FACTORS:
        return type_from_odoo
    return "hemp_composite"


def calculate_carbon_footprint(material_type: str, kg_produced: float) -> float:
    """Huella de carbono del material producido (kg CO₂e)."""
    co2_per_kg = EMISSION_FACTORS.get(material_type, 1.0)
    return kg_produced * co2_per_kg


def calculate_carbon_savings(material_type: str, kg_produced: float) -> float:
    """Ahorro de CO₂ vs material convencional equivalente (kg CO₂e)."""
    conv = CONVENTIONAL_ALTERNATIVE.get(material_type, "conventional_plastic")
    conventional_co2 = EMISSION_FACTORS.get(conv, 3.5)
    eco_co2 = EMISSION_FACTORS.get(material_type, 1.0)
    return kg_produced * (conventional_co2 - eco_co2)


def register_carbon_credits_stub(
    kg_produced: float,
    material_id: int,
    savings_kg_co2: float,
    date: Optional[str] = None,
) -> str:
    """Stub: registra créditos en blockchain; devuelve tx_hash simulado."""
    from hashlib import sha256
    data = f"carbon-{material_id}-{kg_produced}-{savings_kg_co2}-{date or datetime.now().isoformat()}"
    return sha256(data.encode()).hexdigest()[:32]
