# backend/api/services/gaiachain.py
"""Wrapper de integración con GaiaChain para registro de eventos (auditoría EU/OSS)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _build_event_data(
    token_id: int,
    action_type: str,
    status: str,
    ipfs_cid: str,
    norms: Any,
    legal_basis: Any,
) -> Dict[str, Any]:
    return {
        "tokenId": token_id,
        "action": action_type,
        "status": status,
        "details": {"ipfs_cid": ipfs_cid, "norms": norms},
        "compliance": legal_basis if isinstance(legal_basis, dict) else {},
    }


class GaiaChainService:
    """Expone registro de eventos hacia el contrato de auditoría GaiaChain."""

    async def register_event(
        self,
        token_id: int,
        action_type: str,
        status: str,
        ipfs_cid: str,
        norms: Any,
        legal_basis: Any,
    ) -> str:
        """Registra un evento en GaiaChain. Devuelve tx hash o fallback si no está configurado."""
        return self.register_event_sync(
            token_id, action_type, status, ipfs_cid, norms, legal_basis
        )

    def register_event_sync(
        self,
        token_id: int,
        action_type: str,
        status: str,
        ipfs_cid: str,
        norms: Any,
        legal_basis: Any,
    ) -> str:
        """Versión síncrona para uso desde scripts y servicios de rotación."""
        try:
            from .gaiachain_service import register_event_in_chain

            event_data = _build_event_data(
                token_id, action_type, status, ipfs_cid, norms, legal_basis
            )
            return register_event_in_chain(event_data)
        except Exception:
            return "fallback-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    def ping(self) -> bool:
        """Comprueba conectividad con GaiaChain (RPC o contrato)."""
        try:
            from . import gaiachain_service

            _ = gaiachain_service.w3.eth.block_number
            return True
        except Exception:
            return False
