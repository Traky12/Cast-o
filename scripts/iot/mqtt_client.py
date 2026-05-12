#!/usr/bin/env python3
"""
Cliente MQTT de ejemplo (laboratorio). Requiere: pip install paho-mqtt
Certificados TLS: rutas configurables por entorno (producción: CA del broker).
"""
from __future__ import annotations

import json
import os
import ssl
import time
from typing import Any, Dict

try:
    import paho.mqtt.client as mqtt
except ImportError:
    raise SystemExit("Instala paho-mqtt: pip install paho-mqtt") from None


class IoTClient:
    def __init__(
        self,
        client_id: str,
        username: str | None = None,
        password: str | None = None,
        broker_host: str | None = None,
        port: int | None = None,
        ca_path: str | None = None,
    ) -> None:
        self.broker_host = broker_host or os.getenv("CASTUO_MQTT_HOST", "127.0.0.1")
        self.port = int(port or os.getenv("CASTUO_MQTT_PORT", "1883"))
        self.ca_path = ca_path or os.getenv("CASTUO_MQTT_CA", "")
        self.client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
        if username and password:
            self.client.username_pw_set(username, password)
        if self.port == 8883 and self.ca_path:
            self.client.tls_set(
                ca_certs=self.ca_path,
                certfile=None,
                keyfile=None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS_CLIENT,
            )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, int], rc: int) -> None:
        print(f"Conectado (rc={rc})")
        client.subscribe("zones/#")
        client.subscribe("actuators/#")

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        print(f"{msg.topic}: {msg.payload.decode(errors='replace')}")

    def connect(self) -> None:
        self.client.connect(self.broker_host, self.port, keepalive=60)
        self.client.loop_start()

    def publish_sensor(self, zone_id: str, sensor_id: str, data: Dict[str, Any]) -> None:
        topic = f"zones/{zone_id}/sensors/{sensor_id}"
        payload = json.dumps(
            {
                "timestamp": int(time.time()),
                "value": data.get("value"),
                "unit": data.get("unit", "unknown"),
            }
        )
        self.client.publish(topic, payload)
        print(f"Publicado {topic}: {payload}")

    def disconnect(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


if __name__ == "__main__":
    c = IoTClient(
        client_id=os.getenv("CASTUO_MQTT_CLIENT_ID", "lab_sensor_1"),
        username=os.getenv("CASTUO_MQTT_USER") or None,
        password=os.getenv("CASTUO_MQTT_PASS") or None,
    )
    c.connect()
    for i in range(3):
        c.publish_sensor("zone_demo", "temp_1", {"value": 22.0 + 0.1 * i, "unit": "°C"})
        time.sleep(1.0)
    c.disconnect()
