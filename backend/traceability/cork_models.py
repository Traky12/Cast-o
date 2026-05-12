"""Trazabilidad Segureja / corcho premium: gemelo digital ↔ láser ↔ GaiaChain (PQC-ready)."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

_SHA3_512_HEX = re.compile(r"^(0x)?[a-fA-F0-9]{128}$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CorkExtractionEventCreate(BaseModel):
    """Cuerpo POST: validación antes de persistir y ancla ledger."""

    tree_uuid: UUID = Field(..., description="Alcornoque — gemelo digital")
    operator_id: str = Field(..., min_length=1, max_length=256, description="Supervisor / dron con trazabilidad eIDAS")
    laser_energy_mj: float = Field(..., gt=0, description="Energía media ablación (mJ por pulso o sesión según política)")
    cambium_integrity_score: float = Field(
        ...,
        gt=0.99,
        le=1.0,
        description="Score NIR / validación cambium (Segureja <1% daño)",
    )
    pqc_signature: str = Field(
        ...,
        min_length=16,
        description="Firma post-cuántica cabezal / módulo (ML-DSA / Dilithium hex o contenedor)",
    )
    gaia_chain_hash: str = Field(
        ...,
        alias="gaichain_hash",
        description="SHA-3-512 anclado al ledger GaiaChain",
    )

    model_config = {"populate_by_name": True}

    @field_validator("gaia_chain_hash")
    @classmethod
    def gaia_hash_format(cls, v: str) -> str:
        s = v.strip()
        if not _SHA3_512_HEX.match(s):
            raise ValueError("gaia_chain_hash debe ser 64 bytes hex (128 hex chars), opcional 0x")
        return s.lower() if not s.startswith("0x") else "0x" + s[2:].lower()


class CorkExtractionEvent(CorkExtractionEventCreate):
    """Incluye sellado temporal auditables."""

    timestamp: datetime = Field(default_factory=_utcnow)


class CorkExtractionEventStored(CorkExtractionEvent):
    event_id: UUID = Field(default_factory=uuid.uuid4)
    received_at: datetime = Field(default_factory=_utcnow)
