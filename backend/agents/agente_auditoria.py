# backend/agents/agente_auditoria.py
"""AGENTE_AUDITOR: ISO 27001 92% → Alertas Stage 2. Métrica: ISO_27001% < 95% → Email Applus+."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

APPLUS_EMAIL = os.getenv("APPLUS_CERTIFICACION_EMAIL", "certificacion@applus.com")
UMBRAL_CRITICO_PORCENTAJE = float(os.getenv("AGENTE_AUDITOR_UMBRAL", "95.0"))


def alert_stage2(
    progress: float | None = None,
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Dispara alerta Stage 2 si certificación < umbral. Acción: email Applus+."""
    progress = progress if progress is not None else (context or {}).get("progress", 0.0)
    if isinstance(progress, dict):
        progress = progress.get("percentage", progress.get("value", 0.0))
    try:
        progress = float(progress)
    except (TypeError, ValueError):
        progress = 0.0

    triggered = progress < UMBRAL_CRITICO_PORCENTAJE
    result: Dict[str, Any] = {
        "agent": "AGENTE_AUDITOR",
        "metric": "ISO_27001%",
        "value": progress,
        "threshold": UMBRAL_CRITICO_PORCENTAJE,
        "triggered": triggered,
        "action": "email_applus" if triggered else None,
    }

    if triggered:
        _send_email_applus(progress, context or {})
        result["action_result"] = "email_sent"
        logger.warning("AGENTE_AUDITOR: ISO 27001 %.1f%% < %.1f%% → alerta Stage 2 enviada", progress, UMBRAL_CRITICO_PORCENTAJE)

    return result


def _send_email_applus(progress: float, context: Dict[str, Any]) -> None:
    """Envío simulado o real a certificacion@applus.com (configurable por SMTP)."""
    smtp_server = os.getenv("SMTP_SERVER")
    if not smtp_server:
        logger.info("AGENTE_AUDITOR: SMTP no configurado, simulación email a %s (ISO %.1f%%)", APPLUS_EMAIL, progress)
        return
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg["Subject"] = f"[CASTÚO] ISO 27001 Stage 2 - Progreso {progress:.1f}%"
        msg["From"] = os.getenv("SMTP_USER", "noreply@castuo.es")
        msg["To"] = APPLUS_EMAIL
        body = f"Progreso certificación ISO 27001: {progress:.1f}%. Umbral crítico: {UMBRAL_CRITICO_PORCENTAJE}%. Solicitud de seguimiento Stage 2."
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(smtp_server, int(os.getenv("SMTP_PORT", "587"))) as s:
            if os.getenv("SMTP_USER"):
                s.starttls()
                s.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
            s.send_message(msg)
        logger.info("AGENTE_AUDITOR: email enviado a %s", APPLUS_EMAIL)
    except Exception as e:
        logger.exception("AGENTE_AUDITOR: fallo envío email: %s", e)
