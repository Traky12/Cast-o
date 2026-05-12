#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publica una carga JSON hacia un broker MQTT (p. ej. Sateliot / intermedio).
Secretos solo por entorno; falla en seco si faltan datos minimos.
Actualizar DPIA si el payload puede contener datos personales.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("castuo.sateliot_bridge")


def _payload_from_env_or_stdin() -> Dict[str, Any]:
    raw = os.environ.get("CASTUO_SENSOR_JSON", "").strip()
    if raw:
        return json.loads(raw)
    data = sys.stdin.read().strip()
    if not data:
        raise ValueError("CASTUO_SENSOR_JSON vacio y stdin vacio")
    return json.loads(data)


def main() -> int:
    host = os.environ.get("SATELIOT_MQTT_HOST", "").strip()
    port = int(os.environ.get("SATELIOT_MQTT_PORT", "8883"))
    topic = os.environ.get("SATELIOT_MQTT_TOPIC", "").strip()
    user = os.environ.get("SATELIOT_MQTT_USER", "").strip() or None
    password = os.environ.get("SATELIOT_MQTT_PASSWORD", "").strip() or None
    client_id = os.environ.get("SATELIOT_MQTT_CLIENT_ID", "castuo_sateliot_bridge").strip()

    if not host or not topic:
        logger.error("Definir SATELIOT_MQTT_HOST y SATELIOT_MQTT_TOPIC")
        return 2

    try:
        payload = _payload_from_env_or_stdin()
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Payload invalido: %s", e)
        return 2

    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        logger.error("Instalar paho-mqtt (p. ej. pip install paho-mqtt>=2.0.0)")
        return 3

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def _on_connect(client: Any, userdata: Any, flags: Any, rc: Any, properties: Any = None) -> None:
        try:
            code = int(rc) if isinstance(rc, int) else int(getattr(rc, "value", rc))
        except (TypeError, ValueError):
            code = -1
        if code == 0:
            logger.info("MQTT conectado")
        else:
            logger.error("MQTT connect rc=%s", code)

    try:
        if hasattr(mqtt, "CallbackAPIVersion"):
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1,
                client_id=client_id,
                protocol=mqtt.MQTTv311,
            )
        else:
            client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    except Exception:
        client = mqtt.Client(client_id=client_id)

    if user and password:
        client.username_pw_set(user, password)

    client.on_connect = _on_connect

    try:
        client.connect(host, port, keepalive=60)
        client.loop_start()
        inf = client.publish(topic, body, qos=1)
        inf.wait_for_publish(timeout=15)
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        logger.error("MQTT error: %s", e)
        return 4

    logger.info("Publicado en %s (bytes=%s)", topic, len(body))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
