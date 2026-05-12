# -*- coding: utf-8 -*-
"""Robótica agrícola: comandos MQTT a robots (deshierbe, poda, cosecha)."""
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/robotica", tags=["robotica"])


class RobotCommandBody(BaseModel):
    robot_id: int
    command: str
    params: Dict[str, Any] = {}


def _publish_mqtt(topic: str, payload: dict) -> bool:
    """Publica en MQTT (paho o bridge HTTP si existe)."""
    try:
        import paho.mqtt.publish as publish
        host = os.environ.get("MQTT_HOST", "localhost")
        port = int(os.environ.get("MQTT_PORT", "1883"))
        publish.single(
            topic,
            __import__("json").dumps(payload),
            hostname=host,
            port=port,
            keepalive=60,
        )
        return True
    except Exception:
        return False


@router.post("/command")
async def robot_command(body: RobotCommandBody):
    """Recibe comando de Odoo y lo reenvía por MQTT al robot (Antenas Conquistadoras)."""
    topic = f"castuo/robot/{body.robot_id}/command"
    payload = {"action": body.command, "params": body.params}
    ok = _publish_mqtt(topic, payload)
    return {"status": "ok" if ok else "mqtt_unavailable", "topic": topic}
