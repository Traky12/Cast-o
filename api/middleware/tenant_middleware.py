from __future__ import annotations

from fastapi import HTTPException, Request

try:
    from models.tenant import Tenant
except ModuleNotFoundError:  # pragma: no cover
    from api.models.tenant import Tenant


def _sanitize_tenant_id(raw: str) -> str:
    tenant_id = raw.strip().lower()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID vacío")
    if not all(c.isalnum() or c == "-" for c in tenant_id):
        raise HTTPException(status_code=400, detail="X-Tenant-ID inválido")
    return tenant_id


async def get_tenant(request: Request) -> Tenant:
    """Resuelve el tenant desde cabecera X-Tenant-ID."""

    raw_tenant = request.headers.get("X-Tenant-ID")
    if not raw_tenant:
        # fallback compatible para entornos legacy/single-tenant
        raw_tenant = "default"

    tenant_id = _sanitize_tenant_id(raw_tenant)
    tenant = Tenant(
        id=tenant_id,
        name=f"Tenant {tenant_id}",
        db_schema=f"tenant_{tenant_id.replace('-', '_')}",
        iot_topic_prefix=f"castuo/{tenant_id}/",
    )
    request.state.tenant = tenant
    return tenant
