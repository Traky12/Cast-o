from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from middleware.security import MFA_ENABLED, verify_totp_code
except ModuleNotFoundError:  # pragma: no cover
    from api.middleware.security import MFA_ENABLED, verify_totp_code


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    tenant_id: str = Field(default="default", min_length=1)
    role: str = Field(default="usuario", min_length=1)


class LoginResponse(BaseModel):
    token: str
    expires_at: str


class ProtectedResponse(BaseModel):
    status: str
    mfa_enabled: bool
    user: str
    tenant: str
    roles: list[str]


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT secret not configured")
    return secret


def _decode_auth_header(authorization: str | None) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = parts[1].strip()
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=60)
    token = jwt.encode(
        {
            "sub": payload.user_id,
            "tenant": payload.tenant_id,
            "roles": [payload.role],
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        },
        _jwt_secret(),
        algorithm="HS256",
    )
    return LoginResponse(token=token, expires_at=exp.isoformat())


@router.get("/protected", response_model=ProtectedResponse)
async def protected_route(
    authorization: str | None = Header(default=None),
    x_mfa_code: str | None = Header(default=None, alias="X-MFA-Code"),
) -> ProtectedResponse:
    payload = _decode_auth_header(authorization)

    if MFA_ENABLED and not verify_totp_code(x_mfa_code):
        raise HTTPException(status_code=403, detail="MFA required or invalid code")

    return ProtectedResponse(
        status="OK",
        mfa_enabled=MFA_ENABLED,
        user=str(payload.get("sub", "unknown")),
        tenant=str(payload.get("tenant", "default")),
        roles=[str(role) for role in payload.get("roles", [])],
    )
