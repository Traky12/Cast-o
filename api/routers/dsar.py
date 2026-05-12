from __future__ import annotations

import os
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from security.rbac import authorize_token, token_from_authorization_header
except ModuleNotFoundError:  # pragma: no cover
    from api.security.rbac import authorize_token, token_from_authorization_header


router = APIRouter(prefix="/api/v1/dsar", tags=["RGPD", "DSAR"])

_PRIVILEGED_ROLES = {
    "admin_general",
    "administrador",
    "ciso",
    "cumplimiento",
    "devops",
}


def _require_privileged_access(authorization: str | None) -> None:
    runtime_env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    if runtime_env != "production":
        return
    token = token_from_authorization_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization Bearer requerido para DSAR")
    authorize_token(token, _PRIVILEGED_ROLES)


class DSARRequestType(str, Enum):
    access = "access"
    rectify = "rectify"
    delete = "delete"
    port = "port"


class DSARDataCategory(str, Enum):
    sensors = "sensors"
    blockchain = "blockchain"
    logs = "logs"


class DSARRequest(BaseModel):
    user_id: str = Field(..., min_length=2)
    request_type: DSARRequestType
    data_category: DSARDataCategory


@router.post("/request")
async def dsar_request(
    request: DSARRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    """Registra una solicitud DSAR (RGPD Art. 15-22) para su procesamiento."""
    _require_privileged_access(authorization)
    request_id = f"dsar-{uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    status = "processing" if request.request_type == DSARRequestType.delete else "queued"

    return {
        "status": status,
        "request_id": request_id,
        "user_id": request.user_id,
        "request_type": request.request_type.value,
        "data_category": request.data_category.value,
        "received_at": now,
    }
