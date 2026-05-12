"""Utilidades MQTT para actuadores edge (Raspberry Pi); GPIO opcional si no hay hardware."""
from __future__ import annotations

import json
import os
import ssl
import time
from typing import Any, Callable, Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None  # type: ignore[assignment]


def build_client(
    client_id: str,
    username: Optional[str],
    password: Optional[str],
    ca_path: Optional[str],
) -> "mqtt.Client":
    if mqtt is None:
        raise SystemExit("Instala paho-mqtt: pip install paho-mqtt")
    c = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    if username and password:
        c.username_pw_set(username, password)
    port = int(os.getenv("CASTUO_MQTT_PORT", "1883"))
    if port == 8883 and ca_path:
        c.tls_set(
            ca_certs=ca_path,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
    return c


def parse_zone_actuator_topic(topic: str) -> Optional[tuple[str, str]]:
    parts = topic.split("/")
    if len(parts) >= 4 and parts[0] == "zones" and parts[2] == "actuators":
        return parts[1], parts[3]
    return None


def status_topic(zone_id: str, actuator_id: str) -> str:
    return f"zones/{zone_id}/actuators/{actuator_id}/status"


def publish_status(client: Any, zone_id: str, actuator_id: str, payload: dict) -> None:
    client.publish(status_topic(zone_id, actuator_id), json.dumps(payload), qos=1)


def run_actuator_loop(
    actuator_id: str,
    on_high: Callable[[bool], None],
    on_cleanup: Callable[[], None],
) -> None:
    host = os.getenv("CASTUO_MQTT_HOST", "127.0.0.1")
    port = int(os.getenv("CASTUO_MQTT_PORT", "1883"))
    user = os.getenv("CASTUO_MQTT_USER")
    pwd = os.getenv("CASTUO_MQTT_PASS")
    ca = os.getenv("CASTUO_MQTT_CA") or None

    client = build_client(f"act_{actuator_id}", user, pwd, ca)

    def on_connect(c: Any, _u: Any, _f: Any, rc: int) -> None:
        print(f"MQTT conectado rc={rc}")
        c.subscribe(f"zones/+/actuators/{actuator_id}")

    def on_message(c: Any, _u: Any, msg: Any) -> None:
        try:
            parsed = parse_zone_actuator_topic(msg.topic)
            if not parsed:
                return
            zone_id, aid = parsed
            if aid != actuator_id:
                return
            payload = json.loads(msg.payload.decode())
            state = payload.get("state")
            if state is None:
                return
            duration = int(payload.get("duration") or 0)
            on_high(bool(state))
            publish_status(
                c,
                zone_id,
                actuator_id,
                {
                    "status": "active" if state else "inactive",
                    "timestamp": int(time.time()),
                    "duration": duration,
                },
            )
            if duration > 0 and state:
                time.sleep(duration)
                on_high(False)
                publish_status(
                    c,
                    zone_id,
                    actuator_id,
                    {
                        "status": "inactive",
                        "timestamp": int(time.time()),
                        "message": f"auto_off_after_{duration}s",
                    },
                )
        except Exception as e:  # noqa: BLE001
            print(f"Error mensaje: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, 60)
    client.loop_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        on_cleanup()
