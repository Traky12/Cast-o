"""MQTT bridge: Mosquitto IoT → CASTÚO FastAPI.

Two reception modes:
  LOCAL   – subscribes to sensors on the local iot-bridge Mosquitto (1883).
  UPSTREAM – also subscribes to an upstream broker (e.g. Wireless Logic Conexa)
             when WIRELESS_LOGIC_MQTT_HOST is set with its token file.

Env vars:
    MQTT_BROKER               local Mosquitto host  (default: iot-bridge)
    MQTT_PORT                 local MQTT port       (default: 1883)
    MQTT_USERNAME             local MQTT username   (optional)
    MQTT_PASSWORD_FILE        file with local MQTT password
    MQTT_TOPIC_PREFIX         base topic            (default: castuo/sensors)
    CASTUO_API_URL            FastAPI base URL      (default: http://api:8000)
    CASTUO_IOT_BEARER_FILE    file with telemetry bearer token
    WIRELESS_LOGIC_MQTT_HOST  upstream WL broker    (optional)
    WIRELESS_LOGIC_MQTT_PORT  upstream WL port      (default: 8883)
    WIRELESS_LOGIC_API_TOKEN_FILE  file with WL API/MQTT token
"""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any

import httpx
import paho.mqtt.client as mqtt

LOG = logging.getLogger("mqtt_bridge")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_file_secret(env_key: str, default: str = "") -> str:
    path = os.getenv(env_key)
    if path and Path(path).exists():
        return Path(path).read_text().strip()
    return default


def _api_url() -> str:
    return os.getenv("CASTUO_API_URL", "http://api:8000")


def _telemetry_bearer() -> str:
    return _read_file_secret("CASTUO_IOT_BEARER_FILE")


# ---------------------------------------------------------------------------
# Forwarding
# ---------------------------------------------------------------------------

def _forward_to_api(payload: dict[str, Any]) -> None:
    """POST a sensor reading to the FastAPI telemetry endpoint."""
    url = f"{_api_url()}/api/v1/iot/telemetry"
    bearer = _telemetry_bearer()
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code < 400:
                LOG.debug("forwarded to API: %s", resp.status_code)
            else:
                LOG.warning("API returned %s: %.200s", resp.status_code, resp.text)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("forward failed: %s", exc)


# ---------------------------------------------------------------------------
# MQTT callbacks
# ---------------------------------------------------------------------------

def _on_message(_client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:  # noqa: BLE001
        LOG.warning("non-JSON message on %s; skipped", msg.topic)
        return
    payload.setdefault("source_topic", msg.topic)
    _forward_to_api(payload)


def _on_connect(client: mqtt.Client, _userdata: Any, _flags: Any, rc: int, *_: Any) -> None:
    if rc == 0:
        topic = os.getenv("MQTT_TOPIC_PREFIX", "castuo/sensors") + "/#"
        client.subscribe(topic, qos=1)
        LOG.info("connected and subscribed to %s", topic)
    else:
        LOG.error("connection refused rc=%s", rc)


def _build_client(client_id: str) -> mqtt.Client:
    client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv5, transport="tcp")
    client.on_message = _on_message
    client.on_connect = _on_connect
    return client


# ---------------------------------------------------------------------------
# Connection factories
# ---------------------------------------------------------------------------

def _connect_local_broker() -> mqtt.Client:
    """Connect to the local Mosquitto iot-bridge."""
    host = os.getenv("MQTT_BROKER", "iot-bridge")
    port = int(os.getenv("MQTT_PORT", "1883"))
    username = os.getenv("MQTT_USERNAME", "")
    password = _read_file_secret("MQTT_PASSWORD_FILE")

    client = _build_client("castuo-bridge-local")
    if username:
        client.username_pw_set(username, password or None)

    LOG.info("connecting to local broker %s:%s", host, port)
    client.connect(host, port, keepalive=60, clean_start=True)
    return client


def _connect_wireless_logic_broker() -> mqtt.Client | None:
    """Optionally connect to a Wireless Logic Conexa upstream broker.

    Returns None when WIRELESS_LOGIC_MQTT_HOST is not set or the token file
    is missing — the bridge continues with local-only mode without error.
    """
    host = os.getenv("WIRELESS_LOGIC_MQTT_HOST", "")
    if not host:
        return None

    token = _read_file_secret("WIRELESS_LOGIC_API_TOKEN_FILE")
    if not token:
        LOG.warning(
            "WIRELESS_LOGIC_MQTT_HOST set but WIRELESS_LOGIC_API_TOKEN_FILE missing; "
            "upstream bridge disabled"
        )
        return None

    port = int(os.getenv("WIRELESS_LOGIC_MQTT_PORT", "8883"))
    client = _build_client("castuo-bridge-wl")
    client.username_pw_set("device", token)
    client.tls_set()  # relies on system CA store; WL Conexa uses valid EU certs

    LOG.info("connecting to Wireless Logic Conexa %s:%s", host, port)
    try:
        client.connect(host, port, keepalive=60, clean_start=True)
        return client
    except Exception as exc:  # noqa: BLE001
        LOG.warning("could not reach Wireless Logic broker: %s; local-only mode", exc)
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    stop = threading.Event()

    def _handle_signal(sig: int, _frame: Any) -> None:  # noqa: ARG001
        LOG.info("signal %s — shutting down", sig)
        stop.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    local = _connect_local_broker()
    wl = _connect_wireless_logic_broker()

    local.loop_start()
    if wl:
        wl.loop_start()

    LOG.info(
        "MQTT bridge running [local-only=%s wireless-logic=%s]",
        True,
        wl is not None,
    )
    stop.wait()

    local.loop_stop()
    local.disconnect()
    if wl:
        wl.loop_stop()
        wl.disconnect()

    LOG.info("MQTT bridge stopped")


if __name__ == "__main__":
    main()
