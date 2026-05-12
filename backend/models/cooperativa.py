# -*- coding: utf-8 -*-
"""Modelos Cooperativa y Parcela — CAPA 3 Core Business (agrovoltaica, PAC 2040)."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class Parcela(BaseModel):
    """Parcela agrovoltaica (cultivo + paneles)."""

    id: int
    hectares: float = Field(..., ge=0, description="Hectáreas")
    cultivo: str = Field(..., description="tomate, vid, olivo, etc.")
    kw_paneles: float = Field(..., ge=0, description="kWp instalados")
    pac2040_eligible: bool = Field(False, description="Elegible subvención PAC 2040")


class Cooperativa(BaseModel):
    """Cooperativa agrovoltaica (SAT Extremadura, socios, parcelas)."""

    id: int
    nombre: str
    nif: str
    parcelas: List[Parcela] = Field(default_factory=list)
    socios: int = Field(..., ge=1)
    capital_social: float = Field(30000.0, ge=0, description="€30K mínimo SAT Extremadura")

    @property
    def roi_anual(self) -> float:
        """Estimación ingresos anuales: energía (€45k/MWp) + cultivo (€12k/ha) + PAC 2040 (€25k/parcela elegible)."""
        energia = sum(p.kw_paneles * 45 for p in self.parcelas)  # €45k/MWp = 45 €/kWp
        cultivo = sum(p.hectares * 12000 for p in self.parcelas)  # €12k/ha
        pac = sum(25000 for p in self.parcelas if p.pac2040_eligible)
        return energia + cultivo + pac

    @property
    def pac2040_eligible(self) -> bool:
        """Al menos una parcela elegible PAC 2040."""
        return any(p.pac2040_eligible for p in self.parcelas)
