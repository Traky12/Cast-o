"""Puente middleware PTM: hardware Aetheris ↔ asiento EnergyCredit / Fabric."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/aetheris", tags=["Aetheris PTM"])


class PTMSession(BaseModel):
    source_node_id: str
    target_node_id: str
    energy_kwh: float = Field(..., gt=0)
    laser_frequency_thz: float | None = Field(None, description="Referencia óptica; validación normativa aparte")
    timestamp: datetime | None = None


def _mock_tx() -> str:
    return "0x" + hashlib.sha256(secrets.token_bytes(32)).hexdigest()


@router.post("/ptm/session")
async def register_ptm_session(session: PTMSession):
    """
    1. Proximidad / alineación (gemelo digital, off-chain).
    2. Hyperledger Fabric o EnergyCredit.sol: openSession + PoT.
    3. Evento EnergyCreditSettled.
    """
    eff = round(session.energy_kwh * 0.85, 4)
    return {
        "status": "confirmed",
        "tx_hash": _mock_tx(),
        "credits_transferred_kwh_equiv": eff,
        "message": f"PTM {session.source_node_id} → {session.target_node_id} (mock; conectar nodo y contrato)",
        "timestamp": (session.timestamp or datetime.now(timezone.utc)).isoformat(),
    }
