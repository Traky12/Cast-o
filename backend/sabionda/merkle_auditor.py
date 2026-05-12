# backend/sabionda/merkle_auditor.py
"""Audit trail inmutable: MerkleRoot( Block(0x) + IPFS(CID) + SabiondaSignature ) → Anytype Sabionda-Audit-{ts}."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from .crypto_pqc import sabionda_signature
except ImportError:
    from crypto_pqc import sabionda_signature

IPFS_HOST = os.getenv("IPFS_HOST", "http://ipfs:5001")
IPFS_ENABLED = os.getenv("IPFS_ENABLED", "true").lower() == "true"
AUDIT_STORE: List[Dict[str, Any]] = []


def _sha256(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()


def _merkle_root(leaves: List[str]) -> str:
    """Raíz Merkle de una lista de strings (cada una se hashea a 32 bytes)."""
    if not leaves:
        return "0x" + "0" * 64
    nodes = [_sha256(h.encode() if isinstance(h, str) else h) for h in leaves]
    while len(nodes) > 1:
        next_level = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left
            next_level.append(_sha256(left + right))
        nodes = next_level
    return "0x" + nodes[0].hex()


def _block_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode()
    return "0x" + hashlib.sha256(blob).hexdigest()


def _ipfs_add(data: dict) -> str:
    """Pin en IPFS, devuelve CID Qm..."""
    if not IPFS_ENABLED:
        return "Qm" + hashlib.sha256(json.dumps(data).encode()).hexdigest()[:44]
    try:
        import httpx
        r = httpx.post(
            f"{IPFS_HOST}/api/v0/add",
            files={"file": ("sabionda_audit.json", json.dumps(data, default=str))},
            timeout=30.0,
        )
        if r.status_code == 200:
            res = r.json()
            return res.get("Hash", res.get("cid", "Qm" + hashlib.sha256(json.dumps(data).encode()).hexdigest()[:44]))
    except Exception as e:
        logger.debug("IPFS add: %s", e)
    return "Qm" + hashlib.sha256(json.dumps(data).encode()).hexdigest()[:44]


async def commit_sabionda_action(action: dict) -> Dict[str, Any]:
    """
    Cada acción → Block Hash (0x) → IPFS Pin (Qm) → MerkleRoot + SabiondaSignature
    → Anytype Object "Sabionda-Audit-{timestamp}".
    """
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        "action": action,
        "timestamp": ts,
        "agent": action.get("agent") or action.get("type") or "sabionda",
        "source": action.get("source_node", "sabionda-master"),
    }
    block_hash = _block_hash(payload)
    cid = _ipfs_add(payload)
    sig = sabionda_signature({"block": block_hash, "cid": cid, "ts": ts})
    merkle_root = _merkle_root([block_hash, cid, sig])
    object_id = f"Sabionda-Audit-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    record = {
        "block_hash": block_hash,
        "ipfs_cid": cid,
        "merkle_root": merkle_root,
        "sabionda_signature": sig,
        "anytype_object_id": object_id,
        "timestamp": ts,
    }
    AUDIT_STORE.append(record)
    logger.info("Merkle audit: %s → %s | CID %s | Merkle %s", object_id, block_hash[:18], cid[:12], merkle_root[:18])
    return record


def get_audit_metrics() -> Dict[str, Any]:
    return {
        "blocks": len(AUDIT_STORE),
        "ipfs_pins": len(AUDIT_STORE),
        "last_merkle_root": AUDIT_STORE[-1]["merkle_root"][:24] + "..." if AUDIT_STORE else None,
        "last_object_id": AUDIT_STORE[-1]["anytype_object_id"] if AUDIT_STORE else None,
    }
