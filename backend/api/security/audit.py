# backend/api/security/audit.py
"""Registro de auditoría (GDPR Art. 30, Ley 3/2023, ISO 27001 A.12.4.1). Log local + Wazuh opcional."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False

logger = logging.getLogger(__name__)


def _audit_log_path() -> str:
    p = os.getenv("AUDIT_LOG_PATH")
    if p:
        return p
    base = Path(__file__).resolve().parents[3]
    return str(base / "logs" / "audit.log")


class AuditLogger:
    def __init__(self) -> None:
        self.log_path = _audit_log_path()
        self.wazuh_enabled = os.getenv("WAZUH_ENABLED", "false").strip().lower() == "true"
        self.wazuh_url = (os.getenv("WAZUH_URL", "http://wazuh:1515") or "").rstrip("/")
        self.wazuh_api_key = os.getenv("WAZUH_API_KEY", "")
        try:
            Path(self.log_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning("Could not create audit log dir: %s", e)

    def _user_dict(self, request: Any) -> Dict[str, Any]:
        user = getattr(request.state, "user", None)
        if user is None:
            return {}
        if isinstance(user, dict):
            return user
        if hasattr(user, "model_dump"):
            return user.model_dump()
        return {
            "id": getattr(user, "sub", None) or getattr(user, "username", None),
            "roles": getattr(user, "roles", []),
            "token_id": getattr(user, "token_id", None),
            "compliance": getattr(user, "compliance", {}),
        }

    async def log_event(
        self,
        request: Any,
        event_type: str,
        data: Dict[str, Any],
        compliance: Dict[str, Any],
    ) -> None:
        """Registra evento en fichero y opcionalmente en Wazuh."""
        user = self._user_dict(request)
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "user": {
                "id": user.get("sub") or user.get("id"),
                "roles": user.get("roles", []),
                "ip": getattr(request.client, "host", None) if getattr(request, "client", None) else "unknown",
                "token_id": user.get("token_id"),
            },
            "data": data,
            "compliance": compliance,
            "service": {
                "name": "backend-forestal",
                "version": "1.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            logger.info("Event logged: %s", event_type)
        except Exception as e:
            logger.error("Error writing to audit log: %s", e)

        if self.wazuh_enabled and self.wazuh_api_key and _HAS_HTTPX:
            await self._send_to_wazuh(event)

    async def _send_to_wazuh(self, event: Dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.wazuh_url}/v1/logs",
                    json={
                        "timestamp": event["timestamp"],
                        "message": json.dumps(event, ensure_ascii=False),
                        "rule": {"level": 6, "description": f"Evento de auditoría: {event['event_type']}"},
                        "location": "backend-forestal",
                    },
                    headers={"Authorization": f"Bearer {self.wazuh_api_key}"},
                )
                response.raise_for_status()
        except Exception as e:
            logger.error("Error sending to Wazuh: %s", e)


audit_logger = AuditLogger()
