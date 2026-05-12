"""
Quantum Auth Middleware — CASTÚO-SYSTEM™ infrastructure (QSEC-001)
FastAPI middleware: valida cabecera X-Quantum-Secure (JWT HS256) + roles.

Cabecera esperada:
    X-Quantum-Secure: Bearer <jwt_token>

Claims JWT esperados:
    sub  : identificador del dispositivo / usuario
    role : admin | api | iot

Secreto de firma leído desde CASTUO_QUANTUM_JWT_SECRET (Opción A/B):
    CASTUO_QUANTUM_JWT_SECRET_FILE → fichero con el secreto (prod)
    CASTUO_QUANTUM_JWT_SECRET      → variable de entorno (dev)

El middleware es opt-in: no interfiere con endpoints que no usen el decorador
`require_quantum_auth()`, por lo que no afecta a clientes legacy.

Reference:
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §2 (RBAC)
  - QSEC-001
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any, Iterable

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.fastapi.crypto import QuantumSecure

# ─── Secreto de firma ────────────────────────────────────────────────────────

def _read_jwt_secret() -> str:
    """Opción A (fichero) → Opción B (env). Devuelve "" si no configurado."""
    file_path = os.getenv("CASTUO_QUANTUM_JWT_SECRET_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            return ""
    return os.getenv("CASTUO_QUANTUM_JWT_SECRET", "")


_ALGORITHM = "HS256"
_VALID_ROLES = frozenset({"admin", "api", "iot"})


# ─── Dependencia FastAPI (functional API, QSEC-001) ──────────────────────────

def require_quantum_auth(allowed_roles: Iterable[str] | None = None):
    """
    FastAPI dependency factory para proteger endpoints con JWT cuántico.

    Uso:
        @app.get("/secure", dependencies=[Depends(require_quantum_auth(["admin"]))])

    Args:
        allowed_roles: Conjunto de roles permitidos. None = cualquier rol válido.
    """
    _allowed = frozenset(allowed_roles) if allowed_roles is not None else _VALID_ROLES

    def _dep(x_quantum_secure: str = Header(default="", alias="X-Quantum-Secure")) -> dict:
        secret = _read_jwt_secret()
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="CASTUO_QUANTUM_JWT_SECRET no configurado — endpoint no disponible",
            )

        if not x_quantum_secure.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Cabecera X-Quantum-Secure requerida (Bearer <jwt>)",
            )

        token = x_quantum_secure.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado")
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

        role = payload.get("role", "")
        if role not in _VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{role}' desconocido. Válidos: {sorted(_VALID_ROLES)}",
            )
        if role not in _allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{role}' no autorizado para este endpoint",
            )

        return {"sub": payload.get("sub"), "role": role}

    return _dep


def create_token(sub: str, role: str, secret: str | None = None) -> str:
    """
    Genera un JWT firmado con HS256. Solo para tests y scripts de administración.

    Args:
        sub: Identificador (device_id, username).
        role: Rol del sujeto (admin | api | iot).
        secret: Secreto de firma. Si None, usa CASTUO_QUANTUM_JWT_SECRET.
    """
    if role not in _VALID_ROLES:
        raise ValueError(f"role debe ser uno de {sorted(_VALID_ROLES)}, recibido: '{role}'")
    _secret = secret or _read_jwt_secret()
    if not _secret:
        raise RuntimeError("CASTUO_QUANTUM_JWT_SECRET no configurado")
    return jwt.encode({"sub": sub, "role": role}, _secret, algorithm=_ALGORITHM)


# ─── Middleware ASGI (class-based, para montaje en Starlette/FastAPI) ─────────

class QuantumAuthMiddleware(BaseHTTPMiddleware):
    """Autenticación para endpoints críticos usando cabecera cifrada."""

    def __init__(self, app, private_key_hex: str | None = None, required_roles: set[str] | None = None):
        super().__init__(app)
        self.quantum = QuantumSecure(private_key_hex=private_key_hex)
        self.required_roles = required_roles or {"admin", "iot", "api"}

    def _jwt_secret(self) -> str:
        secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret not configured",
            )
        return secret

    def _decrypt_token(self, encoded_header: str) -> str:
        try:
            encrypted_json = base64.b64decode(encoded_header).decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Quantum-Secure format",
            ) from exc

        try:
            return self.quantum.decrypt(json.loads(encrypted_json))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Quantum decryption failed",
            ) from exc

    def _validate_roles(self, roles: list[str]) -> bool:
        return any(role in self.required_roles for role in roles)

    async def dispatch(self, request: Request, call_next):
        token_header = request.headers.get("X-Quantum-Secure")
        if not token_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Quantum authentication required",
                headers={"WWW-Authenticate": "Quantum realm"},
            )

        decrypted_token = self._decrypt_token(token_header)
        try:
            payload: dict[str, Any] = jwt.decode(
                decrypted_token,
                self._jwt_secret(),
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            ) from exc

        if not self._validate_roles(payload.get("roles", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )

        request.state.user = payload
        return await call_next(request)
