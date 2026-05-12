from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

try:
    from middleware.tenant_middleware import get_tenant
    from models.tenant import Tenant
except ModuleNotFoundError:  # pragma: no cover
    from api.middleware.tenant_middleware import get_tenant
    from api.models.tenant import Tenant


router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])


class UpdateTenantPhoneRequest(BaseModel):
    """Solicitud para actualizar números de teléfono de alertas de un tenant."""
    phone: str = Field(..., description="Número de teléfono para alertas del cultivo (formato: +34XXXXXXXXX)")
    

class TenantPhoneResponse(BaseModel):
    """Respuesta con información de contacto del tenant."""
    id: str
    name: str
    phone: str | None
    admin_phone: str | None
    updated_at: str


@router.get("/current")
async def get_current_tenant(tenant: Tenant = Depends(get_tenant)) -> dict[str, Any]:
    return {
        "status": "OK",
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "schema": tenant.db_schema,
            "iot_topic_prefix": tenant.iot_topic_prefix,
            "phone": tenant.phone,
            "admin_phone": tenant.admin_phone,
        },
    }


@router.put("/{tenant_id}/phone", response_model=TenantPhoneResponse)
async def update_tenant_phone(
    tenant_id: str,
    request: UpdateTenantPhoneRequest,
    tenant: Tenant = Depends(get_tenant)
) -> TenantPhoneResponse:
    """
    Actualiza el número de teléfono para alertas WhatsApp de un tenant.
    Validado contra el tenant autenticado para seguridad multi-tenant.
    """
    # Validar que el tenant autenticado coincida
    if tenant.id != tenant_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para actualizar este tenant"
        )
    
    # Validar formato de teléfono (simple: debe empezar con + y tener al menos 10 dígitos)
    if not request.phone.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="El número de teléfono debe comenzar con + (ej: +34693443825)"
        )
    
    digits_only = "".join(c for c in request.phone if c.isdigit())
    if len(digits_only) < 10:
        raise HTTPException(
            status_code=400,
            detail="El número de teléfono debe tener al menos 10 dígitos"
        )
    
    # Actualizar el tenant (aquí se simula; en producción seria una BD)
    tenant.phone = request.phone
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    
    return TenantPhoneResponse(
        id=tenant.id,
        name=tenant.name,
        phone=tenant.phone,
        admin_phone=tenant.admin_phone,
        updated_at=now,
    )

