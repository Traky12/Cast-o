# backend/agents/protocol.py
# Protocolo estándar de comunicación entre agentes (FIPA-style, cifrado PQC)

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from backend.agents.message_bus import AgentMessageBus
except ImportError:
    AgentMessageBus = None


class AgentMessageType(Enum):
    TASK = "task"
    RESPONSE = "response"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    BROADCAST = "broadcast"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"


class AgentProtocol:
    """
    Protocolo de mensajes entre agentes: estructura, cifrado, timeouts y reintentos.
    """

    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name
        self.logger = logging.getLogger(__name__)
        self.crypto: Any = None
        try:
            from backend.security.pq_crypto import PostQuantumCrypto
            self.crypto = PostQuantumCrypto()
        except Exception as e:
            self.logger.debug("PostQuantumCrypto no disponible: %s", e)
        self.message_bus: Any = AgentMessageBus(agent_name) if AgentMessageBus else None
        self.timeouts = {
            AgentMessageType.TASK: 30,
            AgentMessageType.RESPONSE: 60,
            AgentMessageType.SYNC_REQUEST: 120,
            AgentMessageType.SYNC_RESPONSE: 180,
        }
        self.max_retries = 3
        self._max_message_age_seconds = 300
        self._handlers: Dict[AgentMessageType, Callable[[Dict], bool]] = {}

    def create_message(
        self,
        message_type: AgentMessageType,
        content: Dict[str, Any],
        recipient: Optional[str] = None,
        encrypt: bool = True,
    ) -> Dict[str, Any]:
        raw_body = {
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender": self.agent_name,
            "recipient": recipient,
            "message_type": message_type.value,
            "message_id": hashlib.sha3_512(
                f"{self.agent_name}{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()[:16],
        }
        message = {"header": raw_body, "body": content}
        if encrypt and self.crypto:
            try:
                enc = self.crypto.hybrid_encrypt(json.dumps(message["body"]))
                message["body"] = {"_encrypted": True, "algorithm": enc.get("algorithm", ""), "data": enc}
            except Exception as e:
                self.logger.error("Error cifrando cuerpo: %s", e)
        return message

    def send_message(self, message: Dict[str, Any], queue: str) -> None:
        if self.message_bus:
            self.message_bus.publish(queue, message, encrypt=False)

    def broadcast(self, message: Dict[str, Any]) -> None:
        if self.message_bus:
            self.message_bus.broadcast(message, encrypt=False)

    def register_handler(self, message_type: AgentMessageType, handler: Callable[[Dict], bool]) -> None:
        self._handlers[message_type] = handler

    def start_consuming_private(self) -> None:
        """Consume desde la cola privada del agente y despacha por message_type."""
        if not self.message_bus or f"{self.agent_name}.private" not in self.queues:
            self.logger.warning("Message bus o cola privada no disponible")
            return

        def dispatch(channel_message: Dict) -> bool:
            try:
                header = channel_message.get("header") or {}
                mt = header.get("message_type")
                for msg_type, h in self._handlers.items():
                    if msg_type.value == mt:
                        if self._validate_message(channel_message, msg_type):
                            return h(channel_message)
                        return False
                self.logger.debug("Tipo de mensaje sin handler: %s", mt)
                return True
            except Exception as e:
                self.logger.error("Error en dispatch: %s", e)
                return False

        self.message_bus.consume(f"{self.agent_name}.private", dispatch)

    def _validate_message(self, message: Dict[str, Any], expected_type: AgentMessageType) -> bool:
        if not isinstance(message, dict):
            return False
        if "header" not in message or "body" not in message:
            return False
        header = message["header"]
        if not isinstance(header, dict):
            return False
        for k in ("version", "timestamp", "sender", "message_type", "message_id"):
            if k not in header:
                return False
        if header.get("message_type") != expected_type.value:
            return False
        try:
            ts = header["timestamp"]
            if isinstance(ts, str):
                if ts.endswith("Z"):
                    ts = ts.replace("Z", "+00:00")
                msg_time = datetime.fromisoformat(ts)
            else:
                return False
            now = datetime.now(timezone.utc)
            if msg_time.tzinfo is None:
                msg_time = msg_time.replace(tzinfo=timezone.utc)
            age = (now - msg_time).total_seconds()
            if age < -60 or age > self._max_message_age_seconds:
                self.logger.warning("Mensaje fuera de ventana temporal: age=%s", age)
                return False
        except Exception as e:
            self.logger.debug("Validación timestamp: %s", e)
            return False
        return True
