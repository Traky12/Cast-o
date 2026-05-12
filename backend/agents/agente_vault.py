# backend/agents/agente_vault.py
"""AGENTE_VAULT: Kyber-768 rotación → Auto-reseal. Métrica: Rotación días < 30d → Auto Kyber-768."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

VAULT_URL = os.getenv("VAULT_URL", os.getenv("VAULT_ADDR", "http://vault:8200"))
ROTATION_DAYS_UMBRAL = int(os.getenv("AGENTE_VAULT_ROTATION_DAYS", "30"))


def rotate_kyber768(
    days_left: int | None = None,
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Dispara rotación Kyber-768 si días hasta rotación < umbral. Acción: auto-rotate + reseal si aplica."""
    context = context or {}
    days_left = days_left if days_left is not None else context.get("days_left", context.get("rotation_days_left", 31))
    try:
        days_left = int(days_left)
    except (TypeError, ValueError):
        days_left = 31

    triggered = days_left < ROTATION_DAYS_UMBRAL
    result: Dict[str, Any] = {
        "agent": "AGENTE_VAULT",
        "metric": "Rotación días",
        "value": days_left,
        "threshold": ROTATION_DAYS_UMBRAL,
        "triggered": triggered,
        "action": "auto_kyber768" if triggered else None,
    }

    if triggered:
        _do_rotate(context)
        result["action_result"] = "rotate_triggered"
        logger.warning("AGENTE_VAULT: rotación Kyber-768 días_left=%d < %d → auto-rotate", days_left, ROTATION_DAYS_UMBRAL)

    return result


def _do_rotate(context: Dict[str, Any]) -> None:
    """Llama al backend/Vault para rotar claves PQC. Sin VAULT_URL simula."""
    if not VAULT_URL or VAULT_URL.startswith("http://vault:"):
        logger.info("AGENTE_VAULT: rotación simulada (Kyber-768). Configurar VAULT_URL para producción.")
        return
    try:
        import httpx
        backend = os.getenv("BACKEND_URL", "http://backend:8000")
        r = httpx.post(
            f"{backend}/api/security/rotate-pqc",
            json={"algorithm": "Kyber-768", "reason": "anytype_agent_auto_rotation"},
            timeout=15.0,
        )
        if r.status_code in (200, 202):
            logger.info("AGENTE_VAULT: rotación PQC solicitada: %s", r.json())
        else:
            logger.warning("AGENTE_VAULT: rotación PQC %s %s", r.status_code, r.text)
    except Exception as e:
        logger.exception("AGENTE_VAULT: fallo rotación: %s", e)
