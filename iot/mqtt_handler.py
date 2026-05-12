# -*- coding: utf-8 -*-
"""
Manejador MQTT: suscripción a temas castuo/data/# y castuo/auth/#,
procesado de datos de sensores, registro en GaiaChain y publicación de comandos.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient
from .api_endpoints import _analyze_sensor_data

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    _MQTT_AVAILABLE = True
except ImportError:
    mqtt = None
    _MQTT_AVAILABLE = False


class MQTTHandler:
    """Maneja comunicación MQTT entre dispositivos IoT y el backend CASTUO-SYSTEM."""

    def __init__(
        self,
        gaiachain: Optional[GaiaChainClient] = None,
        broker: str = "localhost",
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.gaiachain = gaiachain or GaiaChainClient()
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self._client = None
        if _MQTT_AVAILABLE and mqtt is not None:
            self._client = mqtt.Client(client_id="castuo-system-backend")
            if username and password:
                self._client.username_pw_set(username, password)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: int) -> None:
        logger.info("Conectado a MQTT broker (rc=%s)", rc)
        client.subscribe("castuo/data/#")
        client.subscribe("castuo/auth/#")

    def _on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        try:
            payload = json.loads(msg.payload.decode())
            topic = getattr(msg, "topic", "")
            if topic.startswith("castuo/data/"):
                self._process_sensor_data(topic, payload)
            elif topic.startswith("castuo/auth/"):
                self._process_auth_request(topic, payload)
        except Exception as e:
            logger.exception("Error procesando mensaje MQTT: %s", e)

    def _process_sensor_data(self, topic: str, data: Dict[str, Any]) -> None:
        parts = topic.split("/")
        tray_id = parts[-1] if len(parts) >= 3 else data.get("tray_id", "unknown")
        session_id = data.get("session_id")
        if not session_id:
            logger.warning("Datos sin session_id en %s", tray_id)
            return
        tx_id = self.gaiachain.log_iot_data({
            "tray_id": tray_id,
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "sensors": data.get("sensors", {}),
            "metadata": data.get("metadata", {}),
            "session_id": session_id,
        })
        logger.info("IoT data registrada en GaiaChain: %s", tx_id)
        commands = _analyze_sensor_data(data.get("sensors", {}), data.get("metadata", {}))
        if commands and self._client:
            cmd_topic = f"castuo/commands/{tray_id}"
            self._client.publish(
                cmd_topic,
                json.dumps({"session_id": session_id, "timestamp": datetime.now().isoformat(), "commands": commands}),
                qos=1,
            )
            logger.info("Comandos publicados en %s", cmd_topic)

    def _process_auth_request(self, topic: str, data: Dict[str, Any]) -> None:
        parts = topic.split("/")
        tray_id = parts[-1] if len(parts) >= 3 else data.get("tray_id", "unknown")
        session_id = hashlib.sha256(f"{tray_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        self.gaiachain.log_iot_auth({
            "tray_id": tray_id,
            "session_id": session_id,
            "device_type": data.get("device_type", "unknown"),
            "location": data.get("location", "unknown"),
            "timestamp": datetime.now().isoformat(),
        })
        if self._client:
            auth_topic = f"castuo/auth/{tray_id}"
            self._client.publish(
                auth_topic,
                json.dumps({"status": "success", "session_id": session_id, "timestamp": datetime.now().isoformat()}),
                qos=1,
            )
        logger.info("Auth IoT: %s -> %s", tray_id, session_id)

    def start(self) -> None:
        """Conecta al broker e inicia el loop."""
        if not _MQTT_AVAILABLE or not self._client:
            logger.warning("paho-mqtt no disponible; MQTT handler no iniciado")
            return
        self._client.connect(self.broker, self.port, 60)
        self._client.loop_start()
        logger.info("MQTT handler iniciado")

    def stop(self) -> None:
        """Detiene el loop y desconecta."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        logger.info("MQTT handler detenido")
