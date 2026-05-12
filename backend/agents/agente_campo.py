# backend/agents/agente_campo.py
"""AGENTE_CAMPO: QR paneles → Consents GDPR auto. Métrica: Consents GDPR < 90% clientes → QR reenvío."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

UMBRAL_CONSENTS_PCT = float(os.getenv("AGENTE_CAMPO_CONSENTS_UMBRAL", "90.0"))


def process_consents_and_alert(
    consents_pct: float | None = None,
    clientes: List[Dict[str, Any]] | None = None,
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Evalúa % consents GDPR; si < umbral dispara reenvío QR / recordatorio."""
    context = context or {}
    consents_pct = consents_pct if consents_pct is not None else context.get("consents_pct", context.get("consent", 100.0))
    try:
        consents_pct = float(consents_pct)
    except (TypeError, ValueError):
        consents_pct = 100.0

    triggered = consents_pct < UMBRAL_CONSENTS_PCT
    result: Dict[str, Any] = {
        "agent": "AGENTE_CAMPO",
        "metric": "Consents GDPR",
        "value": consents_pct,
        "threshold": UMBRAL_CONSENTS_PCT,
        "triggered": triggered,
        "action": "qr_reenvio" if triggered else None,
    }

    if triggered:
        _trigger_qr_reenvio(context, clientes or [])
        result["action_result"] = "qr_reenvio_triggered"
        logger.warning("AGENTE_CAMPO: Consents %.1f%% < %.1f%% → QR reenvío", consents_pct, UMBRAL_CONSENTS_PCT)

    return result


def mark_consent_gdpr_ok(object_id: str, qr_scanned: bool = True) -> Dict[str, Any]:
    """Marca objeto Cliente como Consent GDPR ✓ (para flujo P2P Anytype → IA)."""
    return {
        "agent": "AGENTE_CAMPO",
        "object_id": object_id,
        "consent": True,
        "qr_scanned": qr_scanned,
        "status": "Procesado IA",
    }


def _trigger_qr_reenvio(context: Dict[str, Any], clientes: List[Dict[str, Any]]) -> None:
    """Dispara reenvío de QR / recordatorio (integración con backend consents o cola)."""
    backend = os.getenv("BACKEND_URL", "http://backend:8000")
    try:
        import httpx
        r = httpx.post(
            f"{backend}/api/consents/remind",
            json={"reason": "agente_campo_below_threshold", "client_ids": [c.get("id") for c in clientes if c.get("id")]},
            timeout=10.0,
        )
        if r.status_code in (200, 202, 404):
            logger.info("AGENTE_CAMPO: recordatorio consents enviado")
        else:
            logger.debug("AGENTE_CAMPO: remind %s (endpoint opcional)", r.status_code)
    except Exception as e:
        logger.debug("AGENTE_CAMPO: remind skip %s", e)
