"""
Lectura opcional desde HashiCorp Vault KV v2 (hvac).
Si hvac, VAULT_ADDR o token (VAULT_TOKEN / VAULT_TOKEN_FILE) faltan, cadena vacía: usar auth_roles.read_secret() / *_FILE.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Paths lógicos (sin mount) alineados con VAULT_KV_PATHS.md
PATH_ADMIN_GENERAL_BEARER = "castuo/admin_general/bearer"
PATH_ROBOTICS_LAB_BEARER = "castuo/robotics/lab/bearer"
PATH_GAIA_CHAIN_PRIVATE_KEY = "castuo/gaia/chain/private_key"
PATH_ADMIN_MASTER_KEY = "castuo/admin/master_key"

_DEFAULT_MOUNT = "secret"


def vault_token_for_client() -> str:
    """
    Token para hvac: VAULT_TOKEN explícito, o contenido de VAULT_TOKEN_FILE (p. ej. /run/secrets/vault_token).
    Misma filosofía que auth_roles.read_secret: el fichero evita tokens en .env commiteado.
    """
    direct = (os.getenv("VAULT_TOKEN") or "").strip()
    if direct:
        return direct
    path = (os.getenv("VAULT_TOKEN_FILE") or "").strip()
    if not path or not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _client():
    try:
        import hvac  # type: ignore
    except ImportError:
        return None
    addr = (os.getenv("VAULT_ADDR") or "").strip()
    token = vault_token_for_client()
    if not addr or not token:
        return None
    c = hvac.Client(url=addr, token=token)
    if not c.is_authenticated():
        logger.warning("Vault: cliente no autenticado (token inválido o expirado).")
        return None
    return c


def read_kv_v2(path: str, field: str = "value", mount_point: str = _DEFAULT_MOUNT) -> str:
    """
    Lee una clave dentro del payload KV v2 (por defecto campo 'value').
    path: p.ej. 'castuo/admin_general/bearer' (sin 'secret/data/').
    """
    c = _client()
    if c is None:
        return ""
    try:
        r: Dict[str, Any] = c.secrets.kv.v2.read_secret_version(path=path, mount_point=mount_point)
        data = (r.get("data") or {}).get("data") or {}
        val = data.get(field)
        if val is None and len(data) == 1:
            val = next(iter(data.values()))
        return str(val).strip() if val is not None else ""
    except Exception as exc:
        logger.debug("Vault read_kv_v2 %s: %s", path, exc)
        return ""


def read_admin_general_bearer() -> str:
    return read_kv_v2(PATH_ADMIN_GENERAL_BEARER)


def read_robotics_lab_bearer() -> str:
    return read_kv_v2(PATH_ROBOTICS_LAB_BEARER)


def read_gaia_chain_private_key() -> str:
    return read_kv_v2(PATH_GAIA_CHAIN_PRIVATE_KEY, field="value")


def read_admin_master_key() -> str:
    return read_kv_v2(PATH_ADMIN_MASTER_KEY)
