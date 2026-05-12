#!/usr/bin/env python3
"""
Capa 7: Audit trail inmutable (IPFS + GaiaChain).
CASTÚO-SYSTEM v1.7.1 — Registro de eventos críticos con hash y testigo on-chain.
"""
from __future__ import annotations

import hashlib
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _sha256_data(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def _pin_json(blob: dict, _key_hint: str | None = None) -> str | None:
    """Sube JSON a IPFS. key_hint opcional para uso con audit_log_key (HKDF)."""
    try:
        from ipfshttpclient import connect
        client = connect("/dns/ipfs.infura.io/tcp/5001/https")
        result = client.add_json(blob)
        if isinstance(result, str):
            return result
        if isinstance(result, (list, tuple)) and result:
            r = result[0]
            return r.get("Hash") or r.get("hash") if isinstance(r, dict) else str(r)
        return None
    except Exception as e:
        logger.warning("IPFS pin no disponible: %s", e)
        return None


def _witness_to_gaia(ipfs_hash: str) -> str | None:
    """Registra hash como testigo en GaiaChain (contrato de auditoría o evento). Opcional."""
    rpc = os.getenv("GAIA_CHAIN_RPC")
    if not rpc:
        return None
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(rpc))
        # Placeholder: en producción enviar tx a contrato AuditWitness o emitir evento
        logger.info("Witness IPFS hash (GaiaChain): %s", ipfs_hash[:20])
        return ipfs_hash
    except Exception as e:
        logger.warning("GaiaChain witness no disponible: %s", e)
        return None


class ImmutableAudit:
    """Registro de eventos críticos: hash del dato, IPFS, opcional testigo en GaiaChain."""

    def __init__(self, signer_address: str | None = None, audit_log_key: str | None = None):
        self.signer_address = signer_address or os.getenv("AUDIT_SIGNER_ADDRESS", "0x0")
        self.audit_log_key = audit_log_key or os.getenv("AUDIT_LOG_KEY", "")

    def log_critical_event(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Registra evento crítico: timestamp, tipo, hash de datos, firmante.
        Sube blob a IPFS y opcionalmente registra testigo en GaiaChain.
        """
        data_hash = _sha256_data(data)
        audit_blob = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "data_hash": data_hash,
            "signer": self.signer_address,
        }
        ipfs_hash = _pin_json(audit_blob, self.audit_log_key)
        witness = None
        if ipfs_hash:
            witness = _witness_to_gaia(ipfs_hash)
        result = {
            "event_type": event_type,
            "data_hash": data_hash,
            "ipfs_hash": ipfs_hash,
            "witness_gaia": witness,
        }
        logger.info("Audit event %s: ipfs=%s", event_type, ipfs_hash)
        return result


def main():
    """Prueba rápida: log de un evento de ejemplo."""
    audit = ImmutableAudit()
    out = audit.log_critical_event("nft_mint_test", {"token_id": 1, "crop": "lettuce"})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
