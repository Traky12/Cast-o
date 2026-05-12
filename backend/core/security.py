from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken


def _load_master_key() -> bytes:
    """Carga la MASTER_KEY desde entorno, en formato urlsafe_base64 para Fernet.

    No se debe hardcodear ninguna clave privada; en ausencia de variable se genera
    una clave efímera solo válida para la ejecución actual.
    """
    raw = os.getenv("CASTUO_AUDIT_MASTER_KEY")
    if raw:
        try:
            return base64.urlsafe_b64decode(raw.encode("utf-8"))
        except Exception:
            pass
    # Fallback efímero: suficiente para entornos de desarrollo, no para producción.
    return Fernet.generate_key()


def get_fernet() -> Fernet:
    """Devuelve una instancia de Fernet basada en MASTER_KEY."""
    key = _load_master_key()
    # Si key ya está en formato Fernet, no es necesario recodificar.
    if len(key) != 32:
        key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
    return Fernet(key)


def encrypt_audit_payload(payload: Dict[str, Any]) -> str:
    """Cifra un payload de auditoría antes de persistirlo.

    # AUDIT_LOG: Protege detalles internos de eventos de seguridad (GDPR/eIDAS).
    """
    f = get_fernet()
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    token = f.encrypt(data)
    return token.decode("utf-8")


def decrypt_audit_payload(token: str) -> Dict[str, Any]:
    """Descifra un payload de auditoría previamente cifrado (uso interno)."""
    f = get_fernet()
    try:
        data = f.decrypt(token.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
    except (InvalidToken, ValueError, json.JSONDecodeError):
        return {}


def compute_model_checksum(model_state: Dict[str, Any], salt: str | bytes) -> str:
    """Calcula checksum SHA-256 con SALT del estado de un modelo federado."""
    if isinstance(salt, str):
        salt_bytes = salt.encode("utf-8")
    else:
        salt_bytes = salt
    blob = json.dumps(model_state, sort_keys=True).encode("utf-8")
    return hashlib.sha256(salt_bytes + blob).hexdigest()


def compute_hmac_signature(secret: str | bytes, body: bytes) -> str:
    """Calcula firma HMAC-SHA256 para cabecera X-Castuo-Signature."""
    if isinstance(secret, str):
        key = secret.encode("utf-8")
    else:
        key = secret
    return hmac.new(key, body, hashlib.sha256).hexdigest()


def verify_hmac_signature(secret: str | bytes, body: bytes, provided: str) -> bool:
    """Verifica firma HMAC con comparación en tiempo constante."""
    expected = compute_hmac_signature(secret, body)
    try:
        return secrets.compare_digest(expected, provided)
    except Exception:
        return False


def build_error_hash(exc: Exception) -> str:
    """Genera un hash truncado del error real para correlación interna."""
    raw = f"{type(exc).__name__}:{str(exc)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]

