# -*- coding: utf-8 -*-
"""Autenticación por roles (CTAEX): IAM simplificado y lectura de secrets desde archivos."""
import os
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def read_secret(name: str) -> str:
    """Lee un secret desde variable de entorno o desde archivo (Docker Secrets)."""
    file_var = f"{name.upper()}_FILE"
    path = os.getenv(file_var)
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except OSError:
            pass
    return os.getenv(name.upper(), os.getenv(name, ""))


# Mapeo token/API key → rol (valor del secret; en producción usar JWT o BD)
def _build_role_by_token() -> Dict[str, str]:
    out: Dict[str, str] = {}
    role_by_key = {
        "CASTUO_ADMIN_GENERAL_BEARER": "admin_general",
        # Lab HTTP usa su propio stub; este token sirve si el monolito expone rutas bajo /api/robotics
        "CASTUO_ROBOTICS_LAB_BEARER_TOKEN": "robotics_lab",
        "GAIA_ADMIN_KEY": "admin",
        "DB_ADMIN_PASSWORD": "admin",
        "STRIPE_SECRET_KEY": "admin",
        "MQTT_TECHNICIAN_PASSWORD": "tecnico",
        "IOT_API_KEY": "tecnico",
        "FARMER_API_KEY": "agricultor",
        "AUDITOR_API_KEY": "auditor",
        "STRIPE_PUBLISHABLE_KEY": "ecommerce",
        "GAIA_CHAIN_PRIVATE_KEY": "blockchain",
    }
    for key, role in role_by_key.items():
        val = read_secret(key)
        if val:
            out[val] = role
    return out

ROLE_BY_TOKEN = _build_role_by_token()

# Rutas permitidas por rol (prefix). Solo admin_general tiene "*" (gobierno total IAM simplificado).
# admin = operaciones CTAEX/ecommerce acotadas (no sustituye al administrador general del sistema).
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin_general": ["*"],
    "admin": [
        "/trazabilidad",
        "/microgreens/sensors",
        "/certificacion",
        "/ecommerce",
    ],
    "robotics_lab": ["/api/robotics"],
    "tecnico": ["/api/environment", "/microgreens/sensors", "/api/water"],
    "agricultor": ["/api/microgreens/batches", "/api/environment/thresholds"],
    "auditor": ["/api/certificates", "/certificacion/ctaex"],
    "ecommerce": ["/api/ecommerce", "/ecommerce/create-checkout", "/certificacion/ctaex", "/api/certificates/verify"],
    "blockchain": ["/trazabilidad/gaia"],
}


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[Dict[str, Any]]:
    """Opcional: devuelve el usuario si hay Bearer token válido; si no, None (acceso público)."""
    if credentials is None:
        return None
    token = credentials.credentials
    role = ROLE_BY_TOKEN.get(token)
    if role is None:
        return None
    return {"role": role, "token": token}


def check_endpoint_permission(path: str, role: str) -> bool:
    """Comprueba si el rol puede acceder a la ruta (por prefix)."""
    allowed = ROLE_PERMISSIONS.get(role, [])
    if "*" in allowed:
        return True
    for prefix in allowed:
        if prefix.endswith("*"):
            prefix = prefix[:-1]
        if path.startswith(prefix):
            return True
    return False


def require_role(*allowed_roles: str) -> Callable:
    """Dependencia que exige uno de los roles indicados (y que el path esté permitido)."""

    async def _require(request: Request, user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Se requiere autenticación (Bearer token o API Key)",
            )
        if allowed_roles and user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{user.get('role')}' no autorizado para esta operación",
            )
        if not check_endpoint_permission(request.url.path, user.get("role", "")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rol sin permiso para este endpoint",
            )
        return user

    return _require
