# -*- coding: utf-8 -*-
"""Permisos por rol y niveles de cuenta Pro (mínimo privilegio)."""
from __future__ import annotations

from typing import Dict, List

from backend.models.pro_account import ProAccountTier
from backend.models.system_admin_playbook import ADMIN_GENERAL_ROLE

# Permisos por rol
ROLE_PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    "user": {
        "agents": ["create", "read", "update", "delete"],
        "content": ["create", "read"],
        "settings": ["read", "update"],
        "ethics": ["read"],
    },
    "moderator": {
        "agents": ["read", "update"],
        "content": ["create", "read", "update", "delete", "moderate"],
        "settings": ["read"],
        "ethics": ["read", "update"],
        "users": ["read", "suspend"],
    },
    "admin": {
        "agents": ["create", "read", "update", "delete"],
        "content": ["create", "read", "update", "delete", "moderate"],
        "settings": ["read", "update"],
        "ethics": ["read", "update"],
        "users": ["create", "read", "update", "delete", "suspend", "ban"],
        "billing": ["read", "update"],
    },
    # Administrador general: mismo núcleo que admin + gobierno de coherencia/seguridad (playbook en código).
    "admin_general": {
        "agents": ["create", "read", "update", "delete"],
        "content": ["create", "read", "update", "delete", "moderate"],
        "settings": ["read", "update"],
        "ethics": ["read", "update"],
        "users": ["create", "read", "update", "delete", "suspend", "ban"],
        "billing": ["read", "update"],
        "governance": ["read", "update"],
        "security": ["read", "update"],
        "system": ["read", "update"],
        "compliance": ["read", "update", "generate"],
        "keys": ["read"],
        "activity": ["read"],
    },
    "auditor": {
        "agents": ["read"],
        "content": ["read"],
        "settings": ["read"],
        "ethics": ["read"],
        "users": ["read"],
        "activity": ["read"],
        "compliance": ["read", "generate"],
    },
    "data_protection_officer": {
        "users": ["read"],  # Solo lectura de datos personales (GDPR)
        "activity": ["read"],  # Acceso a logs para auditorías
        "compliance": ["read", "generate"],  # Informes de cumplimiento
    },
}

# Niveles de cuenta Pro (tiers)
ACCOUNT_TIERS: Dict[str, ProAccountTier] = {
    "basic": ProAccountTier(
        name="basic",
        max_agents=5,
        max_storage_gb=10,
        api_requests_per_minute=100,
        support_level="email",
        features=["basic_agents", "content_restrictions"],
    ),
    "advanced": ProAccountTier(
        name="advanced",
        max_agents=20,
        max_storage_gb=50,
        api_requests_per_minute=500,
        support_level="priority",
        features=[
            "basic_agents",
            "content_restrictions",
            "advanced_analytics",
            "api_access",
        ],
    ),
    "enterprise": ProAccountTier(
        name="enterprise",
        max_agents=100,
        max_storage_gb=500,
        api_requests_per_minute=2000,
        support_level="24/7",
        features=[
            "basic_agents",
            "content_restrictions",
            "advanced_analytics",
            "api_access",
            "dedicated_support",
            "custom_integration",
            "cannabis_management",
        ],
    ),
    "admin": ProAccountTier(
        name="admin",
        max_agents=9999,
        max_storage_gb=9999,
        api_requests_per_minute=10000,
        support_level="dedicated",
        features=["all", "cannabis_management"],
    ),
}


def check_permission(role: str, resource: str, action: str) -> bool:
    """Verifica si un rol tiene permiso para una acción sobre un recurso."""
    if role == ADMIN_GENERAL_ROLE:
        return True
    if role not in ROLE_PERMISSIONS:
        return False
    perms = ROLE_PERMISSIONS[role]
    if resource not in perms:
        return False
    return action in perms[resource]
