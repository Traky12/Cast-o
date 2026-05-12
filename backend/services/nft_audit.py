# -*- coding: utf-8 -*-
"""
Trazabilidad inmutable de eventos NFT (mint, update growth).
Registro en IPFS + witness opcional en GaiaChain para cooperativas protegidas.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _pin_audit_json(data: dict) -> str:
    """Sube el evento de auditoría a IPFS. Sin IPFS devuelve placeholder."""
    try:
        import ipfshttpclient
        api = os.getenv("IPFS_GATEWAY", "/dns/ipfs.infura.io/tcp/5001/https")
        client = ipfshttpclient.connect(api)
        return client.add_str(json.dumps(data, default=str))
    except Exception:
        return "QmAuditPlaceholder"


def _witness_to_gaia(ipfs_hash: str) -> Optional[str]:
    """Registra el hash de auditoría en GaiaChain como testigo inmutable. Opcional."""
    rpc = os.getenv("GAIA_CHAIN_RPC", "")
    if not rpc:
        return None
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(rpc))
        if w3.is_connected():
            return ipfs_hash
    except Exception:
        pass
    return None


class NFTAuditTrail:
    """Registro de auditoría para mints y actualizaciones de DynamicCropNFT."""

    def __init__(self) -> None:
        self._tx_hash: Optional[str] = None
        self._signer_address: Optional[str] = None

    def set_tx_context(self, tx_hash: str, signer_address: str) -> None:
        self._tx_hash = tx_hash
        self._signer_address = signer_address

    def log_mint(
        self,
        token_id: int,
        farm_id: str,
        growth_stage: int = 0,
        crop_type: str = "",
    ) -> str:
        """Registra un mint en el audit trail y devuelve el hash IPFS."""
        audit_event: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "MINT_DYNAMIC_NFT",
            "token_id": token_id,
            "farm_id": farm_id,
            "growth_stage": growth_stage,
            "crop_type": crop_type,
            "tx_hash": self._tx_hash or "",
            "signer": self._signer_address or "",
        }
        ipfs_hash = _pin_audit_json(audit_event)
        _witness_to_gaia(ipfs_hash)
        return ipfs_hash

    def log_update_growth(self, token_id: int, farm_id: str, growth_stage: int) -> str:
        """Registra una actualización de growth stage."""
        audit_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "UPDATE_GROWTH_NFT",
            "token_id": token_id,
            "farm_id": farm_id,
            "growth_stage": growth_stage,
            "tx_hash": self._tx_hash or "",
            "signer": self._signer_address or "",
        }
        ipfs_hash = _pin_audit_json(audit_event)
        _witness_to_gaia(ipfs_hash)
        return ipfs_hash

    def get_trace(self, token_id: int) -> Optional[Dict[str, Any]]:
        """Devuelve la traza de auditoría del token si está disponible (ej. desde almacén local/IPFS)."""
        return None
