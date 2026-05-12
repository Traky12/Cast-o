"""Validación JWT vía JWKS Keycloak (alineado con backend/api/security/keycloak.py)."""
from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

_bearer = HTTPBearer(auto_error=False)


class GatewayUser(BaseModel):
    sub: str
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)


class _JWKSCache:
    def __init__(self) -> None:
        self._jwks: Optional[Dict[str, Any]] = None
        self._fetched_at: float = 0.0

    async def get(self, url: str, ttl_seconds: int = 300) -> Dict[str, Any]:
        now = time.time()
        if self._jwks and (now - self._fetched_at) < ttl_seconds:
            return self._jwks
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            self._jwks = r.json()
            self._fetched_at = now
            return self._jwks


_jwks_cache = _JWKSCache()


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


async def get_gateway_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> GatewayUser:
    if _env_bool("AUTH_DISABLED", default=False):
        return GatewayUser(sub="dev-gateway", email=None, roles=["admin", "technician", "viewer"])

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere Bearer JWT",
            headers={"WWW-Authenticate": "Bearer"},
        )

    keycloak_url = os.getenv("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "castuo-system")
    audience = os.getenv("KEYCLOAK_CLIENT_ID", "api-gateway")
    verify_aud = _env_bool("GATEWAY_VERIFY_AUD", default=True)
    token = credentials.credentials

    jwks_url = f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"

    try:
        jwks = await _jwks_cache.get(jwks_url)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="JWT sin kid")

        key = None
        for k in jwks.get("keys", []):
            if k.get("kid") == kid:
                key = k
                break
        if key is None:
            raise HTTPException(status_code=401, detail="JWKS kid no encontrado")

        if verify_aud:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=audience,
                options={"verify_aud": True},
            )
        else:
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        roles = (claims.get("realm_access") or {}).get("roles") or []
        return GatewayUser(
            sub=str(claims.get("sub", "")),
            email=claims.get("email"),
            roles=[str(r) for r in roles],
        )
    except HTTPException:
        raise
    except (JWTError, httpx.HTTPError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_any_role(*allowed: str):
    async def _check(user: GatewayUser = Depends(get_gateway_user)) -> GatewayUser:
        if not allowed:
            return user
        if not any(r in user.roles for r in allowed):
            raise HTTPException(status_code=403, detail="Rol insuficiente")
        return user

    return _check
