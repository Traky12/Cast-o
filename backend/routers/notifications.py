# -*- coding: utf-8 -*-
"""Notificaciones Slack/Telegram (webhooks)."""
import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/notifications", tags=["notifications"])


class SlackBody(BaseModel):
    channel: str = "#alertas-drones"
    message: str


class AlertBody(BaseModel):
    alert_id: Optional[int] = None
    name: str = ""
    message: str
    severity: str = "medium"
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    material_name: str = ""


@router.post("/slack")
async def slack(body: SlackBody):
    """Envía mensaje a Slack (webhook URL)."""
    url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not url:
        return {"status": "skipped", "reason": "SLACK_WEBHOOK_URL not set"}
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json={"text": body.message, "channel": body.channel},
                timeout=5.0,
            )
        return {"status": "sent"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/alert")
async def alert(body: AlertBody):
    """Envía alerta predictiva a Slack y/o Telegram (webhooks en env)."""
    alert_dict = {
        "name": body.name,
        "message": body.message,
        "severity": body.severity,
        "current_value": body.current_value,
        "threshold_value": body.threshold_value,
    }
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "") or os.environ.get("CASTUO_SLACK_WEBHOOK", "")
    telegram_token = os.environ.get("CASTUO_TELEGRAM_BOT_TOKEN", "")
    telegram_chat = os.environ.get("CASTUO_TELEGRAM_CHAT_ID", "")
    sent = []
    if slack_url:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    slack_url,
                    json={
                        "text": f"ALERTA {body.severity.upper()}: {body.name}",
                        "attachments": [{"text": body.message, "color": "danger" if body.severity in ("high", "critical") else "warning"}],
                    },
                    timeout=5.0,
                )
            sent.append("slack")
        except Exception:
            pass
    if telegram_token and telegram_chat:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    data={"chat_id": telegram_chat, "text": f"ALERTA {body.severity.upper()}\n\n{body.message}"},
                    timeout=5.0,
                )
            sent.append("telegram")
        except Exception:
            pass
    return {"status": "sent" if sent else "skipped", "channels": sent}
