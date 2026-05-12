from __future__ import annotations

import base64
import hashlib
import os
import unicodedata
from collections.abc import Callable
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


_BEARER_SCHEME = HTTPBearer(auto_error=False)

ROLE_ALIASES: dict[str, str] = {
    "superadmin": "admin_general",
    "super_admin": "admin_general",
    "administrador_general": "admin_general",
    "administrator": "administrador",
    "tecnico": "tecnico",
    "tecnico_soporte": "tecnico",
    "tecnico_campo": "tecnico",
    "user": "usuario",
    "student": "alumno",
    "sales": "comercial",
    "compliance": "cumplimiento",
    "security": "ciso",
}

ROLE_INHERITANCE: dict[str, set[str]] = {
    "admin_general": {
        "administrador",
        "tecnico",
        "usuario",
        "auditor",
        "comercial",
        "alumno",
        "devops",
        "ciso",
        "cumplimiento",
        "data_scientist",
    },
    "administrador": {"tecnico", "usuario", "comercial", "alumno"},
    "tecnico": {"usuario"},
    "auditor": {"usuario"},
    "devops": {"tecnico", "usuario"},
    "ciso": {"auditor", "cumplimiento"},
}


def _normalize_role(role: str) -> str:
    normalized = unicodedata.normalize("NFKD", role)
    ascii_role = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = ascii_role.strip().lower().replace("-", "_").replace(" ", "_")
    return ROLE_ALIASES.get(cleaned, cleaned)


def _expand_roles(roles: set[str]) -> set[str]:
    expanded = set(roles)
    changed = True
    while changed:
        changed = False
        for role in list(expanded):
            inherited = ROLE_INHERITANCE.get(role, set())
            new_roles = inherited - expanded
            if new_roles:
                expanded.update(new_roles)
                changed = True
    return expanded


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured",
        )
    return secret


def _decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from exc
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    role_values: list[str] = []
    raw_roles = payload.get("roles")
    if isinstance(raw_roles, list):
        role_values.extend(str(item) for item in raw_roles)
    raw_role = payload.get("role")
    if isinstance(raw_role, str):
        role_values.append(raw_role)

    normalized_roles = [_normalize_role(role) for role in role_values if role]
    payload["roles"] = sorted(_expand_roles(set(normalized_roles)))
    return payload


def token_from_authorization_header(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def authorize_token(token: str, required_roles: set[str]) -> dict[str, Any]:
    payload = _decode_token(token)
    token_roles = set(payload.get("roles", []))
    normalized_required = {_normalize_role(role) for role in required_roles}
    if not token_roles.intersection(normalized_required):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return payload


def current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(_BEARER_SCHEME),
) -> dict[str, Any]:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return _decode_token(credentials.credentials)


def require_roles(*required_roles: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    normalized_required = {_normalize_role(role) for role in required_roles}

    def dependency(identity: dict[str, Any] = Depends(current_identity)) -> dict[str, Any]:
        user_roles = set(identity.get("roles", []))
        if not user_roles.intersection(normalized_required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return identity

    return dependency


def encryption_key_from_env() -> bytes:
    explicit_key = os.getenv("DATA_ENCRYPTION_KEY")
    if explicit_key:
        return explicit_key.encode("utf-8")

    seed = _jwt_secret().encode("utf-8")
    derived = hashlib.sha256(seed).digest()
    return base64.urlsafe_b64encode(derived)