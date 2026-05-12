# -*- coding: utf-8 -*-
"""Modelos para Cuentas Pro: jerarquía, restricciones y gestión ética (AI Act UE, GDPR)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ContentRestriction(BaseModel):
    """Restricciones de contenido para cuentas Pro."""

    allowed_domains: List[str] = Field(default_factory=list)
    blocked_keywords: List[str] = Field(default_factory=list)
    max_content_length: int = 5000
    allowed_file_types: List[str] = Field(
        default_factory=lambda: ["pdf", "jpg", "png", "csv"]
    )
    moderation_level: Literal["low", "medium", "high"] = "medium"


class EthicalGuideline(BaseModel):
    """Directrices éticas para cuentas Pro (AI Act UE 2024/1689)."""

    equity: float = Field(1.0, ge=0.0, le=1.0)
    transparency: float = Field(1.0, ge=0.0, le=1.0)
    privacy: float = Field(1.0, ge=0.0, le=1.0)
    sustainability: float = Field(0.9, ge=0.0, le=1.0)
    compliance: List[str] = Field(
        default_factory=lambda: [
            "AI_Act_UE_2024_1689",
            "GDPR",
            "ISO_27001",
            "ISO_9001",
        ]
    )
    data_retention_days: int = Field(90, ge=1, le=3650)
    audit_frequency: Literal["weekly", "monthly", "quarterly"] = "monthly"


class ProAccountTier(BaseModel):
    """Niveles de cuenta Pro (jerarquía)."""

    name: Literal["basic", "advanced", "enterprise", "admin"]
    max_agents: int = 5
    max_storage_gb: int = 10
    api_requests_per_minute: int = 100
    support_level: Literal["email", "priority", "24/7", "dedicated"] = "email"
    features: List[str] = Field(default_factory=list)


class ProUserProfile(BaseModel):
    """Perfil de usuario Pro con preferencias y restricciones."""

    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    full_name: str = ""
    role: Literal["user", "moderator", "admin", "auditor", "data_protection_officer"] = "user"
    tier: Optional[ProAccountTier] = None
    restrictions: ContentRestriction = Field(default_factory=ContentRestriction)
    ethics: EthicalGuideline = Field(default_factory=EthicalGuideline)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    status: Literal["active", "suspended", "banned", "data_erased"] = "active"
    password_hash: Optional[str] = None  # En producción: hash bcrypt


class ProAccountActivity(BaseModel):
    """Registro de actividad para auditoría."""

    action: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConsentRecord(BaseModel):
    """Registro de consentimiento del usuario (GDPR Art. 7)."""

    user_id: str = ""
    purpose: str = ""  # ej: "marketing", "analytics", "necessary"
    consent_date: str = ""  # ISO format
    recorded_by: str = ""


class ProAccount(BaseModel):
    """Cuenta Pro con jerarquía y gestión ética (GDPR Art. 37: DPO)."""

    account_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner: Optional[ProUserProfile] = None
    members: List[ProUserProfile] = Field(default_factory=list)
    activity_log: List[ProAccountActivity] = Field(default_factory=list)
    billing_info: Dict[str, Any] = Field(default_factory=dict)
    compliance_reports: List[Dict[str, Any]] = Field(default_factory=list)
    status: Literal["active", "suspended", "cancelled"] = "active"
    # GDPR Art. 37: Delegado de Protección de Datos
    data_protection_officer: Optional[str] = Field(None, description="Email o contacto del DPO")
    # GDPR Art. 7: Gestión del consentimiento
    consent_records: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Registros de consentimiento: user_id, purpose, consent_date, recorded_by",
    )
