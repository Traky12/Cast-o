#!/usr/bin/env python3
"""End-to-end smoke test: MQTT publish → bridge → FastAPI ingest.

Usage (local Docker stack, iot profile up):
    python scripts/cloud-iot-smoke.py

Exit codes:
    0 – all checks passed (GO)
    1 – at least one check failed (NO-GO)

Environment variables (all optional, defaults target local docker-compose.cloud.yml):
    SMOKE_MQTT_HOST        MQTT broker host        (default: 127.0.0.1)
    SMOKE_MQTT_PORT        MQTT broker port        (default: 1883)
    SMOKE_MQTT_USERNAME    MQTT username           (default: castuo)
    SMOKE_MQTT_PASSWORD    MQTT password           (default: empty)
    SMOKE_TOPIC_PREFIX     topic namespace         (default: castuo/sensors)
    SMOKE_API_URL          FastAPI base URL        (default: http://127.0.0.1:8000)
    SMOKE_BEARER           API bearer token        (default: empty)
    SMOKE_TIMEOUT          seconds to wait         (default: 10)
    SMOKE_TLS              1 = use TLS port 8883   (default: 0)
    SMOKE_TLS_CA           CA cert path for TLS    (default: certs/ca.crt)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import uuid

try:
    import httpx
    import paho.mqtt.client as mqtt
except ImportError:
    print("NO-GO: install paho-mqtt and httpx: pip install paho-mqtt httpx", file=sys.stderr)
    sys.exit(1)

LOG = logging.getLogger("smoke")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


MQTT_HOST = _env("SMOKE_MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(_env("SMOKE_MQTT_PORT", "1883"))
MQTT_USERNAME = _env("SMOKE_MQTT_USERNAME", "castuo")
MQTT_PASSWORD = _env("SMOKE_MQTT_PASSWORD", "")
TOPIC_PREFIX = _env("SMOKE_TOPIC_PREFIX", "castuo/sensors")
API_URL = _env("SMOKE_API_URL", "http://127.0.0.1:8000").rstrip("/")
BEARER = _env("SMOKE_BEARER", "")
TIMEOUT = int(_env("SMOKE_TIMEOUT", "10"))
USE_TLS = _env("SMOKE_TLS", "0") == "1"
CA_CERT = _env("SMOKE_TLS_CA", "certs/ca.crt")

SENSOR_ID = f"smoke-{uuid.uuid4().hex[:8]}"
TOPIC = f"{TOPIC_PREFIX}/greenhouse/smoke"
PAYLOAD = {
    "sensor_id": SENSOR_ID,
    "temperature_c": 22.5,
    "humidity_pct": 65.0,
    "co2_ppm": 420,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "source": "smoke-test",
}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

_results: dict[str, str] = {}    # check_name → "PASS" | "FAIL: reason"


def _pass(name: str) -> None:
    _results[name] = "PASS"
    LOG.info("✅  %s", name)


def _fail(name: str, reason: str) -> None:
    _results[name] = f"FAIL: {reason}"
    LOG.error("❌  %s — %s", name, reason)


# ---------------------------------------------------------------------------
# 1. API health
# ---------------------------------------------------------------------------

def check_api_health() -> bool:
    name = "api_health"
    try:
        headers = {}
        if BEARER:
            headers["Authorization"] = f"Bearer {BEARER}"
        with httpx.Client(timeout=TIMEOUT) as client:
            r = client.get(f"{API_URL}/health", headers=headers)
        if r.status_code == 200:
            _pass(name)
            return True
        _fail(name, f"HTTP {r.status_code}")
        return False
    except Exception as exc:  # noqa: BLE001
        _fail(name, str(exc))
        return False


# ---------------------------------------------------------------------------
# 2. MQTT broker reachable + publish
# ---------------------------------------------------------------------------

def check_mqtt_publish() -> bool:
    name = "mqtt_publish"
    connected = threading.Event()
    published = threading.Event()

    def on_connect(client: mqtt.Client, _ud: object, _flags: object, rc: int, *_: object) -> None:
        if rc == 0:
            connected.set()
        else:
            _fail(name, f"connect refused rc={rc}")

    def on_publish(_client: mqtt.Client, _ud: object, mid: int, *_: object) -> None:  # noqa: ARG001
        published.set()

    client = mqtt.Client(
        client_id=f"smoke-pub-{SENSOR_ID}",
        protocol=mqtt.MQTTv5,
        transport="tcp",
    )
    client.on_connect = on_connect
    client.on_publish = on_publish

    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD or None)

    if USE_TLS:
        import ssl

        ca = CA_CERT if os.path.exists(CA_CERT) else None
        try:
            client.tls_set(ca_certs=ca, cert_reqs=ssl.CERT_NONE if ca is None else ssl.CERT_REQUIRED)
        except Exception as exc:  # noqa: BLE001
            _fail(name, f"TLS setup failed: {exc}")
            return False

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    except Exception as exc:  # noqa: BLE001
        _fail(name, f"connect failed: {exc}")
        return False

    client.loop_start()
    if not connected.wait(timeout=TIMEOUT):
        _fail(name, f"timeout connecting to {MQTT_HOST}:{MQTT_PORT}")
        client.loop_stop()
        return False

    result = client.publish(TOPIC, json.dumps(PAYLOAD), qos=1)
    result.wait_for_publish(timeout=TIMEOUT)
    if not published.wait(timeout=TIMEOUT):
        _fail(name, "publish confirm timeout")
        client.loop_stop()
        return False

    client.loop_stop()
    client.disconnect()
    _pass(name)
    return True


# ---------------------------------------------------------------------------
# 3. E2E ingestion lookup (expects bridge to have forwarded published payload)
# ---------------------------------------------------------------------------

def check_telemetry_ingest_lookup() -> bool:
    name = "telemetry_ingest_lookup"
    url = f"{API_URL}/api/v1/iot/telemetry/{SENSOR_ID}/latest"
    headers: dict[str, str] = {}
    if BEARER:
        headers["Authorization"] = f"Bearer {BEARER}"

    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=TIMEOUT) as client:
                r = client.get(url, headers=headers)
            if r.status_code == 404:
                time.sleep(1)
                continue
            if r.status_code != 200:
                _fail(name, f"HTTP {r.status_code}: {r.text[:120]}")
                return False

            data = r.json()
            if data.get("sensor_id") != SENSOR_ID:
                _fail(name, "sensor_id mismatch in latest ingestion")
                return False

            traces_status = data.get("traces", {}).get("status", "")
            if traces_status not in {"queued", "disabled"}:
                _fail(name, f"unexpected traces status: {traces_status}")
                return False

            _pass(name)
            return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
            continue

    _fail(name, f"timeout waiting ingestion for sensor {SENSOR_ID}")
    return False


# ---------------------------------------------------------------------------
# 4. Wireless Logic upstream broker (optional, only when SMOKE_WL_HOST set)
# ---------------------------------------------------------------------------

def check_wireless_logic_upstream() -> bool | None:
    """Returns None if the check is skipped (no WL host configured)."""
    host = _env("SMOKE_WL_HOST")
    if not host:
        LOG.info("ℹ️   wireless_logic_upstream — skipped (SMOKE_WL_HOST not set)")
        return None

    name = "wireless_logic_upstream"
    token = _env("SMOKE_WL_TOKEN")
    port = int(_env("SMOKE_WL_PORT", "8883"))

    connected = threading.Event()

    def on_connect(_c: mqtt.Client, _ud: object, _f: object, rc: int, *_: object) -> None:
        if rc == 0:
            connected.set()

    client = mqtt.Client(client_id=f"smoke-wl-{SENSOR_ID}", protocol=mqtt.MQTTv5)
    client.on_connect = on_connect
    if token:
        client.username_pw_set("device", token)
    client.tls_set()

    try:
        client.connect(host, port, keepalive=20)
    except Exception as exc:  # noqa: BLE001
        _fail(name, f"connect failed: {exc}")
        return False

    client.loop_start()
    ok = connected.wait(timeout=TIMEOUT)
    client.loop_stop()
    client.disconnect()

    if ok:
        _pass(name)
        return True
    _fail(name, f"timeout connecting to WL broker {host}:{port}")
    return False


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _print_summary() -> int:
    print()
    print("=" * 50)
    print("SMOKE TEST SUMMARY — CASTÚO-SYSTEM IoT v4.2")
    print("=" * 50)
    all_pass = True
    for check, status in _results.items():
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon}  {check}: {status}")
        if not status.startswith("PASS"):
            all_pass = False
    print()
    if all_pass:
        print("GO — all checks passed")
    else:
        print("NO-GO — one or more checks failed")
    return 0 if all_pass else 1


def main() -> int:
    LOG.info("Starting CASTÚO IoT smoke test [sensor_id=%s]", SENSOR_ID)
    LOG.info("API: %s   MQTT: %s:%s   TLS: %s", API_URL, MQTT_HOST, MQTT_PORT, USE_TLS)

    check_api_health()
    check_mqtt_publish()
    check_telemetry_ingest_lookup()
    check_wireless_logic_upstream()   # skipped if SMOKE_WL_HOST unset

    return _print_summary()


if __name__ == "__main__":
    sys.exit(main())
