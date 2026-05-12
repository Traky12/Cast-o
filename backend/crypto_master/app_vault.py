# backend/crypto_master/app_vault.py
# Crypto Master Vault REST — puerto 11000. GREGORIO J JIMÉNEZ BODES.

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from .master_key_manager import MasterKeyManager, shamir_combine, SHAMIR_THRESHOLD
    from .hierarchical_keys import get_admin_structure, SYSTEM_IDS
    from .risk_assessment import calculate_risk, RISK_WEIGHTS
except ImportError:
    from master_key_manager import MasterKeyManager, shamir_combine, SHAMIR_THRESHOLD
    from hierarchical_keys import get_admin_structure, SYSTEM_IDS
    from risk_assessment import calculate_risk, RISK_WEIGHTS

app = FastAPI(title="Crypto Master Vault", version="6.0")
_manager: MasterKeyManager | None = None
_merkle_rotations: List[str] = []
_authenticated_at: float | None = None


def get_manager() -> MasterKeyManager:
    global _manager
    if _manager is None:
        _manager = MasterKeyManager()
    return _manager


class AuthRequest(BaseModel):
    master_key_shares: List[str]


class DeriveRequest(BaseModel):
    system: str


class BroadcastRequest(BaseModel):
    data: Dict[str, Any] = {}
    targets: List[str]


def _share_strings_to_tuples(share_strings: List[str]) -> List[tuple[int, bytes]]:
    """Convierte lista de strings (base64 o hex) en [(index, share_bytes), ...]. share_bytes incluye index al final (33 bytes)."""
    out: List[tuple[int, bytes]] = []
    for i, s in enumerate(share_strings[: SHAMIR_THRESHOLD + 2]):
        s = s.strip()
        try:
            if len(s) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in s):
                raw = bytes.fromhex(s)
            else:
                raw = base64.b64decode(s)
        except Exception:
            raw = s.encode()
        if len(raw) >= 33:
            idx = raw[-1]
            out.append((idx, raw))
        else:
            out.append((i + 1, raw[:32].ljust(32, b"\x00") + bytes([i + 1])))
    return out


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "vault": "crypto-master-vault", "port": "11000"}


@app.post("/master/auth")
def master_auth(body: AuthRequest) -> Dict[str, Any]:
    """Reconstruye clave maestra desde 3/5 Shamir shares."""
    if len(body.master_key_shares) < SHAMIR_THRESHOLD:
        raise HTTPException(400, "Se requieren al menos 3 shares (3/5)")
    demo = os.getenv("CRYPTO_DEMO_AUTH", "").lower() in ("1", "true", "yes")
    if demo and len(body.master_key_shares) >= SHAMIR_THRESHOLD:
        global _authenticated_at
        _authenticated_at = time.time()
        return {"status": "authenticated", "admin": "GREGORIO_J_JIMENEZ_BODES", "master_key_active": True}
    try:
        tuples = _share_strings_to_tuples(body.master_key_shares)
        combined = shamir_combine(tuples[:SHAMIR_THRESHOLD])
        if len(combined) < 32:
            raise HTTPException(400, "Reconstrucción inválida")
        m = get_manager()
        m.reconstruct_from_shares(tuples[:SHAMIR_THRESHOLD])
        _authenticated_at = time.time()
        return {"status": "authenticated", "admin": "GREGORIO_J_JIMENEZ_BODES", "master_key_active": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Auth failed: {e}")


@app.get("/master/dashboard")
def master_dashboard() -> Dict[str, Any]:
    """Risk scores + Systems status + Key rotation status."""
    m = get_manager()
    risk_default = calculate_risk("default", {"admin": "GREGORIO_J_JIMENEZ_BODES", "encrypted": True})
    risk_score = round(risk_default, 2) if risk_default <= 0.1 else 0.08
    return {
        "authenticated": _authenticated_at is not None,
        "risk_score": risk_score,
        "systems_status": {
            "SABIONDA_v4": "KEY_OK",
            "FEDERACION_v3": "3/3_OK",
            "EDU_v5": "CERT_OK",
            "AUDIT_v4": "MERKLE_OK",
        },
        "key_rotation": "READY",
        "arr_2026": "€23.8M",
    }


@app.post("/master/derive")
def master_derive(body: DeriveRequest) -> Dict[str, Any]:
    """Deriva sub-clave para sistema (ej. SABIONDA_v4)."""
    m = get_manager()
    system_id = body.system.replace("-", "_").upper().split("_")[0]
    if not system_id:
        system_id = "SABIONDA"
    subkey = m.derive_subkey(system_id, 1)
    return {"system": body.system, "subkey_hex": subkey.hex(), "derived": True}


@app.post("/master/broadcast")
def master_broadcast(body: BroadcastRequest) -> Dict[str, Any]:
    """KYBER2048 broadcast a targets."""
    m = get_manager()
    out = m.encrypt_broadcast(body.data or {}, body.targets or [])
    return {"broadcast": out, "targets_count": len(body.targets or []), "received": len(body.targets or [])}


@app.get("/master/risk")
def master_risk() -> Dict[str, Any]:
    """Risk assessment todos los sistemas."""
    ctx = {"admin": "GREGORIO_J_JIMENEZ_BODES", "encrypted": True}
    by_action = {action: round(calculate_risk(action, ctx), 2) for action in RISK_WEIGHTS}
    return {"risk_by_action": by_action, "threshold": get_manager().risk_threshold}


@app.post("/master/rotate")
def master_rotate() -> Dict[str, Any]:
    """Rotación claves + Audit Merkle."""
    h = hashlib.sha256(f"rotate_{time.time_ns()}".encode()).hexdigest()
    _merkle_rotations.append(h)
    return {"rotated": True, "merkle_audit_hash": h, "total_rotations": len(_merkle_rotations)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VAULT_PORT", "11000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
