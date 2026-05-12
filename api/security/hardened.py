"""
Módulo de hardening y seguridad integral para CASTUO-SYSTEM.

Incluye:
- Validación obligatoria de secretos en producción
- Security headers HTTP (HSTS, X-Frame, CSP, etc)
- Rate limiting decorador
- CORS configuración segura
- Validación de origen y tokens
- Auditoría de seguridad
"""

import functools
import hashlib
import logging
import os
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


# =========================================================================
# 1. VALIDACIÓN DE SECRETOS OBLIGATORIOS
# =========================================================================

class SecretValidator:
    """Valida que los secretos obligatorios se hayan configurado."""

    REQUIRED_IN_PRODUCTION = {
        "JWT_SECRET": "Token authentication secret",
        "DEVICE_JWT_SECRET": "IoT device authentication secret",
    }

    STRONGLY_RECOMMENDED = {
        "API_KEY": "API key for external integrations",
        "WEBHOOK_SECRET": "GitHub webhook verification secret",
        "TRACES_API_KEY": "TRACES system API key",
    }

    @staticmethod
    def _runtime_env() -> str:
        """Resuelve entorno runtime: ENV → ENVIRONMENT → development."""
        return os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()

    @classmethod
    def validate(cls) -> dict[str, Any]:
        """
        Valida secretos en modo estricto según entorno.
        
        Retorna:
            dict con claves 'missing_required', 'missing_recommended', 'status'
        """
        env = cls._runtime_env()
        missing_required = []
        missing_recommended = []

        # En producción, obligatorio
        if env == "production":
            for secret_name, description in cls.REQUIRED_IN_PRODUCTION.items():
                if not os.getenv(secret_name):
                    missing_required.append(f"{secret_name}: {description}")

            if missing_required:
                msg = f"Secretos obligatorios faltantes en producción: {', '.join(missing_required)}"
                logger.error(msg)
                raise RuntimeError(msg)
            
            logger.info("✅ Todos los secretos obligatorios configurados en producción")

        # Recomendados en cualquier entorno
        for secret_name, description in cls.STRONGLY_RECOMMENDED.items():
            if not os.getenv(secret_name):
                missing_recommended.append(f"{secret_name}: {description}")

        if missing_recommended and env == "production":
            logger.warning(f"⚠️  Secretos recomendados faltantes: {', '.join(missing_recommended)}")

        return {
            "environment": env,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "status": "secure" if not missing_required else "insecure",
        }


# =========================================================================
# 2. SECURITY HEADERS MIDDLEWARE
# =========================================================================

class SecurityHeadersMiddleware:
    """
    Middleware que añade headers de seguridad HTTP estándar según OWASP.
    """

    HEADERS = {
        "X-Content-Type-Options": "nosniff",  # Previene MIME-type sniffing
        "X-Frame-Options": "DENY",  # Previene clickjacking
        "X-XSS-Protection": "1; mode=block",  # Protección XSS (legacy)
        "Referrer-Policy": "strict-origin-when-cross-origin",  # Control de referrer
        "Permissions-Policy": (
            "geolocation=(), microphone=(), camera=(), usb=(), "
            "payment=(), magnetometer=(), gyroscope=(), accelerometer=()"
        ),
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",  # HSTS
    }

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                # Agregar security headers a la respuesta
                headers = list(message.get("headers", []))
                for header_name, header_value in self.HEADERS.items():
                    # Convertir a bytes para Starlette
                    headers.append((
                        header_name.lower().encode(),
                        header_value.encode(),
                    ))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)


# =========================================================================
# 3. RATE LIMITING DECORADOR
# =========================================================================

class RateLimitStore:
    """Almacén en memoria para rate limiting (escalable a Redis)."""

    def __init__(self, default_limit: int = 100, window_seconds: int = 60) -> None:
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._records: dict[str, list[float]] = {}

    def is_allowed(self, key: str, limit: Optional[int] = None) -> bool:
        """Verifica si la key está dentro del límite."""
        limit = limit or self.default_limit
        now = time.time()
        min_time = now - self.window_seconds

        # Limpiar timestamps antiguos
        if key in self._records:
            self._records[key] = [ts for ts in self._records[key] if ts > min_time]
        else:
            self._records[key] = []

        # Si no hay space, rechazar
        if len(self._records[key]) >= limit:
            return False

        # Registrar este intento
        self._records[key].append(now)
        return True

    def get_remaining(self, key: str, limit: Optional[int] = None) -> int:
        """Retorna requests restantes antes de rate limit."""
        limit = limit or self.default_limit
        now = time.time()
        min_time = now - self.window_seconds

        if key in self._records:
            valid = [ts for ts in self._records[key] if ts > min_time]
            return max(0, limit - len(valid))
        return limit


