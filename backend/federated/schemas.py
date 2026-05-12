from __future__ import annotations

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field


class FederatedUpdate(BaseModel):
    node_id: str
    model_params: List[float] = Field(default_factory=list)
    zk_proof: str = ""
    compliant: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    consent_accepted: bool = True

    model_config = ConfigDict(extra="allow")


class AnalysisRequest(BaseModel):
    finca_id: str = Field(
        ...,
        description="UUID inmutable de la explotación agraria registrada.",
        examples=["EXT-001-8f3a4d90-7c12-4a3d-b7b7-9a0c2f4e6f11"],
    )
    solar_exposure: float = Field(
        ...,
        description="Radiación solar global horizontal (GHI) en kWh/m².",
        ge=0,
        examples=[2450.0],
    )
    consent_accepted: bool = Field(
        ...,
        description="Flag de cumplimiento legal: el agricultor autoriza el tratamiento federado de sus datos.",
        examples=[True],
    )

    model_config = ConfigDict(extra="allow")


class AnalysisResponse(BaseModel):
    status: Literal["processing"] = Field(
        default="processing",
        description="Estado administrativo del proceso de certificación técnica.",
        examples=["processing"],
    )
    message: str = Field(
        default="Certificación UNE 216701 en proceso de validación técnica por CTAEX/Castúo",
        description="Mensaje oficial para el solicitante: la validación técnica UNE 216701 está en curso.",
        examples=[
            "Certificación UNE 216701 en proceso de validación técnica por CTAEX/Castúo"
        ],
    )
    audit_id: str = Field(
        ...,
        description="Identificador único de auditoría cifrada para trazabilidad legal.",
        examples=["AUD-a1b2c3d4e5f6g7h"],
    )
    estimated_completion: str = Field(
        default="TBD (Pendiente de validación de fórmulas oficiales)",
        description="Estimación de finalización del proceso (tbd hasta validación oficial UNE 216701).",
        examples=["TBD (Pendiente de validación de fórmulas oficiales)"],
    )

