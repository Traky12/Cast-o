#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plantilla de reenvio MQTT (origen CASTÚO / broker local -> destino tipo Arsys IoT).
Configuracion exclusivamente por variables de entorno; revisar DPA con el proveedor antes de produccion.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("castuo.arsys_bridge")


def _load_optional_paho():
    try:
        import paho.mqtt.client as mqtt

        return mqtt
    except ImportError:
        return None


def _mqtt_client(mqtt_mod: Any, client_id: str) -> Any:
    try:
        if hasattr(mqtt_mod, "CallbackAPIVersion"):
            return mqtt_mod.Client(
                mqtt_mod.CallbackAPIVersion.VERSION1,
                client_id=client_id,
                protocol=mqtt_mod.MQTTv311,
            )
        return mqtt_mod.Client(client_id=client_id, protocol=mqtt_mod.MQTTv311)
    except Exception:
        return mqtt_mod.Client(client_id=client_id)


def main() -> int:
    mqtt = _load_optional_paho()
    if mqtt is None:
        logger.error("Instalar paho-mqtt")
        return 3

    src_host = os.environ.get("CASTUO_BRIDGE_SRC_HOST", "127.0.0.1").strip()
    src_port = int(os.environ.get("CASTUO_BRIDGE_SRC_PORT", "1883"))
    src_topic = os.environ.get("CASTUO_BRIDGE_SRC_TOPIC", "castuo/sensors/#").strip()

    dst_host = os.environ.get("ARSYS_MQTT_HOST", "").strip()
    dst_port = int(os.environ.get("ARSYS_MQTT_PORT", "8883"))
    dst_topic_prefix = os.environ.get("ARSYS_MQTT_TOPIC_PREFIX", "arsys/castuo/").strip()

    if not dst_host:
        logger.error("Definir ARSYS_MQTT_HOST (y credenciales si aplica)")
        return 2

    dst_user = os.environ.get("ARSYS_MQTT_USER", "").strip() or None
    dst_pass = os.environ.get("ARSYS_MQTT_PASSWORD", "").strip() or None

    dst_client = mqtt.Client(client_id=os.environ.get("ARSYS_MQTT_CLIENT_ID", "castuo_arsys_out"))
    if dst_user and dst_pass:
        dst_client.username_pw_set(dst_user, dst_pass)

    try:
        dst_client.connect(dst_host, dst_port, keepalive=60)
        dst_client.loop_start()
    except Exception as e:
        logger.error("Destino MQTT: %s", e)
        return 4

    def on_message(_c: Any, _u: Any, msg: Any) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            payload = {"raw_b64": msg.payload.hex()[:200]}
        out_topic = f"{dst_topic_prefix.rstrip('/')}/{msg.topic.replace('/', '_')}"
        dst_client.publish(out_topic, json.dumps(payload, ensure_ascii=False), qos=1)

    src_client = _mqtt_client(mqtt, os.environ.get("CASTUO_BRIDGE_CLIENT_ID", "castuo_arsys_in"))
    src_client.on_message = on_message

    try:
        src_client.connect(src_host, src_port, keepalive=60)
        src_client.subscribe(src_topic)
        src_client.loop_start()
        logger.info("Bridge activo %s:%s %s -> %s:%s", src_host, src_port, src_topic, dst_host, dst_port)
        logger.info("Pulsa Ctrl+C para detener")
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Deteniendo")
    finally:
        src_client.loop_stop()
        dst_client.loop_stop()
        try:
            src_client.disconnect()
            dst_client.disconnect()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
