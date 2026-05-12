from __future__ import annotations

import os
from typing import Optional

import httpx

from ..models import SabiondaDecision, SabiondaRequest


class TelegramNotifier:
    """
    Notificador mínimo para enviar resúmenes de decisión a un chat de Telegram.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> None:
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID_B001")

    def notify(self, request: SabiondaRequest, decision: SabiondaDecision) -> None:
        if not self.bot_token or not self.chat_id:
            return

        text = (
            f"Castúo Sabionda · {request.bandeja} ({request.crop})\n"
            f"pH={request.ph} | EC={request.ec} | Temp={request.temp}°C\n"
            f"Decisión: {decision.decision} · O3={decision.o3_target}\n"
            f"{decision.log_message}"
        )
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {"chat_id": self.chat_id, "text": text}

        try:
            with httpx.Client(timeout=5.0) as client:
                client.post(url, data=data)
        except Exception:
            return

