"""
Autenticación JWT por dispositivo IoT y rate-limiting en memoria.

NOTA: El rate-limiting en memoria es válido para un único worker.
En producción multi-worker use Redis (slowapi + redis backend).
"""

import os
from importlib import import_module
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TypedDict

import jwt
from fastapi import HTTPException

pyotp: Any | None = None
with suppress(Exception):  # pragma: no cover
    pyotp = import_module("pyotp")


MFA_ENABLED = os.getenv("MFA_ENABLED", "false").lower() == "true"


class _RateRecord(TypedDict):
    count: int
    window_start: float


def verify_totp_code(code: str | None, secret: str | None = None) -> bool:
    """Valida un código TOTP de 6 dígitos.

    En producción, MFA_ENABLED debe estar a true y MFA_SECRET configurado.
    """
    if not MFA_ENABLED:
        return True

    if not code:
        return False

    mfa_secret = secret or os.getenv("MFA_SECRET", "")
    if not mfa_secret:
        return False

    if pyotp is None:
        return False

    try:
        totp = pyotp.TOTP(mfa_secret)
        return bool(totp.verify(code, valid_window=1))
    except Exception:
        return False


class DeviceAuth:
    """Autenticación y rate limiting para dispositivos IoT.

    Usa PyJWT (ya en requirements.txt). El secreto se lee **siempre**
    desde la variable de entorno DEVICE_JWT_SECRET; si no está definida
    se lanza un error en producción (ENV=production).
    """

    ALGORITHM = "HS256"

    def __init__(self) -> None:
        # device_id → {"count": int, "window_start": float}
        self._device_rates: dict[str, _RateRecord] = {}

    @property
    def _secret(self) -> str:
        secret = os.getenv("DEVICE_JWT_SECRET", "")
        if not secret:
            env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
            if env == "production":
                raise RuntimeError(
                    "DEVICE_JWT_SECRET no configurado — obligatorio en producción."
                )
            # En desarrollo usamos un secreto fijo inofensivo
            secret = "dev-only-insecure-secret"
        return secret

    # ------------------------------------------------------------------
    # Generación de tokens
    # ------------------------------------------------------------------

    def create_device_token(
        self, device_id: str, expires_minutes: int = 60
    ) -> str:
        """Genera un JWT HS256 para un dispositivo IoT."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": device_id,
            "iat": now,
            "exp": now + timedelta(minutes=expires_minutes),
            "scope": "iot:telemetry",
        }
        return jwt.encode(payload, self._secret, algorithm=self.ALGORITHM)

    # ------------------------------------------------------------------
    # Validación de tokens
    # ------------------------------------------------------------------

    def validate_device_token(self, token: str) -> str:
        """Valida el JWT y retorna el device_id (claim 'sub').

        Lanza HTTPException 401 si el token es inválido o expirado.
        """
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=[self.ALGORITHM]
            )
            device_id: Optional[str] = payload.get("sub")
            if not device_id:
                raise HTTPException(status_code=401, detail="Token sin subject")
            return device_id
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail=f"JWT inválido: {exc}")

    # ------------------------------------------------------------------
    # Rate limiting por dispositivo
    # ------------------------------------------------------------------

    def check_rate_limit(
        self,
        device_id: str,
        limit: int = 100,
        window_seconds: int = 60,
    ) -> bool:
        """Comprueba y actualiza el contador de peticiones por dispositivo.

        Retorna True si la petición está permitida; False si supera el límite.
        """
        now = datetime.now(timezone.utc).timestamp()
        record = self._device_rates.get(device_id)

        if record is None or (now - record["window_start"]) > window_seconds:
            self._device_rates[device_id] = {"count": 1, "window_start": now}
            return True

        if record["count"] >= limit:
            return False

        record["count"] += 1
        return True


# Singleton
device_auth = DeviceAuth()
