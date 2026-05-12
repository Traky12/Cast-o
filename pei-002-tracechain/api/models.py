"""Modelos Pydantic v2 para stub PEI-002 (laboratorio). No sustituyen al backend Castuo."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class EnvelopeMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    mapping_path: Optional[str] = None
    usos_problematicos: Dict[str, Dict[str, list]] = Field(default_factory=dict)
    summary: Dict[str, Any] = Field(default_factory=dict)


class SigpacValidationEnvelope(BaseModel):
    """Envelope sin geometrias (minimizacion RGPD frente a enviar Feature completos)."""

    event_type: str = "sigpac_validation"
    digest: str
    timestamp: int
    parcelas: int
    cumplen: int
    metadata: EnvelopeMetadata = Field(default_factory=EnvelopeMetadata)


class ParcelAuditPayload(BaseModel):
    """
    Registro por parcela sin geometry: el cliente debe enviar solo identificadores y usos.
    Cualquier geometria en el cuerpo se ignora (no se persiste en este stub).
    """

    model_config = ConfigDict(extra="ignore")

    event_type: str = "parcela_validation"
    parcela_id: str
    digest: str
    timestamp: int
    uso_declarado: Optional[str] = None
    uso_sigpac: Optional[str] = None
    codigo_sigpac: Optional[str] = None
    cumple: bool
    cumple_via: str = "no"
    metadata: Dict[str, Any] = Field(default_factory=dict)
