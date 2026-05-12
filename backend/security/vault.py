"""
CASTÚO-SYSTEM™ — Secrets resolver
Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §1 (Matriz A/B/C)

Opción A (recomendado prod): NAME_FILE=/run/secrets/<name>  → lee fichero montado
Opción B (alternativo prod): VAULT_ADDR + VAULT_TOKEN/_FILE → Vault KV v2
Opción C (PROHIBIDO prod):   NAME=<valor> en .env versionado → solo dev local comentado

read_secret("NAME"):
  1. Si NAME_FILE está en entorno → lee el fichero en esa ruta (Docker secret / Swarm).
  2. Si no → lee NAME del entorno (fallback dev).
  3. Nunca lanzar excepción: devuelve "" si nada está configurado.

El primer argumento es el nombre lógico (p.ej. "GAIACHAIN_API_KEY"),
NO el sufijo "_FILE". El código resuelve GAIACHAIN_API_KEY_FILE automáticamente.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

VAULT_ADDR: str = os.getenv("VAULT_ADDR", "")


# ─── Opción A — fichero montado (Docker secret / Swarm) ───────────────────────

def read_secret(name: str) -> str:
    """
    Resolve a secret by logical name.

    Priority:
      1. {NAME}_FILE env var → read file content at that path (Option A).
      2. {NAME} env var → plain value (dev fallback; never use in prod with real secrets).
      3. "" if neither is set.

    Usage:
        key = read_secret("GAIACHAIN_API_KEY")
        # In prod: set GAIACHAIN_API_KEY_FILE=/run/secrets/gaiachain_api_key
        # In dev:  set GAIACHAIN_API_KEY=localkey  (never commit the value)
    """
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            return ""
    return os.getenv(name, "")


# ─── Opción B — HashiCorp Vault KV v2 ────────────────────────────────────────

def vault_token_for_client() -> str:
    """
    Resolve Vault token.
    Priority: VAULT_TOKEN (env) > VAULT_TOKEN_FILE (direct file read).
    NOTE: reads VAULT_TOKEN_FILE with open(), NOT with read_secret() —
    the prontuario distinguishes between the two to avoid recursion.
    Returns "" if neither is configured.
    """
    token = os.getenv("VAULT_TOKEN", "")
    if token:
        return token
    token_file = os.getenv("VAULT_TOKEN_FILE", "")
    if token_file:
        try:
            with open(token_file) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return ""


def read_kv_v2(path: str) -> str:
    """
    Read a secret value from Vault KV v2 (default mount: secret/).
    Path is the logical path WITHOUT the mount prefix (e.g. 'castuo/admin_general/bearer').

    Returns "" if:
      - VAULT_ADDR is not set
      - No token is available
      - Vault is unreachable (network error)
      - Secret does not exist at that path

    The caller MUST fall back to read_secret() / *_FILE when this returns "".
    This ensures Option A always works even when Vault is down.
    """
    if not VAULT_ADDR:
        return ""
    token = vault_token_for_client()
    if not token:
        return ""
    try:
        resp = httpx.get(
            f"{VAULT_ADDR.rstrip('/')}/v1/secret/data/{path}",
            headers={"X-Vault-Token": token},
            timeout=5.0,
        )
        if resp.status_code == 200:
            return (
                resp.json()
                .get("data", {})
                .get("data", {})
                .get("value", "")
            )
    except httpx.RequestError:
        pass  # Vault unavailable → caller uses Option A fallback
    return ""
