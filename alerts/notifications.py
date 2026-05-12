# -*- coding: utf-8 -*-
"""Notificaciones de alertas a Slack y Telegram."""
import json
import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

SLACK_WEBHOOK = os.environ.get("CASTUO_SLACK_WEBHOOK", "")
TELEGRAM_BOT_TOKEN = os.environ.get("CASTUO_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("CASTUO_TELEGRAM_CHAT_ID", "")


def send_slack(alert: Dict[str, Any], message: str) -> bool:
    """Envía notificación a Slack (webhook)."""
    if not SLACK_WEBHOOK:
        logger.warning("CASTUO_SLACK_WEBHOOK no configurado")
        return False
    payload = {
        "text": f"ALERTA {alert.get('severity', 'medium').upper()}",
        "attachments": [{
            "color": "danger" if alert.get("severity") in ("high", "critical") else "warning",
            "title": alert.get("name", "Alerta"),
            "text": message,
            "fields": [
                {"title": "Valor actual", "value": str(alert.get("current_value", "")), "short": True},
                {"title": "Umbral", "value": str(alert.get("threshold_value", "")), "short": True},
            ],
        }],
    }
    try:
        r = requests.post(SLACK_WEBHOOK, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning("Slack send failed: %s", e)
        return False


def send_telegram(alert: Dict[str, Any], message: str) -> bool:
    """Envía notificación a Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram no configurado")
        return False
    text = f"ALERTA {alert.get('severity', 'medium').upper()}\n\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return False
