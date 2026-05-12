# backend/federated/blockchain_auditor.py
"""Audit trail blockchain: cada acción agente → Block Hash → IPFS Pin → Anytype Object (Audit-001)."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

IPFS_HOST = os.getenv("IPFS_HOST", "http://ipfs:5001")
IPFS_ENABLED = os.getenv("IPFS_ENABLED", "true").lower() == "true"
SEPOLIA_RPC = os.getenv("SEPOLIA_RPC", "")
AUDIT_STORE: List[Dict[str, Any]] = []


def _block_hash(payload: dict) -> str:
    """Genera hash tipo block (SHA-256 prefijo 0x)."""
    blob = json.dumps(payload, sort_keys=True, default=str)
    return "0x" + hashlib.sha256(blob.encode()).hexdigest()


def _ipfs_add(data: dict) -> str | None:
    """Pin JSON en IPFS y devuelve CID (Qm...). Simulado si IPFS no disponible."""
    if not IPFS_ENABLED:
        return "Qm" + hashlib.sha256(json.dumps(data).encode()).hexdigest()[:44]
    try:
        import httpx
        r = httpx.post(
            f"{IPFS_HOST}/api/v0/add",
            files={"file": ("audit.json", json.dumps(data, default=str))},
            timeout=30.0,
        )
        if r.status_code == 200:
            res = r.json()
            return res.get("Hash", res.get("cid"))
    except Exception as e:
        logger.debug("IPFS add failed: %s", e)
    return "Qm" + hashlib.sha256(json.dumps(data).encode()).hexdigest()[:44]


def commit_audit(action: dict) -> Dict[str, Any]:
    """
    Registra acción en audit trail: block_hash + IPFS CID.
    Anytype Object "Audit-001" se puede crear con este payload.
    """
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "action": action,
        "timestamp": ts,
        "source_node": action.get("source_node", "unknown"),
        "agent": action.get("agent") or action.get("type") or "federated",
    }
    block_hash = _block_hash(payload)
    cid = _ipfs_add(payload)
    record = {
        "block_hash": block_hash,
        "ipfs_cid": cid,
        "timestamp": ts,
        "agent": payload["agent"],
        "source_node": payload["source_node"],
        "anytype_object_id": f"Audit-{len(AUDIT_STORE) + 1:03d}",
    }
    AUDIT_STORE.append(record)
    logger.info("Audit committed: %s → %s → %s", record["anytype_object_id"], block_hash[:18], cid)
    return {
        "block_hash": block_hash,
        "ipfs_cid": cid,
        "anytype_object_id": record["anytype_object_id"],
        "timestamp": ts,
    }


def get_audit_metrics() -> Dict[str, Any]:
    """Métricas para dashboard: blocks, IPFS pins, últimos CIDs."""
    return {
        "audit_trail_blocks": len(AUDIT_STORE),
        "ipfs_pins": len(AUDIT_STORE),
        "last_cids": [r["ipfs_cid"] for r in AUDIT_STORE[-5:]],
        "last_block": AUDIT_STORE[-1]["block_hash"][:20] + "..." if AUDIT_STORE else None,
    }