# Store global
rate_limit_store = RateLimitStore(default_limit=100, window_seconds=60)


def rate_limit(
    limit: int = 100, window_seconds: int = 60
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """
    Decorador de rate limiting basado en client IP.
    
    Uso:
        @rate_limit(limit=10, window_seconds=60)
        async def endpoint(request: Request):
            ...
    """

    def decorator(
        func: Callable[..., Awaitable[Any]],
    ) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            request = kwargs.get("request") or (
                args[0] if args and isinstance(args[0], Request) else None
            )
            if request is None:
                return await func(*args, **kwargs)

            client_ip = request.client.host if request.client else "unknown"
            key = f"ratelimit:{client_ip}:{func.__name__}"

            store = RateLimitStore(default_limit=limit, window_seconds=window_seconds)
            if not store.is_allowed(key, limit=limit):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(window_seconds)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# =========================================================================
# 4. CORS CONFIGURACIÓN SEGURA
# =========================================================================

class CORSConfig:
    """Configuración de CORS según entorno."""

    @staticmethod
    def get_allowed_origins() -> list[str]:
        """Retorna origins permitidos según entorno."""
        env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()

        if env == "production":
            # En producción, solo origins conocidos
            trusted_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
            return [origin.strip() for origin in trusted_origins if origin.strip()]
        else:
            # En desarrollo, más permisivos
            return [
                "http://localhost:3000",
                "http://localhost:5432",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5432",
            ]

    @staticmethod
    def setup_cors(app: Any) -> None:
        """Configura CORS middleware en la app."""
        allowed_origins = CORSConfig.get_allowed_origins()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            allow_headers=["*"],
            max_age=3600,  # Cache preflight 1 hora
        )

        logger.info(f"CORS configurado: {len(allowed_origins)} origins permitidos")


# =========================================================================
# 5. AUDITORÍA Y LOGGING DE SEGURIDAD
# =========================================================================

class SecurityAudit:
    """Registra eventos de seguridad para auditoría."""

    @staticmethod
    def log_event(
        event_type: str,
        severity: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Registra un evento de seguridad.
        
        Args:
            event_type: tipo de evento (auth_failure, rbac_denial, suspicious_activity, etc)
            severity: critical, high, medium, low
            user_id: ID del usuario involucrado
            ip_address: IP de origen
            details: dict con detalles adicionales
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        audit_log = {
            "timestamp": timestamp,
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id or "unknown",
            "ip_address": ip_address or "unknown",
            "details": details or {},
        }

        logger.warning(f"SECURITY_AUDIT: {audit_log}")

    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash de datos sensibles para logs (no reversible)."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# =========================================================================
# 6. TOKEN VALIDATION HARDENED
# =========================================================================

class TokenValidator:
    """Validador de tokens con verificaciones adicionales."""

    MAX_TOKEN_AGE_SECONDS = 3600  # 1 hora

    @staticmethod
    def validate_token_age(token_claims: dict[str, Any]) -> bool:
        """Verifica que el token no sea demasiado viejo."""
        issued_at = token_claims.get("iat")
        if not issued_at:
            return False

        age = time.time() - issued_at
        if age > TokenValidator.MAX_TOKEN_AGE_SECONDS:
            logger.warning(f"Token demasiado viejo: {age}s > {TokenValidator.MAX_TOKEN_AGE_SECONDS}s")
            return False

        return True

    @staticmethod
    def validate_required_claims(token_claims: dict[str, Any]) -> bool:
        """Verifica que el token tenga los claims requeridos."""
        required_claims = {"sub", "iat", "roles"}
        missing = required_claims - set(token_claims.keys())

        if missing:
            logger.warning(f"Token missing required claims: {missing}")
            return False

        return True


# =========================================================================
# 7. INPUT VALIDATION UTILITIES
# =========================================================================

class InputValidator:
    """Utilidades para validar entrada de usuario."""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitiza strings: remove null bytes, control chars, limita largo."""
        if not isinstance(value, str):
            raise ValueError("Expected string input")

        # Remove null bytes
        sanitized = value.replace("\x00", "")

        # Remove control characters (excepto \n, \r, \t)
        sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in "\n\r\t")

        # Truncate if needed
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validación básica de email."""
        if not email or len(email) > 254:
            return False

        # Simple pattern check
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_uuid(value: str) -> bool:
        """Valida que sea un UUID válido."""
        import uuid

        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
