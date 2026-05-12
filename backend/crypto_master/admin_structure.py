# backend/crypto_master/admin_structure.py
# Roles jerárquicos encriptados — Nivel 0 GREGORIO a 4 AUDIT.

from __future__ import annotations

from typing import Any, Dict, List

try:
    from .hierarchical_keys import ADMIN_STRUCTURE, get_admin_structure
except ImportError:
    from hierarchical_keys import ADMIN_STRUCTURE, get_admin_structure


def get_roles_table() -> List[Dict[str, Any]]:
    """Tabla niveles: Rol, Clave, Acceso, Riesgo."""
    return get_admin_structure()


def get_role_by_level(level: int) -> Dict[str, Any] | None:
    """Rol por nivel 0-4."""
    for r in ADMIN_STRUCTURE:
        if r["nivel"] == level:
            return r
    return None
