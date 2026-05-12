# -*- coding: utf-8 -*-
"""
Modelos Hidroponía — Sabionda Omega 2040.
El pH es el aliento de la solución nutritiva; la EC, la riqueza de sales que nutre el sistema.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, Tuple

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class HidroponiaSensor(BaseModel):
    """
    Lectura de sensores: pulso de la biosfera del tanque.
    Potencial de Hidrógeno (pH), conductividad (EC), oxígeno disuelto, temperatura.
    """

    ph: float = Field(
        ...,
        ge=0,
        le=14,
        description="Potencial de Hidrógeno — aliento de la acidez del agua en la Raya",
    )
    ec: float = Field(
        ...,
        ge=0,
        le=10,
        description="Conductividad Eléctrica (mS/cm) — riqueza de sales que nutre el sistema",
    )
    do: float = Field(..., ge=0, le=20, description="Oxígeno Disuelto (mg/L)")
    temp: float = Field(..., ge=0, le=50, description="Temperatura del agua (°C)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("ph")
    @classmethod
    def validar_ph_omega(cls, v: float) -> float:
        """Sabionda Omega detecta estrés inminente en la solución nutritiva."""
        if not (5.5 <= v <= 6.5):
            logger.warning("⚠️ Alerta Biótica: pH fuera de rango óptimo (%s)", v)
        return v


class HidroponiaSistema(BaseModel):
    """Sistema hidropónico (NFT, DWC, EbbFlow, Aeroponia) bajo paneles agrovoltaicos."""

    id: str
    tipo: Literal["NFT", "DWC", "EbbFlow", "Aeroponia"]
    canales: int = Field(..., ge=1)
    volumen_tanque: float = Field(..., ge=0, description="Litros")
    plantas_por_canal: int = Field(..., ge=0)


class CultivoHidroponico(BaseModel):
    """Cultivo hidropónico asociado a un sistema — soberanía alimentaria por m²."""

    id: str
    nombre: str = Field(..., description="lechuga, albahaca, microgreens")
    sistema: HidroponiaSistema
    plantas_totales: int = Field(..., ge=0)
    ec_objetivo: Tuple[float, float] = Field(..., description="mS/cm min, max")
    ph_objetivo: Tuple[float, float] = Field(..., description="pH min, max")
    densidad: float = Field(..., ge=0, description="Plantas por m²")
