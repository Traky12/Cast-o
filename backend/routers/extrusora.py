# -*- coding: utf-8 -*-
"""Comandos a la extrusora de bio-compuestos (Serial/Arduino vía MQTT bridge)."""
import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/extrusora", tags=["extrusora"])


class ExtrusoraCommandBody(BaseModel):
    command: str  # SET_TEMP 200, START_EXTRUSION, STOP_EXTRUSION
    material_type: Optional[str] = None
    kg: Optional[float] = None


def _publish_mqtt(topic: str, payload: str) -> bool:
    try:
        import paho.mqtt.publish as publish
        host = os.environ.get("MQTT_HOST", "localhost")
        port = int(os.environ.get("MQTT_PORT", "1883"))
        publish.single(topic, payload, hostname=host, port=port, keepalive=60)
        return True
    except Exception:
        return False


@router.post("/command")
async def extrusora_command(body: ExtrusoraCommandBody):
    """Envía comando a la extrusora (bridge Serial↔MQTT en Raspberry Pi suscrito a castu/extrusora/command)."""
    payload = body.command
    if body.command == "START_EXTRUSION" and body.material_type and body.kg is not None:
        # Opcional: SET_TEMP según tipo de material (ej. cáñamo ~200°C)
        payload = "START_EXTRUSION"
    ok = _publish_mqtt("castu/extrusora/command", payload)
    return {"status": "ok" if ok else "mqtt_unavailable", "command": body.command}
