"""
CASTÚO-SYSTEM™ v3.1 — Cliente Kafka
Mensajería asíncrona para eventos entre componentes: Claude, GitHub, Mistral,
sistema agrovoltaico, y GaiaChain.

Topics predefinidos:
    code_updates      Push/PR de GitHub → workers de análisis
    ai_events         Llamadas a Claude/Mistral → trazabilidad
    sensor_alerts     Alertas del invernadero → workers de actuación
    blockchain_events Transacciones GaiaChain → auditoría
    model_updates     Actualizaciones de modelo ML → Model Registry

Variables de entorno:
    KAFKA_BOOTSTRAP_SERVERS   Brokers Kafka (default: localhost:9092)
    KAFKA_SECURITY_PROTOCOL   PLAINTEXT | SSL | SASL_SSL (default: PLAINTEXT)
    KAFKA_SASL_USERNAME       Usuario SASL (opcional)
    KAFKA_SASL_PASSWORD_FILE / KAFKA_SASL_PASSWORD  Contraseña SASL
    KAFKA_CLIENT_ID           ID del cliente (default: castuo-system)
    KAFKA_GROUP_ID            Grupo de consumo (default: castuo-workers)
    KAFKA_ACKS                Nivel de acks para productor (default: all)
    KAFKA_RETRIES             Reintentos del productor (default: 3)

Dependencias opcionales:
    pip install kafka-python>=2.0.0
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Generator

logger = logging.getLogger("castuo.kafka_client")


# ── Secrets helper ─────────────────────────────────────────────────────────────

def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


# ── Configuración ──────────────────────────────────────────────────────────────

KAFKA_SERVERS  = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")
KAFKA_USER     = os.getenv("KAFKA_SASL_USERNAME", "")
KAFKA_PASS     = _read_secret("KAFKA_SASL_PASSWORD")
KAFKA_CLIENT   = os.getenv("KAFKA_CLIENT_ID", "castuo-system")
KAFKA_GROUP    = os.getenv("KAFKA_GROUP_ID", "castuo-workers")
KAFKA_ACKS     = os.getenv("KAFKA_ACKS", "all")
KAFKA_RETRIES  = int(os.getenv("KAFKA_RETRIES", "3"))


# Topics del sistema
class KafkaTopic:
    CODE_UPDATES      = "code_updates"
    AI_EVENTS         = "ai_events"
    SENSOR_ALERTS     = "sensor_alerts"
    BLOCKCHAIN_EVENTS = "blockchain_events"
    MODEL_UPDATES     = "model_updates"


try:
    from kafka import KafkaProducer as _KafkaProducer  # type: ignore
    from kafka import KafkaConsumer as _KafkaConsumer  # type: ignore
    from kafka.errors import KafkaError  # type: ignore
    _KAFKA_AVAILABLE = True
except ImportError:
    _KAFKA_AVAILABLE = False
    logger.info("[kafka_client] kafka-python no instalado — modo simulación activo")


# ── Mensaje de evento ──────────────────────────────────────────────────────────

class KafkaEvent:
    def __init__(
        self,
        topic: str,
        event_type: str,
        payload: dict,
        source: str = "castuo-system",
        correlation_id: str | None = None,
    ) -> None:
        self.topic = topic
        self.event_type = event_type
        self.payload = payload
        self.source = source
        self.correlation_id = correlation_id or _generate_id()
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_type":     self.event_type,
            "source":         self.source,
            "correlation_id": self.correlation_id,
            "timestamp":      self.timestamp,
            "payload":        self.payload,
        }

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), ensure_ascii=False).encode("utf-8")


def _generate_id() -> str:
    import hashlib
    return hashlib.sha256(
        f"{time.time_ns()}".encode()
    ).hexdigest()[:16]


# ── Productor ─────────────────────────────────────────────────────────────────

class CastouKafkaProducer:
    """
    Productor Kafka con fallback a buffer en memoria cuando Kafka no está disponible.
    """

    def __init__(self) -> None:
        self._producer: Any = None
        self._sim_buffer: list[dict] = []
        self._connect()

    def _connect(self) -> None:
        if not _KAFKA_AVAILABLE:
            return
        try:
            kwargs: dict = {
                "bootstrap_servers": KAFKA_SERVERS,
                "client_id": KAFKA_CLIENT,
                "acks": KAFKA_ACKS,
                "retries": KAFKA_RETRIES,
                "value_serializer": lambda v: v if isinstance(v, bytes) else json.dumps(v).encode("utf-8"),
            }
            if KAFKA_PROTOCOL in ("SSL", "SASL_SSL"):
                kwargs["security_protocol"] = KAFKA_PROTOCOL
            if KAFKA_USER:
                kwargs.update({
                    "sasl_mechanism": "PLAIN",
                    "sasl_plain_username": KAFKA_USER,
                    "sasl_plain_password": KAFKA_PASS,
                })
            self._producer = _KafkaProducer(**kwargs)
            logger.info("[kafka_producer] Conectado a %s", KAFKA_SERVERS)
        except Exception as exc:
            logger.warning("[kafka_producer] No se pudo conectar: %s — modo simulación", exc)
            self._producer = None

    @property
    def is_connected(self) -> bool:
        return self._producer is not None

    def send(
        self,
        topic: str,
        event_type: str,
        payload: dict,
        source: str = "castuo-system",
        correlation_id: str | None = None,
        key: str | None = None,
    ) -> dict:
        """
        Publica un evento en el topic indicado.
        Retorna dict con ok, topic, correlation_id, simulado.
        """
        event = KafkaEvent(
            topic=topic,
            event_type=event_type,
            payload=payload,
            source=source,
            correlation_id=correlation_id,
        )
        published = False

        if self._producer:
            try:
                key_bytes = key.encode() if key else None
                future = self._producer.send(topic, value=event.to_bytes(), key=key_bytes)
                future.get(timeout=10)
                published = True
                logger.debug("[kafka_producer] Enviado %s → %s cid=%s", event_type, topic, event.correlation_id)
            except Exception as exc:
                logger.warning("[kafka_producer] Error enviando a %s: %s — simulando", topic, exc)

        if not published:
            record = {"topic": topic, **event.to_dict()}
            self._sim_buffer.append(record)
            if len(self._sim_buffer) > 1000:
                self._sim_buffer.pop(0)

        return {
            "ok":             True,
            "topic":          topic,
            "event_type":     event_type,
            "correlation_id": event.correlation_id,
            "timestamp":      event.timestamp,
            "simulado":       not published,
        }

    def send_code_update(self, repo: str, commit: str, actor: str, event: str = "push") -> dict:
        return self.send(
            KafkaTopic.CODE_UPDATES, "github.code_update",
            {"repo": repo, "commit": commit, "actor": actor, "event": event},
            key=repo,
        )

    def send_ai_event(self, model: str, action: str, tokens: int = 0, latency_ms: float = 0) -> dict:
        return self.send(
            KafkaTopic.AI_EVENTS, f"ai.{action}",
            {"model": model, "action": action, "tokens": tokens, "latency_ms": latency_ms},
        )

    def send_sensor_alert(self, lote_id: str, zona: str, tipo: str, valor: float) -> dict:
        return self.send(
            KafkaTopic.SENSOR_ALERTS, f"sensor.alert.{tipo}",
            {"lote_id": lote_id, "zona": zona, "tipo": tipo, "valor": valor},
            key=lote_id,
        )

    def send_blockchain_event(self, lote_id: str, tx_hash: str, tipo: str) -> dict:
        return self.send(
            KafkaTopic.BLOCKCHAIN_EVENTS, "blockchain.tx",
            {"lote_id": lote_id, "tx_hash": tx_hash, "tipo": tipo},
            key=lote_id,
        )

    def get_sim_buffer(self) -> list[dict]:
        return list(self._sim_buffer)

    def flush_sim_buffer(self) -> None:
        self._sim_buffer.clear()

    def close(self) -> None:
        if self._producer:
            self._producer.close()


# ── Consumidor ─────────────────────────────────────────────────────────────────

class CastouKafkaConsumer:
    """
    Consumidor Kafka con modo simulación cuando kafka-python no está disponible.
    """

    def __init__(self, topics: list[str], group_id: str | None = None) -> None:
        self._topics = topics
        self._group = group_id or KAFKA_GROUP
        self._consumer: Any = None
        self._connect()

    def _connect(self) -> None:
        if not _KAFKA_AVAILABLE:
            return
        try:
            kwargs: dict = {
                "bootstrap_servers": KAFKA_SERVERS,
                "group_id": self._group,
                "client_id": f"{KAFKA_CLIENT}-consumer",
                "auto_offset_reset": "latest",
                "enable_auto_commit": True,
                "value_deserializer": lambda x: json.loads(x.decode("utf-8")),
            }
            self._consumer = _KafkaConsumer(*self._topics, **kwargs)
            logger.info("[kafka_consumer] Suscrito a %s (group=%s)", self._topics, self._group)
        except Exception as exc:
            logger.warning("[kafka_consumer] No se pudo conectar: %s — modo simulación", exc)
            self._consumer = None

    @property
    def is_connected(self) -> bool:
        return self._consumer is not None

    def poll(self, timeout_ms: int = 1000) -> list[dict]:
        """Consume mensajes disponibles. Retorna lista vacía en simulación."""
        if self._consumer:
            try:
                records = self._consumer.poll(timeout_ms=timeout_ms)
                messages = []
                for tp, msgs in records.items():
                    for msg in msgs:
                        messages.append({
                            "topic":     msg.topic,
                            "partition": msg.partition,
                            "offset":    msg.offset,
                            "key":       msg.key.decode() if msg.key else None,
                            "value":     msg.value,
                            "timestamp": msg.timestamp,
                        })
                return messages
            except Exception as exc:
                logger.warning("[kafka_consumer] Error en poll: %s", exc)
        return []

    def close(self) -> None:
        if self._consumer:
            self._consumer.close()


# ── Instancias globales ────────────────────────────────────────────────────────

_producer_instance: CastouKafkaProducer | None = None


def get_producer() -> CastouKafkaProducer:
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = CastouKafkaProducer()
    return _producer_instance
