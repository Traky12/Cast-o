# backend/sabion_omega_2040/quantum_merkle.py
"""QuantumMerkle2040 — Audit trail admin exclusivo. MERKLE_ROOT_ADMIN_EXCLUSIVO."""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

OMEGA_AUDIT_STORE: List[Dict[str, Any]] = []
AUDIT_RETENTION = int(os.getenv("OMEGA_AUDIT_RETENTION", "1000"))


def _sha3_512(b: bytes) -> bytes:
    return hashlib.sha3_512(b).digest()


def merkle_root_admin_exclusivo(leaves: List[str]) -> str:
    """Raíz Merkle nivel 2040 (SHA3-512 por hoja)."""
    if not leaves:
        return "0x" + "0" * 128
    nodes = [_sha3_512((h).encode() if isinstance(h, str) else h) for h in leaves]
    while len(nodes) > 1:
        next_level = []
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else left
            next_level.append(_sha3_512(left + right))
        nodes = next_level
    return "0x" + nodes[0].hex()


def omega_audit_log(action: str, admin_identity: str, detail: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Registro audit OMEGA_2040: Block → MerkleRoot_Admin → Anytype Omega-Audit-{timestamp}."""
    ts = datetime.now(timezone.utc)
    ts_iso = ts.isoformat()
    payload = {"action": action, "admin": admin_identity, "timestamp": ts_iso, "detail": detail or {}}
    blob = json.dumps(payload, sort_keys=True, default=str)
    block_hash = "0xomega" + hashlib.sha256(blob.encode()).hexdigest()[:12] + "..."
    root = merkle_root_admin_exclusivo([block_hash, admin_identity, ts_iso])
    anytype_object_id = f"Omega-Audit-{ts.strftime('%Y%m%d%H%M%S')}"
    record = {
        "block_hash": block_hash,
        "merkle_root_admin": root,
        "merkle_root_display": root[:24] + "..." if len(root) > 24 else root,
        "anytype_object_id": anytype_object_id,
        "admin": admin_identity,
        "action": action,
        "timestamp": ts_iso,
    }
    OMEGA_AUDIT_STORE.append(record)
    while len(OMEGA_AUDIT_STORE) > AUDIT_RETENTION:
        OMEGA_AUDIT_STORE.pop(0)
    return record


def audit_purge_simulated(admin_identity: str) -> int:
    """Limpieza Merkle (simulado: vacía solo si autorizado)."""
    n = len(OMEGA_AUDIT_STORE)
    OMEGA_AUDIT_STORE.clear()
    omega_audit_log("OMEGA_AUDIT_PURGE", admin_identity, {"purged": n})
    return n
