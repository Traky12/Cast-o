# backend/api/routes/admin.py
"""Endpoints de administración: rotación de claves y emergencias. EU/OSS."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from ..security.audit import audit_logger
from ..security.keycloak import require_admin, require_dpo
from ..security.pqc import pqc
from ..services.emergency import EmergencyService
from ..services.key_rotation import KeyRotationService

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UnsealBody(BaseModel):
    shares: List[str]


class NotifyBody(BaseModel):
    incident_type: str
    details: Dict[str, Any] = {}


class PqcSignBody(BaseModel):
    data: str


class PqcVerifyBody(BaseModel):
    data: str
    signature: str


@router.post("/rotate-key/{key_name}")
async def rotate_key(
    key_name: str,
    background_tasks: BackgroundTasks,
    force: bool = False,
    _user=Depends(require_admin),
):
    """Rota una clave (requiere rol admin)."""
    rotation_service = KeyRotationService()
    result = rotation_service.rotate_key(key_name, force=force)

    if result.get("success"):
        background_tasks.add_task(
            lambda: __audit_sync(
                "admin_key_rotation",
                {"key_name": key_name, "force": force, "tx_hash": result.get("tx_hash")},
            )
        )
        return result
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=result.get("message", "Error en rotación"),
    )


def __audit_sync(event_type: str, data: dict) -> None:
    import asyncio
    try:
        asyncio.run(
            audit_logger.log_event(
                request=None,
                event_type=event_type,
                data=data,
                compliance={"iso_27001": ["A.10.1.1"], "gdpr": ["Art.32"]},
            )
        )
    except Exception:
        pass


@router.get("/rotation-status")
async def get_rotation_status(_user=Depends(require_dpo)):
    """Estado de rotación de todas las claves (requiere rol dpo)."""
    rotation_service = KeyRotationService()
    return rotation_service.get_rotation_status()


@router.post("/emergency/seal")
async def emergency_seal(
    background_tasks: BackgroundTasks,
    _user=Depends(require_admin),
):
    """Sella Vault en emergencia (requiere admin)."""
    emergency_service = EmergencyService()
    result = emergency_service.seal_vault()
    if result.get("success"):
        background_tasks.add_task(
            lambda: __audit_sync("admin_emergency_seal", {"tx_hash": result.get("tx_hash")})
        )
    return result


@router.post("/emergency/unseal")
async def emergency_unseal(
    body: UnsealBody,
    background_tasks: BackgroundTasks,
    _user=Depends(require_admin),
):
    """Desbloquea Vault con al menos 3 shares Shamir (requiere admin)."""
    emergency_service = EmergencyService()
    result = emergency_service.unseal_vault(body.shares)
    if result.get("success"):
        background_tasks.add_task(
            lambda: __audit_sync("admin_emergency_unseal", {"tx_hash": result.get("tx_hash"), "shares_used": 3})
        )
    return result


@router.post("/emergency/notify")
async def notify_authorities(
    body: NotifyBody,
    background_tasks: BackgroundTasks,
    _user=Depends(require_admin),
):
    """Notifica a autoridades por tipo de incidente (requiere admin)."""
    emergency_service = EmergencyService()
    result = emergency_service.notify_authorities(body.incident_type, body.details)
    if result.get("success"):
        background_tasks.add_task(
            lambda: __audit_sync(
                f"admin_emergency_notify_{body.incident_type}",
                {"tx_hash": result.get("tx_hash"), "incident_type": body.incident_type},
            )
        )
    return result


@router.get("/emergency/procedures")
async def get_emergency_procedures(_user=Depends(require_dpo)):
    """Devuelve los procedimientos de emergencia documentados (requiere dpo)."""
    emergency_service = EmergencyService()
    return emergency_service.get_emergency_procedures()


@router.post("/emergency/generate-report")
async def generate_emergency_report(
    body: NotifyBody,
    _user=Depends(require_admin),
):
    """Genera informe de emergencia (requiere admin)."""
    emergency_service = EmergencyService()
    return emergency_service.generate_emergency_report(body.incident_type, body.details)


@router.post("/pqc/sign")
async def sign_with_pqc(body: PqcSignBody, _user=Depends(require_admin)):
    """Firma datos con criptografía post-cuántica (requiere admin)."""
    return pqc.sign_data_pqc(body.data)


@router.post("/pqc/verify")
async def verify_pqc_signature(body: PqcVerifyBody, _user=Depends(require_admin)):
    """Verifica firma PQC (requiere admin)."""
    return {"valid": pqc.verify_signature_pqc(body.data, body.signature)}
