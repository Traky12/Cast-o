# backend/api/security/keycloak.py
"""Autenticación OIDC con Keycloak (EU/OSS)."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel


class TokenData(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []
    token_id: Optional[int] = None
    compliance: Dict[str, Any] = {}

    class Config:
        frozen = True


_bearer = HTTPBearer(auto_error=False)


class _JWKSCache:
    def __init__(self) -> None:
        self._jwks: Optional[Dict[str, Any]] = None
        self._fetched_at: float = 0.0

    async def get(self, url: str, ttl_seconds: int = 300) -> Dict[str, Any]:
        now = time.time()
        if self._jwks and (now - self._fetched_at) < ttl_seconds:
            return self._jwks
        async with httpx.AsyncClient(timeout=10) as client:
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


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> TokenData:
    """Valida JWT de Keycloak y devuelve TokenData (EU/OSS)."""
    if _env_bool("AUTH_DISABLED", default=False):
        return TokenData(
            sub="dev-user",
            email=None,
            roles=["owner", "dpo"],
            token_id=12345,
            compliance={"gdpr": ["Art. 6.1(a)"]},
        )

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido (GDPR Art. 32)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    keycloak_url = os.getenv("KEYCLOAK_URL", "http://localhost:8080").rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", "castuo-system")
    audience = os.getenv("KEYCLOAK_CLIENT_ID", "backend")
    token = credentials.credentials

    if not keycloak_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="KEYCLOAK_URL no configurado",
        )

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

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=audience,
            options={"verify_aud": True},
        )

        roles = (claims.get("realm_access") or {}).get("roles") or []
        raw_token_id = claims.get("token_id") or claims.get("tokenId")
        token_id = None
        if raw_token_id is not None:
            try:
                token_id = int(raw_token_id)
            except (TypeError, ValueError):
                token_id = None
        if not token_id and "token_id" in str(claims):
            token_id = 12345  # fallback dev

        return TokenData(
            sub=str(claims.get("sub", "")),
            email=claims.get("email"),
            roles=[str(r) for r in roles],
            token_id=token_id,
            compliance=claims.get("compliance", {}),
        )
    except HTTPException:
        raise
    except (JWTError, httpx.HTTPError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token JWT inválido: {e} (GDPR Art. 32)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de autenticación: {e}",
        )


def require_role(required_role: str):
    async def _checker(user: TokenData = Depends(get_current_user)) -> TokenData:
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{required_role}' requerido (ISO 27001 A.9.1.1)",
            )
        return user

    return _checker


require_owner = require_role("owner")
require_dpo = require_role("dpo")
require_admin = require_role("admin")
