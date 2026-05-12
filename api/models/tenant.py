from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    """Modelo de tenant para aislamiento lógico por cliente."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    db_schema: str
    iot_topic_prefix: str
    phone: Optional[str] = Field(None, description="Número de teléfono para alertas WhatsApp (formato: +34XXXXXXXXX)")
    admin_phone: Optional[str] = Field(None, description="Número de admin para emergencias del sistema")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[dict[str, Any]] = None


class TenantDBConfig(BaseModel):
    """Configuración de conexión por tenant (si aplica)."""

    db_schema: str
    host: str
    port: int
    user: str
    password: str
