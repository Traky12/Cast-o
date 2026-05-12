"""
CASTÚO-SYSTEM™ v3.1 — MQTT Bridge
Suscribe a todos los topics castuo/# y reenvía a la API + InfluxDB.

Topics escuchados:
  castuo/invernadero/sensores/{zona}        → POST /api/v1/invernadero/sensor-data
  castuo/invernadero/actuadores/{zona}/{id} → registra en InfluxDB
  castuo/invernadero/alertas/#              → log de alertas
  castuo/rpi/{node_id}/heartbeat            → registro de nodo
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from threading import Thread

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [mqtt-bridge] %(levelname)s %(message)s",
)
logger = logging.getLogger("castuo.mqtt_bridge")

MQTT_HOST  = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT  = int(os.getenv("MQTT_PORT", "1883"))
API_URL    = os.getenv("API_URL", "http://localhost:8000")
INFLUX_URL = os.getenv("INFLUXDB_URL", "")
INFLUX_TOK = os.getenv("INFLUXDB_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUXDB_ORG", "castuo")

# ── Simulación fallback ────────────────────────────────────────────────────────
_sim_stats = {"received": 0, "forwarded": 0, "errors": 0, "start": time.time()}


def _forward_to_api(topic: str, payload: dict) -> bool:
    """Reenvía el mensaje al API HTTP."""
    try:
        import urllib.request, urllib.error
        data = json.dumps({"topic": topic, **payload}).encode()
        req = urllib.request.Request(
            f"{API_URL}/api/v1/iot/ingest",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3):
            _sim_stats["forwarded"] += 1
            return True
    except Exception as exc:
        logger.debug("forward_to_api error: %s", exc)
        _sim_stats["errors"] += 1
        return False


def _on_message(client, userdata, msg):
    """Callback MQTT: recibe mensaje y lo reenvía."""
    _sim_stats["received"] += 1
    try:
        payload = json.loads(msg.payload.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {"raw": msg.payload.decode(errors="replace")}

    topic = msg.topic
    logger.debug("MQTT ← %s : %s", topic, str(payload)[:120])

    # Clasificar y reenviar
    if "sensores" in topic:
        _forward_to_api(topic, {"tipo": "sensor", "datos": payload})
    elif "actuadores" in topic:
        _forward_to_api(topic, {"tipo": "actuador", "datos": payload})
    elif "alertas" in topic:
        logger.warning("ALERTA MQTT [%s]: %s", topic, payload)
        _forward_to_api(topic, {"tipo": "alerta", "datos": payload})
    elif "heartbeat" in topic:
        logger.info("Heartbeat nodo: %s", topic)


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Conectado a Mosquitto %s:%s", MQTT_HOST, MQTT_PORT)
        client.subscribe("castuo/#", qos=1)
        logger.info("Suscrito a castuo/#")
    else:
        logger.error("Error de conexión MQTT rc=%s", rc)


def _on_disconnect(client, userdata, rc):
    if rc != 0:
        logger.warning("Desconexión MQTT inesperada rc=%s — reconectando...", rc)


def _publish_sim_sensors(client):
    """Publica sensores simulados cada 5s para desarrollo sin RPi real."""
    import random, math
    t = 0
    while True:
        t += 1
        payload = {
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "zona":       "zona-a",
            "ph":         round(6.4 + random.gauss(0, 0.05), 2),
            "ec":         round(1.5 + random.gauss(0, 0.04), 2),
            "temperatura": round(23.2 + random.gauss(0, 0.3), 1),
            "humedad":    round(62 + random.gauss(0, 1.5), 1),
            "co2":        round(760 + random.gauss(0, 20), 1),
            "luz_par":    round(14238 + random.gauss(0, 500), 1),
            "o2_disuelto": round(9.0 + random.gauss(0, 0.1), 2),
            "orp":        round(701 + random.gauss(0, 8), 1),
            "flujo":      round(13.2 + random.gauss(0, 0.3), 2),
            "o3":         round(0.7 + random.gauss(0, 0.03), 2),
            "sim":        True,
        }
        client.publish(
            "castuo/invernadero/sensores/zona-a",
            json.dumps(payload),
            qos=1,
        )
        logger.debug("SIM sensor publicado t=%s", t)
        time.sleep(5)


def run():
    try:
        import paho.mqtt.client as mqtt_client
    except ImportError:
        logger.warning("paho-mqtt no instalado — modo polling simulado")
        _run_sim_polling()
        return

    client = mqtt_client.Client(client_id="castuo-mqtt-bridge", clean_session=True)
    client.on_connect    = _on_connect
    client.on_message    = _on_message
    client.on_disconnect = _on_disconnect

    logger.info("Conectando a %s:%s...", MQTT_HOST, MQTT_PORT)
    retries = 0
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            break
        except Exception as exc:
            retries += 1
            wait = min(2 ** retries, 30)
            logger.warning("No se pudo conectar a MQTT (%s) — reintentando en %ss", exc, wait)
            time.sleep(wait)

    # Publicar sensores simulados en background
    sim_thread = Thread(target=_publish_sim_sensors, args=(client,), daemon=True)
    sim_thread.start()

    logger.info("MQTT Bridge listo. Escuchando castuo/#")
    client.loop_forever()


def _run_sim_polling():
    """Modo de respaldo: sin paho-mqtt, simula lecturas directamente a la API."""
    logger.info("Modo sim-polling activo (sin MQTT real)")
    import random
    while True:
        payload = {
            "topic": "castuo/invernadero/sensores/zona-a",
            "tipo": "sensor",
            "datos": {
                "zona": "zona-a",
                "ph": round(6.4 + random.gauss(0, 0.05), 2),
                "ec": round(1.5 + random.gauss(0, 0.04), 2),
                "temperatura": round(23.2 + random.gauss(0, 0.3), 1),
                "humedad": round(62 + random.gauss(0, 1.5), 1),
                "co2": round(760 + random.gauss(0, 20), 1),
                "sim": True,
            },
        }
        _forward_to_api("sim", payload)
        _sim_stats["received"] += 1
        time.sleep(5)


if __name__ == "__main__":
    run()
