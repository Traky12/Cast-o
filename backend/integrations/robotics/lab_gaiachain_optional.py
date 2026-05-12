"""
Registro GaiaChain **opt-in** desde el robotics lab stub.
Requiere contrato + ABI + clave reales; si falta algo, no rompe el stub (tx_id null).

No sustituye revisión legal: minimizar `details` y usar tokenId acordado con DPIA.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def robotics_lab_chain_register_enabled() -> bool:
    if os.getenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", "").strip() != "1":
        return False
    try:
        from backend.api.config import settings
    except Exception as exc:
        logger.debug("config no disponible para cadena: %s", exc)
        return False
    pk = (settings.GAIA_CHAIN_PRIVATE_KEY or "").strip()
    if not pk or pk in ("0x0", "0", "0x00"):
        return False
    addr = (settings.GAIA_CHAIN_AUDIT_CONTRACT or "").strip().lower()
    if not addr or addr == "0x0000000000000000000000000000000000000000":
        return False
    abi = (settings.GAIA_CHAIN_AUDIT_ABI or "").strip()
    if not abi or abi == "[]":
        return False
    return True


def robotics_lab_chain_status() -> str:
    """Para /health: sin credenciales; indica si el operador pidió cadena y si la config es coherente."""
    if os.getenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", "").strip() != "1":
        return "disabled"
    if robotics_lab_chain_register_enabled():
        return "ready"
    return "misconfigured"


def _include_parcel_in_chain_details() -> bool:
    return os.getenv("CASTUO_ROBOTICS_LAB_CHAIN_INCLUDE_PARCEL_ID", "").strip() == "1"


def build_snapshot_audit_payload(
    *,
    token_id: int,
    action: str,
    status: str,
    digest_with_prefix: str,
    parcel_id: str,
    neuromorphic: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    details: Dict[str, Any] = {
        "digest": digest_with_prefix,
    }
    if _include_parcel_in_chain_details():
        details["parcel_ref"] = parcel_id
    if neuromorphic:
        inf = neuromorphic.get("inference") or {}
        if "riego_ml" in inf:
            details["riego_ml"] = inf["riego_ml"]
        eco = inf.get("eco_alloy")
        if eco:
            details["eco_alloy"] = eco
        details["neuro_chain_seal"] = neuromorphic.get("chain_seal")
    return {
        "tokenId": int(token_id),
        "action": action,
        "status": status,
        "details": details,
        "compliance": {
            "module": "robotics_lab_snapshot",
            "minimization": "parcel_ref_opt_in",
        },
    }


def try_register_lab_audit_event(payload: Dict[str, Any]) -> Optional[str]:
    if not robotics_lab_chain_register_enabled():
        return None
    try:
        from backend.api.services.gaiachain_service import register_event_in_chain

        return register_event_in_chain(payload)
    except Exception as exc:
        logger.exception("robotics lab: registro cadena fallido: %s", exc)
        return None


def resolve_snapshot_token_id(explicit: Optional[int]) -> int:
    if explicit is not None and explicit > 0:
        return int(explicit)
    raw = os.getenv("CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID", "0").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def build_scan3d_print_audit_payload(
    *,
    token_id: int,
    scan_id: str,
    chain_seal_dilithium: str,
    volume_cm3: float,
    material: str,
) -> Dict[str, Any]:
    details: Dict[str, Any] = {
        "scan_ref": scan_id[:128],
        "volume_cm3": volume_cm3,
        "material": material,
        "dilithium_seal": chain_seal_dilithium,
    }
    return {
        "tokenId": int(token_id),
        "action": "SCAN3D_PRINT_JOB",
        "status": "GCODE_READY",
        "details": details,
        "compliance": {"module": "robotics_lab_scan3d", "minimization": "no_mesh_blob"},
    }
