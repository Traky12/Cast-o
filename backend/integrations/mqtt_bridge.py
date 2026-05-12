"""
CASTÚO-SYSTEM™ v3.1 — MQTT → GaiaChain Bridge
Escucha topics MQTT de sensores IoT y registra cada mensaje en GaiaChain.

Uso:
    python -m backend.integrations.mqtt_bridge

Variables de entorno:
    MQTT_BROKER_HOST    Broker MQTT (default: localhost)
    MQTT_BROKER_PORT    Puerto (default: 1883)
    MQTT_USERNAME       Usuario MQTT (opcional)
    MQTT_PASSWORD_FILE  Ruta a fichero con password (Opción A)
    MQTT_PASSWORD       Password plana (Opción B)
    MQTT_TOPICS         Comma-separated topics a suscribir
                        (default: castuo/+/telemetry,castuo/+/sensor)
    MQTT_TLS            "1" para habilitar TLS (default: 0)
    GAIACHAIN_RPC_URL   Nodo RPC GaiaChain
    GAIACHAIN_PRIVATE_KEY_FILE / GAIACHAIN_PRIVATE_KEY  Clave de firma

Dependencias opcionales:
    pip install paho-mqtt>=2.0.0
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("castuo.mqtt_bridge")


# ── Secrets helper ────────────────────────────────────────────────────────────

def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


# ── Configuración ─────────────────────────────────────────────────────────────

MQTT_HOST    = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_PORT    = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USER    = os.getenv("MQTT_USERNAME", "")
MQTT_PASS    = _read_secret("MQTT_PASSWORD")
MQTT_TLS     = os.getenv("MQTT_TLS", "0") == "1"
MQTT_TOPICS  = [
    t.strip()
    for t in os.getenv("MQTT_TOPICS", "castuo/+/telemetry,castuo/+/sensor").split(",")
    if t.strip()
]
# QoS 1 garantiza al-menos-una-entrega sin requerir broker persistente
MQTT_QOS     = int(os.getenv("MQTT_QOS", "1"))
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "castuo-bridge-001")

# Reintentos en registro blockchain
BLOCKCHAIN_RETRIES = int(os.getenv("BLOCKCHAIN_RETRIES", "3"))
BLOCKCHAIN_RETRY_DELAY = float(os.getenv("BLOCKCHAIN_RETRY_DELAY", "2.0"))


# ── Blockchain helper ─────────────────────────────────────────────────────────

def _registrar(topic: str, payload: dict) -> str:
    """
    Registra el payload IoT en GaiaChain.
    Devuelve tx_hash (0x...) o sim-<sha256> como fallback.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    from castuo_graph.skills import registrar_en_blockchain

    lote_id = f"IOT:{topic.replace('/', ':')}"
    metadata = {
        "topic": topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    last_exc: Exception | None = None
    for attempt in range(1, BLOCKCHAIN_RETRIES + 1):
        try:
            tx_hash = registrar_en_blockchain(lote_id, metadata)
            return tx_hash
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "[mqtt_bridge] Intento %d/%d fallido para %s: %s",
                attempt, BLOCKCHAIN_RETRIES, topic, exc,
            )
            if attempt < BLOCKCHAIN_RETRIES:
                time.sleep(BLOCKCHAIN_RETRY_DELAY * attempt)

    logger.error("[mqtt_bridge] Fallback sim para %s tras %d intentos", topic, BLOCKCHAIN_RETRIES)
    import hashlib, json as _json
    sim_data = json.dumps(metadata, sort_keys=True).encode()
    return f"sim-{hashlib.sha256(sim_data).hexdigest()[:16]}"


# ── Callbacks MQTT ────────────────────────────────────────────────────────────

def on_connect(client: Any, userdata: Any, flags: Any, rc: int, properties: Any = None) -> None:
    if rc == 0:
        logger.info("[mqtt_bridge] Conectado al broker %s:%d", MQTT_HOST, MQTT_PORT)
        for topic in MQTT_TOPICS:
            client.subscribe(topic, qos=MQTT_QOS)
            logger.info("[mqtt_bridge] Suscrito a: %s (QoS %d)", topic, MQTT_QOS)
    else:
        logger.error("[mqtt_bridge] Error de conexión rc=%d", rc)


def on_disconnect(client: Any, userdata: Any, rc: int, properties: Any = None) -> None:
    if rc != 0:
        logger.warning("[mqtt_bridge] Desconexión inesperada rc=%d — reconectando...", rc)


def on_message(client: Any, userdata: Any, msg: Any) -> None:
    topic = msg.topic
    try:
        payload_str = msg.payload.decode("utf-8")
        payload: dict = json.loads(payload_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("[mqtt_bridge] Payload no-JSON en %s: %s", topic, exc)
        payload = {"raw": msg.payload.hex(), "encoding_error": str(exc)}

    logger.info("[mqtt_bridge] Mensaje recibido en %s: %s", topic, str(payload)[:120])

    tx_hash = _registrar(topic, payload)

    if tx_hash.startswith("0x"):
        logger.info("[mqtt_bridge] ✅ GaiaChain tx=%s topic=%s", tx_hash[:20], topic)
    else:
        logger.info("[mqtt_bridge] 📋 Simulado tx=%s topic=%s", tx_hash, topic)


# ── Punto de entrada ──────────────────────────────────────────────────────────

def build_client() -> Any:
    """Construye y configura el cliente MQTT. Requiere paho-mqtt>=2.0."""
    try:
        import paho.mqtt.client as mqtt  # type: ignore
    except ImportError:
        raise RuntimeError(
            "paho-mqtt no instalado. Ejecutar: pip install 'paho-mqtt>=2.0.0'"
        )

    client = mqtt.Client(
        client_id=MQTT_CLIENT_ID,
        protocol=mqtt.MQTTv5,
    )
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS or None)

    if MQTT_TLS:
        import ssl
        client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        logger.info("[mqtt_bridge] TLS habilitado")

    return client


def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger.info(
        "[mqtt_bridge] Iniciando CASTÚO MQTT Bridge — broker=%s:%d topics=%s",
        MQTT_HOST, MQTT_PORT, MQTT_TOPICS,
    )
    client = build_client()

    retry_delay = 5
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except ConnectionRefusedError:
            logger.error(
                "[mqtt_bridge] Broker %s:%d rechazó conexión — reintento en %ds",
                MQTT_HOST, MQTT_PORT, retry_delay,
            )
        except Exception as exc:
            logger.error("[mqtt_bridge] Error inesperado: %s — reintento en %ds", exc, retry_delay)
        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)


if __name__ == "__main__":
    run()
