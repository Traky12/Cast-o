"""
CASTÚO-SYSTEM™ v3.1 — Middleware de Seguridad
MFA TOTP, rate limiting por IP/usuario, multi-tenancy (X-Tenant-ID).

Variables de entorno:
    MFA_ENABLED                 Habilitar verificación TOTP (default: false)
    MFA_ISSUER                  Nombre del emisor TOTP (default: CASTUO-SYSTEM)
    RATE_LIMIT_ENABLED          Habilitar rate limiting (default: true)
    RATE_LIMIT_REQUESTS         Peticiones máximas por ventana (default: 100)
    RATE_LIMIT_WINDOW_S         Ventana de tiempo en segundos (default: 60)
    ALLOWED_TENANTS             Lista de tenants autorizados separada por comas
    DEFAULT_TENANT              Tenant por defecto cuando no se especifica
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Callable

from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute

logger = logging.getLogger("castuo.security")

# ── Configuración ──────────────────────────────────────────────────────────────

MFA_ENABLED         = os.getenv("MFA_ENABLED", "false").lower() == "true"
MFA_ISSUER          = os.getenv("MFA_ISSUER", "CASTUO-SYSTEM")
RATE_LIMIT_ENABLED  = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW_S = int(os.getenv("RATE_LIMIT_WINDOW_S", "60"))
DEFAULT_TENANT      = os.getenv("DEFAULT_TENANT", "castuo")
_ALLOWED_TENANTS_RAW = os.getenv("ALLOWED_TENANTS", "castuo,demo,staging")
ALLOWED_TENANTS: set[str] = {t.strip() for t in _ALLOWED_TENANTS_RAW.split(",") if t.strip()}

# Rutas excluidas de rate limiting (health checks, etc.)
_RATE_LIMIT_EXEMPT = {"/health", "/api/v1/health", "/docs", "/openapi.json", "/redoc"}

# ── Rate Limiter ───────────────────────────────────────────────────────────────

class _InMemoryRateLimiter:
    """
    Sliding-window rate limiter en memoria.
    Para producción, reemplazar con Redis usando INCR + EXPIRE.
    """

    def __init__(self, max_requests: int, window_s: int) -> None:
        self._max = max_requests
        self._window = window_s
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _key(self, request: Request) -> str:
        # Clave: IP real (respeta X-Forwarded-For del reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For", "")
        ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        tenant = request.headers.get("X-Tenant-ID", DEFAULT_TENANT)
        return f"{tenant}:{ip}"

    def is_allowed(self, request: Request) -> tuple[bool, int, int]:
        """
        Retorna (permitido, requests_restantes, reset_en_segundos).
        La decisión de si llamar a este método la toma el middleware (según RATE_LIMIT_ENABLED).
        """
        key = self._key(request)
        now = time.time()
        window_start = now - self._window

        with self._lock:
            timestamps = self._buckets[key]
            # Limpiar timestamps fuera de la ventana
            timestamps[:] = [t for t in timestamps if t > window_start]

            if len(timestamps) >= self._max:
                oldest = timestamps[0]
                reset_in = int(self._window - (now - oldest)) + 1
                return False, 0, reset_in

            timestamps.append(now)
            remaining = self._max - len(timestamps)
            reset_in = self._window

        return True, remaining, reset_in


_rate_limiter = _InMemoryRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_S)


# ── MFA TOTP ───────────────────────────────────────────────────────────────────

def verify_totp(secret: str, token: str) -> bool:
    """
    Verifica un token TOTP (RFC 6238) con ventana de ±1 período.
    Requiere: pip install pyotp
    """
    try:
        import pyotp  # type: ignore
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    except ImportError:
        logger.warning("[security] pyotp no instalado — MFA deshabilitado en runtime")
        return True  # fail-open en dev si no hay pyotp
    except Exception as exc:
        logger.warning("[security] Error verificando TOTP: %s", exc)
        return False


def generate_totp_uri(secret: str, account: str) -> str:
    """Genera URI para QR code de configuración TOTP."""
    try:
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=account, issuer_name=MFA_ISSUER)
    except ImportError:
        return f"otpauth://totp/{MFA_ISSUER}:{account}?secret={secret}&issuer={MFA_ISSUER}"


def new_totp_secret() -> str:
    """Genera un secreto TOTP base32 seguro."""
    try:
        import pyotp
        return pyotp.random_base32()
    except ImportError:
        import secrets
        import base64
        return base64.b32encode(secrets.token_bytes(20)).decode()


# ── Multi-tenancy ──────────────────────────────────────────────────────────────

def extract_tenant(request: Request) -> str:
    """
    Extrae el tenant del header X-Tenant-ID.
    Valida contra ALLOWED_TENANTS; rechaza si no es válido.
    Retorna el tenant validado.
    """
    tenant = request.headers.get("X-Tenant-ID", DEFAULT_TENANT).strip()
    if not tenant:
        tenant = DEFAULT_TENANT
    if ALLOWED_TENANTS and tenant not in ALLOWED_TENANTS:
        raise HTTPException(
            status_code=403,
            detail=f"Tenant '{tenant}' no autorizado. Tenants válidos: {sorted(ALLOWED_TENANTS)}",
        )
    return tenant


# ── FastAPI Middleware ─────────────────────────────────────────────────────────

async def security_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware principal de seguridad:
    1. Rate limiting por IP + tenant
    2. Extracción y validación de X-Tenant-ID
    3. Registro de tenant en request.state para uso en handlers
    """
    path = request.url.path

    # Extraer y validar tenant (antes del rate limit para incluirlo en la clave)
    tenant = request.headers.get("X-Tenant-ID", DEFAULT_TENANT).strip() or DEFAULT_TENANT
    if ALLOWED_TENANTS and tenant not in ALLOWED_TENANTS:
        return Response(
            content=f'{{"detail":"Tenant \'{tenant}\' no autorizado"}}',
            status_code=403,
            media_type="application/json",
        )
    request.state.tenant = tenant

    # Rate limiting (excluir rutas exentas; comprobar env en runtime para desactivar en tests)
    _rate_limit_on = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    if _rate_limit_on and path not in _RATE_LIMIT_EXEMPT:
        allowed, remaining, reset_in = _rate_limiter.is_allowed(request)
        if not allowed:
            return Response(
                content='{"detail":"Rate limit excedido. Intente de nuevo más tarde."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "Retry-After": str(reset_in),
                    "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_in),
                },
            )

    response = await call_next(request)

    # Añadir headers de rate limit informativos (solo si rate limiting activo)
    if _rate_limit_on and path not in _RATE_LIMIT_EXEMPT:
        _, remaining, reset_in = _rate_limiter.is_allowed(request)
        response.headers["X-RateLimit-Limit"]     = str(RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"]     = str(int(time.time()) + reset_in)
    response.headers["X-Tenant-ID"] = tenant

    return response


# ── Endpoint de tenant actual ──────────────────────────────────────────────────

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.get("/current", summary="Tenant actual de la petición")
async def get_current_tenant(request: Request) -> dict:
    """
    Retorna el tenant extraído del header X-Tenant-ID.
    Útil para verificar multi-tenancy en tests y debug.

    curl -H "X-Tenant-ID: demo" http://api.castuo-system.cloud/api/v1/tenants/current
    """
    tenant = getattr(request.state, "tenant", DEFAULT_TENANT)
    return {
        "tenant":          tenant,
        "allowed_tenants": sorted(ALLOWED_TENANTS),
        "mfa_enabled":     MFA_ENABLED,
        "rate_limit": {
            "enabled":     RATE_LIMIT_ENABLED,
            "max_requests": RATE_LIMIT_REQUESTS,
            "window_s":    RATE_LIMIT_WINDOW_S,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/mfa/setup", summary="Configuración TOTP para MFA")
async def mfa_setup(account: str = "admin") -> dict:
    """
    Genera un secreto TOTP y URI para configurar autenticador (Google Authenticator, Authy, etc.).
    En producción: persistir el secreto en la BD del usuario, no en respuesta.
    """
    secret = new_totp_secret()
    uri = generate_totp_uri(secret, account)
    return {
        "secret":    secret,
        "uri":       uri,
        "issuer":    MFA_ISSUER,
        "algorithm": "SHA1",
        "digits":    6,
        "period":    30,
        "aviso":     "Guardar el secreto de forma segura. Esta respuesta no se almacena.",
    }


@router.post("/mfa/verify", summary="Verificar token TOTP")
async def mfa_verify(secret: str, token: str) -> dict:
    """Verifica un token TOTP contra el secreto del usuario."""
    valid = verify_totp(secret, token)
    if not valid:
        raise HTTPException(status_code=401, detail="Token TOTP inválido o expirado")
    return {"valid": True, "timestamp": datetime.now(timezone.utc).isoformat()}
