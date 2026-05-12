"""
Stub HTTP para laboratorio: acepta un snapshot JSON (metadatos PEI-001 / intervención) y devuelve digest canónico.
GaiaChain: **solo** si CASTUO_ROBOTICS_LAB_CHAIN_REGISTER=1 y `gaiachain_service` tiene RPC/contrato/clave válidos
(`register_event_in_chain`); si no, tx_id permanece null (coherente con PEI-002 stub).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

app = FastAPI(title="Castuo Robotics Lab Stub", version="0.1.0")
_bearer = HTTPBearer(auto_error=False)


class SnapshotBody(BaseModel):
    model_config = ConfigDict(extra="ignore")

    parcel_id: str = Field(..., min_length=1)
    timestamp: str = Field(..., min_length=1)
    intervention_type: str = Field(..., min_length=1)
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)
    sigpac_compliant: bool = False
    pei001_digest: Optional[str] = None
    audit_event: Optional[str] = None
    token_id: Optional[int] = Field(
        default=None,
        ge=0,
        description="tokenId para register_event_in_chain; si null, usa CASTUO_ROBOTICS_LAB_CHAIN_TOKEN_ID.",
    )


class SnapshotResponse(BaseModel):
    status: str = "stub-registered"
    tx_id: Optional[str] = None
    gaia_chain_digest: str
    compliance: bool
    neuromorphic_inference: Optional[Dict[str, Any]] = None
    chain_registration: str = "none"
    chain_seal: Optional[str] = Field(
        default=None,
        description="Firma Dilithium del bloque neuromórfico (si CASTUO_NEUROMORPHIC_LAB=1 y hay sensores).",
    )


def _canonical_json(body: SnapshotBody) -> str:
    return json.dumps(body.model_dump(exclude_none=True), sort_keys=True, separators=(",", ":"))


def _digest_sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _lab_auth_optional() -> bool:
    return os.getenv("CASTUO_ROBOTICS_LAB", "").strip() == "1"


def _expected_token() -> Optional[str]:
    t = os.getenv("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "").strip()
    return t or None


async def _verify_lab_bearer(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    expected = _expected_token()
    if expected:
        if creds is None or creds.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Authorization: Bearer requerido")
        if creds.credentials != expected:
            raise HTTPException(status_code=401, detail="Token inválido")
        return
    if _lab_auth_optional():
        logger.warning(
            "CASTUO_ROBOTICS_LAB=1 sin CASTUO_ROBOTICS_LAB_BEARER_TOKEN: stub sin autenticación (solo laboratorio)."
        )
        return
    raise HTTPException(
        status_code=503,
        detail="Configura CASTUO_ROBOTICS_LAB_BEARER_TOKEN (o CASTUO_ROBOTICS_LAB=1 solo en dev).",
    )


@app.post("/api/robotics/lab/snapshot", response_model=SnapshotResponse)
async def robotics_lab_snapshot(body: SnapshotBody, _: None = Depends(_verify_lab_bearer)) -> SnapshotResponse:
    canonical = _canonical_json(body)
    digest_hex = _digest_sha256_hex(canonical)
    digest_pref = f"sha256:{digest_hex}"
    client = (body.pei001_digest or "").strip().lower().removeprefix("sha256:")
    if client and client != digest_hex.lower():
        logger.info(
            "pei001_digest del cliente no coincide con digest canónico del cuerpo POST "
            "(normal si el digest refiere a otro artefacto JSON)."
        )

    neuro: Optional[Dict[str, Any]] = None
    if os.getenv("CASTUO_NEUROMORPHIC_LAB", "").strip() == "1":
        from backend.integrations.robotics.neuromorphic_edge import neuromorphic_hint_from_metadata

        neuro = neuromorphic_hint_from_metadata(dict(body.metrics_summary))

    chain_registration = "none"
    tx_hash: Optional[str] = None
    from backend.integrations.robotics.lab_gaiachain_optional import (
        build_snapshot_audit_payload,
        resolve_snapshot_token_id,
        robotics_lab_chain_register_enabled,
        try_register_lab_audit_event,
    )

    tid = resolve_snapshot_token_id(body.token_id)
    if robotics_lab_chain_register_enabled() and tid > 0:
        action = (body.audit_event or "robotics_lab_snapshot").strip() or "robotics_lab_snapshot"
        payload = build_snapshot_audit_payload(
            token_id=tid,
            action=action,
            status="REGISTERED",
            digest_with_prefix=digest_pref,
            parcel_id=body.parcel_id,
            neuromorphic=neuro,
        )
        tx_hash = try_register_lab_audit_event(payload)
        if tx_hash:
            chain_registration = "registered"
        else:
            chain_registration = "failed"
    elif robotics_lab_chain_register_enabled() and tid <= 0:
        chain_registration = "missing_token"

    neuro_seal: Optional[str] = None
    if neuro and isinstance(neuro.get("chain_seal"), str):
        neuro_seal = neuro["chain_seal"]

    return SnapshotResponse(
        tx_id=tx_hash,
        gaia_chain_digest=digest_pref,
        compliance=bool(body.sigpac_compliant),
        neuromorphic_inference=neuro,
        chain_registration=chain_registration,
        chain_seal=neuro_seal,
    )


async def _verify_admin_general_bearer(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> None:
    from backend.auth_roles import read_secret

    expected = read_secret("CASTUO_ADMIN_GENERAL_BEARER").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="CASTUO_ADMIN_GENERAL_BEARER no configurado (o _FILE).",
        )
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization: Bearer requerido")
    if creds.credentials != expected:
        raise HTTPException(status_code=401, detail="Token administrador general inválido")


@app.get("/admin_general/playbook")
async def admin_general_playbook(_: None = Depends(_verify_admin_general_bearer)) -> Dict[str, Any]:
    from backend.models.system_admin_playbook import get_admin_general_playbook

    return get_admin_general_playbook()


@app.get("/health")
async def health() -> Dict[str, Any]:
    from backend.integrations.robotics.lab_gaiachain_optional import robotics_lab_chain_status

    return {
        "status": "ok",
        "service": "robotics-lab-stub",
        "chain_status": robotics_lab_chain_status(),
        "neuromorphic_lab": os.getenv("CASTUO_NEUROMORPHIC_LAB", "").strip() == "1",
    }


def _register_lab_extras() -> None:
    from backend.integrations.robotics.lab_metrics_optional import attach_lab_prometheus
    from backend.integrations.robotics.neuromorphic_edge import attach_neuromorphic_routes
    from backend.integrations.robotics.scan3d_print import attach_scan3d_routes

    attach_neuromorphic_routes(app, _verify_lab_bearer)
    attach_scan3d_routes(app, _verify_lab_bearer)
    attach_lab_prometheus(app)


_register_lab_extras()
