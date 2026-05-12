from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

try:
    from middleware.tenant_middleware import get_tenant
    from models.tenant import Tenant
    from services.traces import traces_client
except ModuleNotFoundError:  # pragma: no cover
    from api.middleware.tenant_middleware import get_tenant
    from api.models.tenant import Tenant
    from api.services.traces import traces_client


router = APIRouter(prefix="/api/v1/traces", tags=["TRACES"])


def _runtime_env() -> str:
    return os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()


class TracesRequest(BaseModel):
    lote_id: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/submit-tenant")
async def submit_to_traces(
    request: TracesRequest,
    tenant: Tenant = Depends(get_tenant),
) -> dict[str, Any]:
    if _runtime_env() == "production" and os.getenv(
        "ENABLE_TRACES_SUBMIT", "false"
    ).strip().lower() not in {"1", "true", "yes", "on"}:
        raise HTTPException(
            status_code=503,
            detail="Integración TRACES deshabilitada por política",
        )

    metadata = dict(request.metadata)
    metadata["tenant_id"] = tenant.id
    return traces_client.submit_to_traces(request.lote_id, metadata)
