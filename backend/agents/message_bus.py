# backend/agents/message_bus.py
# Bus de mensajes entre agentes (RabbitMQ). Cifrado post-cuántico opcional.

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

try:
    import pika
    _PIKA = True
except ImportError:
    pika = None
    _PIKA = False


class AgentMessageBus:
    """
    Mensajería entre agentes vía RabbitMQ.
    Mensajes opcionalmente cifrados con PostQuantumCrypto (Kyber-1024 + AES-256-GCM).
    """

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self.logger = logging.getLogger(__name__)
        self._conn: Any = None
        self._channel: Any = None
        self.crypto: Any = None
        try:
            from backend.security.pq_crypto import PostQuantumCrypto
            self.crypto = PostQuantumCrypto()
        except Exception as e:
            self.logger.debug("PostQuantumCrypto no disponible: %s", e)

        self.queues: Dict[str, str] = {
            "ecommerce": "agent.ecommerce",
            "security": "agent.security",
            "maintenance": "agent.maintenance",
            "development": "agent.development",
            "compliance": "agent.compliance",
            "broadcast": "agent.broadcast",
            f"{agent_name}.private": f"agent.{agent_name}.private",
        }
        if _PIKA:
            self._connect()
        else:
            self.logger.warning("pika no instalado; message_bus en modo stub")

    def _connect(self) -> None:
        host = os.getenv("RABBITMQ_HOST", "localhost")
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        user = os.getenv("RABBITMQ_USER", "guest")
        password = os.getenv("RABBITMQ_PASSWORD", "guest")
        try:
            params = pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=pika.PlainCredentials(user, password),
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self._conn = pika.BlockingConnection(params)
            self._channel = self._conn.channel()
            for q in self.queues.values():
                self._channel.queue_declare(queue=q, durable=True)
            self._channel.exchange_declare(exchange="agent_broadcast", exchange_type="fanout")
            self.logger.info("%s conectado a RabbitMQ", self.agent_name)
        except Exception as e:
            self.logger.error("Error RabbitMQ: %s", e)
            self._conn = None
            self._channel = None

    def publish(self, queue: str, message: Dict[str, Any], encrypt: bool = True) -> None:
        if queue not in self.queues:
            raise ValueError(f"Cola desconocida: {queue}")
        if not self._channel:
            self.logger.debug("RabbitMQ no disponible; mensaje no enviado")
            return
        payload: Dict[str, Any] = message
        if encrypt and self.crypto:
            try:
                enc = self.crypto.hybrid_encrypt(json.dumps(message))
                payload = {"_encrypted": True, "algorithm": enc.get("algorithm", ""), "data": enc}
            except Exception as e:
                self.logger.error("Error cifrando mensaje: %s", e)
                return
        body = json.dumps(payload)
        self._channel.basic_publish(
            exchange="",
            routing_key=self.queues[queue],
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                headers={"sender": self.agent_name, "timestamp": str(datetime.utcnow().timestamp())},
            ),
        )
        self.logger.debug("Mensaje publicado en %s", queue)

    def broadcast(self, message: Dict[str, Any], encrypt: bool = True) -> None:
        if not self._channel:
            return
        payload: Dict[str, Any] = message
        if encrypt and self.crypto:
            try:
                enc = self.crypto.hybrid_encrypt(json.dumps(message))
                payload = {"_encrypted": True, "algorithm": enc.get("algorithm", ""), "data": enc}
            except Exception as e:
                self.logger.error("Error cifrando broadcast: %s", e)
                return
        self._channel.basic_publish(
            exchange="agent_broadcast",
            routing_key="",
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
                headers={"sender": self.agent_name, "timestamp": str(datetime.utcnow().timestamp())},
            ),
        )

    def consume(self, queue: str, callback: Callable[[Dict], bool], auto_ack: bool = False) -> None:
        if queue not in self.queues or not self._channel:
            self.logger.warning("Consume: cola o canal no disponible")
            return

        def on_message(ch: Any, method: Any, properties: Any, body: bytes) -> None:
            try:
                msg = json.loads(body)
                if msg.get("_encrypted") and self.crypto:
                    dec = self.crypto.hybrid_decrypt(msg["data"])
                    msg = json.loads(dec)
                elif isinstance(msg.get("body"), dict) and msg["body"].get("_encrypted") and self.crypto:
                    msg["body"] = json.loads(self.crypto.hybrid_decrypt(msg["body"]["data"]))
                ack = callback(msg)
                if not auto_ack:
                    if ack:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as e:
                self.logger.error("Error procesando mensaje: %s", e)
                if not auto_ack:
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self._channel.basic_consume(queue=self.queues[queue], on_message_callback=on_message, auto_ack=auto_ack)
        self.logger.info("Consumiendo de %s", queue)

    def start_consuming(self) -> None:
        if self._channel:
            self._channel.start_consuming()

    def close(self) -> None:
        try:
            if self._conn and not self._conn.is_closed:
                self._conn.close()
        except Exception as e:
            self.logger.error("Error cerrando RabbitMQ: %s", e)
