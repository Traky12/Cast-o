from __future__ import annotations

import os

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException

try:
    from api.middleware.tenant_middleware import get_tenant
    from api.models.tenant import Tenant
    from api.security.rbac import authorize_token, token_from_authorization_header
except ModuleNotFoundError:  # pragma: no cover
    from middleware.tenant_middleware import get_tenant
    from models.tenant import Tenant
    from security.rbac import authorize_token, token_from_authorization_header


router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR"])

_PRIVILEGED_ROLES = {
    "admin_general",
    "administrador",
    "ciso",
    "cumplimiento",
    "devops",
}


def _require_privileged_access(authorization: str | None, operation: str) -> None:
    runtime_env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    if runtime_env != "production":
        return
    token = token_from_authorization_header(authorization)
    if not token:
        raise HTTPException(
            status_code=401,
            detail=f"Authorization Bearer requerido para {operation}",
        )
    authorize_token(token, _PRIVILEGED_ROLES)


def _enqueue_backup(tenant_id: str, user_id: str) -> None:
    # Hook intencional para reemplazar por integración real con backup/S3.
    _ = (tenant_id, user_id)


@router.post("/delete")
async def gdpr_delete(
    user_id: str,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
    tenant: Tenant = Depends(get_tenant),
) -> dict[str, str]:
    _require_privileged_access(authorization, operation="/api/v1/gdpr/delete")
    background_tasks.add_task(_enqueue_backup, tenant.id, user_id)
    return {
        "status": "OK",
        "tenant": tenant.id,
        "user_id": user_id,
        "message": "Solicitud GDPR aceptada",
    }
