# -*- coding: utf-8 -*-
"""Modelos Sabionda (decisiones, bandejas)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, constr

TrayId = constr(pattern=r"^B0[0-4][0-9]$")  # B001-B048


class SabiondaRequest(BaseModel):
    """Payload desde sensores / n8n / IoT al endpoint de decisión."""

    bandeja: TrayId = Field(..., description="Identificador de bandeja, p.ej. B001")
    crop: str = Field(
        ...,
        description=(
            "Cultivo en la bandeja, p.ej. 'guisantes', 'rabanos', 'lentejas', "
            "'mostaza', 'brocoli', 'kale', etc."
        ),
    )
    system: str = Field(
        ...,
        description=(
            "Sistema registrado, p.ej. 'hidroponia_rpi4', "
            "'hidroponia_v1', 'agrovolt_b5'"
        ),
    )
    ph: float = Field(..., description="pH medido en la bandeja")
    ec: float = Field(..., description="Conductividad eléctrica (mS/cm)")
    temp: Optional[float] = Field(
        None, description="Temperatura del aire/líquido asociada a la bandeja (°C)"
    )
    humidity: Optional[float] = Field(
        None, description="Humedad relativa asociada al cultivo (%)"
    )


class SabiondaDecision(BaseModel):
    """Forma exacta de la respuesta esperada por Castuo TRL8."""

    decision: str = Field(..., description="Ejemplo: 'V01 ON' o 'V01 OFF'")
    uv_status: bool = Field(..., description="Si el sistema UV está activo")
    o3_target: float = Field(..., description="Setpoint objetivo para O3")
    log_message: str = Field(
        ...,
        description="Mensaje humano-legible, p.ej. 'B001 ph=6.9 → V01 ON → SHA256 log'",
    )
    version: str = Field("2.0", description="Versión del contrato de respuesta")
    sha256: str = Field(..., description="Hash del payload original para auditoría")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recomendaciones agronómicas específicas para el operador",
    )
