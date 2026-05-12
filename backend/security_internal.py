# -*- coding: utf-8 -*-
"""Seguridad interna CTAEX: redacción de secretos, sanitización de respuestas y auditoría."""
import json
import logging
import os
import re
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union
import secrets

# Claves que nunca deben aparecer en respuestas ni en logs (case-insensitive)
SENSITIVE_KEYS: Set[str] = {
    "password", "secret", "api_key", "apikey", "private_key", "token",
    "authorization", "bearer", "stripe_secret", "webhook_secret",
    "db_password", "mqtt_password", "gaia_chain_private_key",
    "access_token", "refresh_token", "credential", "pin", "pwd",
}

# Patrones de clave sensible (regex)
SENSITIVE_PATTERN = re.compile(
    r"^(.*(?:password|secret|key|token|credential|auth|private).*)$",
    re.IGNORECASE,
)

REDACTED = "***REDACTED***"
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "")
_audit_lock = threading.Lock()

# Rate limit: (ip, path) -> list of timestamps (solo ventana reciente)
_rate_store: Dict[str, List[float]] = defaultdict(list)
_rate_lock = threading.Lock()
RATE_WINDOW = 60.0  # segundos
RATE_MAX_REQUESTS = 60  # máx por IP por path en la ventana

# --- Correlación: storm detection + aislamiento de nodo ---
# Por defecto se mantiene “compatibilidad Base44” al no aislar salvo que se habilite explícitamente.
EDUCACION_STORM_THRESHOLD = int(os.getenv("EDUCACION_STORM_THRESHOLD", "100").strip() or "100")
EDUCACION_STORM_WINDOW_SECONDS = float(os.getenv("EDUCACION_STORM_WINDOW_SECONDS", "1").strip() or "1")
EDUCACION_ISOLATION_SECONDS = int(os.getenv("EDUCACION_ISOLATION_SECONDS", "30").strip() or "30")
EDUCACION_ISOLATION_ON_STORM = os.getenv("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true"

# Pseudonimización: salt rotativo del búnker para impedir que un auditor reconstruya identidad.
_API_KEY_LOG_SALT: Optional[str] = None
_API_KEY_LOG_SALT_EPOCH: Optional[str] = None

_api_key_storm_store: Dict[str, List[float]] = defaultdict(list)
_api_key_isolated_until: Dict[str, float] = {}
_storm_lock = threading.Lock()

logger = logging.getLogger(__name__)


def _is_sensitive_key(key: str) -> bool:
    if not key or not isinstance(key, str):
        return False
    k = key.lower().replace("-", "_").replace(".", "_")
    if k in SENSITIVE_KEYS:
        return True
    return bool(SENSITIVE_PATTERN.match(k))


def redact_secrets(obj: Any) -> Any:
    """Recorre dict/list y reemplaza valores de claves sensibles por REDACTED. No modifica el original."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {
            k: REDACTED if _is_sensitive_key(k) else redact_secrets(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact_secrets(item) for item in obj]
    return obj


def sanitize_response_body(body: bytes, content_type: str) -> bytes:
    """Si el cuerpo es JSON, redacta claves sensibles y devuelve el nuevo cuerpo."""
    if not body or not content_type or "application/json" not in content_type.lower():
        return body
    try:
        data = json.loads(body.decode("utf-8"))
        sanitized = redact_secrets(data)
        return json.dumps(sanitized, ensure_ascii=False).encode("utf-8")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return body


def audit_log(
    event_type: str,
    path: str,
    method: str,
    role: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Registro de auditoría sin datos confidenciales. Escribe a archivo si AUDIT_LOG_PATH está definido."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "path": path,
        "method": method,
        "role": role,
        "resource_id": resource_id,
        "ip": ip,
        **(redact_secrets(extra) if extra else {}),
    }
    with _audit_lock:
        if AUDIT_LOG_PATH:
            try:
                with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError as e:
                logger.warning("No se pudo escribir audit log: %s", e)
        logger.info("audit %s %s %s role=%s", event_type, method, path, role or "-")


def _get_api_key_log_salt() -> str:
    """
    Devuelve un salt efímero (o semideterminista si se define por env).
    Permite que `api_key_id` sea pseudonimizado sin guardar el api_key real en logs.
    """
    global _API_KEY_LOG_SALT, _API_KEY_LOG_SALT_EPOCH

    salt_env = os.getenv("EDUCACION_API_KEY_LOG_SALT", "").strip()
    epoch_env = os.getenv("EDUCACION_API_KEY_LOG_SALT_ROTATE_EPOCH", "").strip()
    if salt_env:
        return salt_env

    # Si hay “epoch” y cambia, rotamos el salt en caliente (sin reiniciar proceso).
    if not epoch_env:
        if _API_KEY_LOG_SALT is None:
            _API_KEY_LOG_SALT = secrets.token_hex(16)
        return _API_KEY_LOG_SALT

    if _API_KEY_LOG_SALT is None or _API_KEY_LOG_SALT_EPOCH != epoch_env:
        _API_KEY_LOG_SALT_EPOCH = epoch_env
        _API_KEY_LOG_SALT = secrets.token_hex(16)
    return _API_KEY_LOG_SALT


def pseudonymize_api_key(api_key: str) -> str:
    """
    Pseudonimiza el api_key para correlación y storm detection.
    NO reversible: se usa un salt rotativo del búnker.
    """
    import hashlib

    salt = _get_api_key_log_salt()
    h = hashlib.blake3((api_key + "|" + salt).encode("utf-8")).hexdigest()
    # Cortar para logs legibles sin pérdida operativa.
    return h[:20]


def check_and_handle_request_storm(
    *,
    api_key_pseudo: str,
    request_id: str,
) -> bool:
    """
    Devuelve True si debe activarse aislamiento por tormenta.
    El aislamiento es opcional (feature env EDUCACION_ISOLATION_ON_STORM).
    """
    now = time.monotonic()
    threshold = EDUCACION_STORM_THRESHOLD
    window = EDUCACION_STORM_WINDOW_SECONDS

    with _storm_lock:
        # Si ya está aislado, mantenemos estado.
        until = _api_key_isolated_until.get(api_key_pseudo)
        if until is not None and now < until:
            return True

        store = _api_key_storm_store[api_key_pseudo]
        store.append(now)
        store[:] = [t for t in store if now - t <= window]

        if len(store) >= threshold:
            if EDUCACION_ISOLATION_ON_STORM:
                _api_key_isolated_until[api_key_pseudo] = now + float(EDUCACION_ISOLATION_SECONDS)
            # Limpiar para no “amplificar” tormenta.
            _api_key_storm_store[api_key_pseudo] = []
            return True

    return False


def check_rate_limit(ip: str, path: str) -> bool:
    """True si la petición está permitida; False si se superó el límite."""
    key = f"{ip}|{path}"
    now = time.monotonic()
    with _rate_lock:
        _rate_store[key] = [t for t in _rate_store[key] if now - t < RATE_WINDOW]
        if len(_rate_store[key]) >= RATE_MAX_REQUESTS:
            return False
        _rate_store[key].append(now)
    return True


def get_client_ip(request: Any) -> str:
    """Obtiene la IP del cliente desde headers de proxy o scope."""
    if hasattr(request, "headers"):
        for h in ("x-forwarded-for", "x-real-ip", "cf-connecting-ip"):
            v = request.headers.get(h)
            if v:
                return v.split(",")[0].strip()
    if hasattr(request, "scope") and request.scope.get("client"):
        return request.scope["client"][0] if isinstance(request.scope["client"], (list, tuple)) else str(request.scope["client"])
    return "unknown"


# --- IP Whitelisting (opcional: ALLOWED_IPS en env) ---
def _parse_allowed_ips() -> List[str]:
    raw = os.getenv("ALLOWED_IPS", "").strip()
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


_ALLOWED_IPS_CACHE: Optional[List[str]] = None


def get_allowed_ips() -> List[str]:
    """Lista de IPs o redes permitidas (ej: 89.167.5.0/24, 195.235.100.123, 127.0.0.1)."""
    global _ALLOWED_IPS_CACHE
    if _ALLOWED_IPS_CACHE is None:
        _ALLOWED_IPS_CACHE = _parse_allowed_ips()
    return _ALLOWED_IPS_CACHE


def ip_in_whitelist(client_ip: str, allowed: Optional[List[str]] = None) -> bool:
    """
    True si client_ip está permitida. allowed: lista de IPs o CIDR (ej. 89.167.5.0/24).
    Si allowed es None, usa ALLOWED_IPS de env. Si no hay lista, devuelve True (sin whitelist).
    """
    if allowed is None:
        allowed = get_allowed_ips()
    if not allowed:
        return True
    for entry in allowed:
        entry = entry.strip()
        if not entry:
            continue
        if "/" in entry:
            prefix = entry.split("/")[0]
            prefix_parts = prefix.split(".")
            if len(prefix_parts) >= 3:
                # /24: mismos 3 primeros octetos
                if client_ip.startswith(".".join(prefix_parts[:3]) + "."):
                    return True
            elif client_ip == prefix:
                return True
        else:
            if client_ip == entry:
                return True
    return False


def check_ip_whitelist(request: Any, allowed: Optional[List[str]] = None) -> None:
    """
    Si ALLOWED_IPS está definido y la IP del request no está permitida, lanza HTTPException 403.
    Usar en middleware o en dependencias de endpoints sensibles.
    """
    from fastapi import HTTPException

    allowed_list = allowed or get_allowed_ips()
    if not allowed_list:
        return
    ip = get_client_ip(request) if hasattr(request, "headers") else "unknown"
    if not ip_in_whitelist(ip, allowed_list):
        raise HTTPException(status_code=403, detail="IP no autorizada")
