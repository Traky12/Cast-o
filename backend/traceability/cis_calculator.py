"""Créditos de Impacto Social (CIS) — Nodo Edge → tokens auditables (ZKP-ready en capa posterior)."""

from __future__ import annotations

from pydantic import BaseModel, Field

CIS_WATER_LITERS_PER_UNIT = 100.0
CIS_KG_CO2_PER_UNIT = 1.0


def calculate_cis_impact(water_saved_liters: float, carbon_avoided_kg: float) -> int:
    """
    1 CIS ≡ 100 L agua ahorrada O 1 kg CO2 evitado (suma lineal entera).
    Métricas pueden provenir de manifiestos firmados HSM (Zero-Water / PUE).
    """
    if water_saved_liters < 0 or carbon_avoided_kg < 0:
        raise ValueError("métricas CIS no negativas")
    impact_score = (water_saved_liters / CIS_WATER_LITERS_PER_UNIT) + (
        carbon_avoided_kg / CIS_KG_CO2_PER_UNIT
    )
    return int(impact_score)


class CISImpactRequest(BaseModel):
    water_saved_liters: float = Field(..., ge=0)
    carbon_avoided_kg: float = Field(..., ge=0)
    edge_node_id: str | None = Field(None, description="Nodo CASTUO Edge origen manifiesto")


class CISImpactResponse(BaseModel):
    cis_credits: int
    water_saved_liters: float
    carbon_avoided_kg: float
    formula: str = Field(
        default=f"floor(L/{CIS_WATER_LITERS_PER_UNIT:g} + CO2/{CIS_KG_CO2_PER_UNIT:g})",
    )


class ImpactCalculator:
    """Servicio explícito para tests y orquestación."""

    @staticmethod
    def compute(water_saved_liters: float, carbon_avoided_kg: float) -> int:
        return calculate_cis_impact(water_saved_liters, carbon_avoided_kg)

    @staticmethod
    def compute_detailed(req: CISImpactRequest) -> CISImpactResponse:
        n = calculate_cis_impact(req.water_saved_liters, req.carbon_avoided_kg)
        return CISImpactResponse(
            cis_credits=n,
            water_saved_liters=req.water_saved_liters,
            carbon_avoided_kg=req.carbon_avoided_kg,
        )
