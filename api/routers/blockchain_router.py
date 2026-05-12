"""
SABIONDA — Registro de eventos en GaiaChain (blockchain)

Endpoint:
  - POST /api/v1/blockchain/log → Registra un evento en GaiaChain
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security.rbac import encryption_key_from_env, require_roles

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/blockchain", tags=["blockchain"])


# ─── Modelos ──────────────────────────────────────────────────────────────────

class BlockchainLogRequest(BaseModel):
    event_type: str = Field(..., min_length=1, description="Tipo de evento (ej: code_update)")
    data: dict[str, Any] = Field(default_factory=dict, description="Datos asociados al evento")
    actor: str = Field(..., min_length=1, description="Identificador del actor que genera el evento")
    sensitive_fields: list[str] = Field(
        default_factory=list,
        description="Campos del objeto data a cifrar antes de registrar en blockchain",
    )


class BlockchainLogResponse(BaseModel):
    txid: str
    event_type: str
    actor: str
    timestamp: str


# ─── Endpoint ─────────────────────────────────────────────────────────────────

def _protect_sensitive_fields(data: dict[str, Any], sensitive_fields: list[str]) -> dict[str, Any]:
    if not sensitive_fields:
        return dict(data)

    cipher = Fernet(encryption_key_from_env())
    protected = dict(data)
    for field in sensitive_fields:
        if field in protected:
            serialized = str(protected[field]).encode("utf-8")
            token = cipher.encrypt(serialized).decode("utf-8")
            protected[field] = f"enc:v1:{token}"
    return protected


@router.post(
    "/log",
    response_model=BlockchainLogResponse,
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "ciso", "devops"))],
)
async def log_to_blockchain(request: BlockchainLogRequest) -> BlockchainLogResponse:
    """
    Registra un evento en GaiaChain para trazabilidad inmutable.

    Devuelve el txid de la transacción blockchain.
    Devuelve 503 si GaiaChain no está disponible.
    """
    try:
        from castuo_graph.blockchain.gaiachain import GaiachainConnector  # noqa: PLC0415

        connector = GaiachainConnector()
        timestamp = datetime.now(timezone.utc).isoformat()
        protected_data = _protect_sensitive_fields(request.data, request.sensitive_fields)

        payload: dict[str, Any] = {
            "event_type": request.event_type,
            "data": protected_data,
            "actor": request.actor,
            "timestamp": timestamp,
        }

        txid = connector.register_hash(payload)

        logger.info(
            "GaiaChain log: event=%s actor=%s txid=%s",
            request.event_type,
            request.actor,
            txid,
        )

        return BlockchainLogResponse(
            txid=txid,
            event_type=request.event_type,
            actor=request.actor,
            timestamp=timestamp,
        )

    except Exception as exc:
        logger.error("Error registrando en GaiaChain: %s", exc)
        raise HTTPException(status_code=503, detail=f"Error de blockchain: {exc}")
