from __future__ import annotations

import base64
import json
import os
from typing import Any

import jwt
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from infrastructure.fastapi.crypto import QuantumSecure


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
