#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any

import httpx
import paho.mqtt.client as mqtt


def _read_secret_from_file(path: str | None) -> str:
    if not path:
        return ""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


@dataclass
class BridgeConfig:
    mqtt_broker: str
    mqtt_port: int
    mqtt_topic: str
    mqtt_user: str
    mqtt_pass: str
    telemetry_url: str
    traces_url: str
    token: str
    timeout_s: int


def load_config() -> BridgeConfig:
    token = os.getenv("WIRELESS_LOGIC_API_TOKEN", "")
    if not token:
        token = _read_secret_from_file(os.getenv("WIRELESS_LOGIC_API_TOKEN_FILE"))
    if not token:
        token = _read_secret_from_file(os.getenv("CASTUO_IOT_BEARER_FILE"))

    return BridgeConfig(
        mqtt_broker=os.getenv("MQTT_BROKER", "iot-bridge"),
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_topic=os.getenv("MQTT_TOPIC", "castuo/sensors/#"),
        mqtt_user=os.getenv("WIRELESS_LOGIC_MQTT_USER", ""),
        mqtt_pass=os.getenv("WIRELESS_LOGIC_MQTT_PASS", ""),
        telemetry_url=os.getenv("IOT_TELEMETRY_URL", ""),
        traces_url=os.getenv("TRACES_HYPERLEDGER_URL", ""),
        token=token,
        timeout_s=int(os.getenv("CASTUO_IOT_TIMEOUT_S", "20")),
    )


class MqttBridge:
    def __init__(self, cfg: BridgeConfig) -> None:
        self.cfg = cfg
        self.keep_running = True
        self.http = httpx.Client(timeout=cfg.timeout_s)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if cfg.mqtt_user and cfg.mqtt_pass:
            self.client.username_pw_set(cfg.mqtt_user, cfg.mqtt_pass)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any = None) -> None:
        if int(reason_code) != 0:
            print(f"MQTT connect failed: {reason_code}", flush=True)
            return
        print(f"MQTT connected -> topic {self.cfg.mqtt_topic}", flush=True)
        client.subscribe(self.cfg.mqtt_topic, qos=1)

    def on_disconnect(self, _client: mqtt.Client, _userdata: Any, _flags: Any, reason_code: Any, _properties: Any = None) -> None:
        print(f"MQTT disconnected: {reason_code}", flush=True)

    def _post_json(self, url: str, payload: dict[str, Any]) -> None:
        if not url:
            return
        headers = {"Content-Type": "application/json"}
        if self.cfg.token:
            headers["Authorization"] = f"Bearer {self.cfg.token}"
        try:
            resp = self.http.post(url, json=payload, headers=headers)
            print(f"POST {url} -> {resp.status_code}", flush=True)
        except httpx.HTTPError as exc:
            print(f"HTTP error posting to {url}: {exc}", flush=True)

    def on_message(self, _client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
        raw_payload = msg.payload.decode("utf-8", errors="replace")
        payload: dict[str, Any]
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            payload = {"raw": raw_payload}

        envelope = {
            "topic": msg.topic,
            "qos": int(msg.qos),
            "timestamp": int(time.time()),
            "data": payload,
        }
        self._post_json(self.cfg.telemetry_url, envelope)
        self._post_json(self.cfg.traces_url, {"event": "iot_ingest", "payload": envelope})

    def start(self) -> int:
        if not self.cfg.telemetry_url:
            print("WARN: IOT_TELEMETRY_URL not set; bridge will run without forwarding.", flush=True)
        try:
            self.client.connect(self.cfg.mqtt_broker, self.cfg.mqtt_port, keepalive=60)
            self.client.loop_start()
            while self.keep_running:
                time.sleep(1)
            return 0
        except Exception as exc:  # pragma: no cover
            print(f"Bridge fatal error: {exc}", flush=True)
            return 1
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            self.http.close()

    def stop(self) -> None:
        self.keep_running = False


def main() -> int:
    bridge = MqttBridge(load_config())

    def _handle_signal(_signum: int, _frame: Any) -> None:
        bridge.stop()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    return bridge.start()


if __name__ == "__main__":
    sys.exit(main())
