"""
Bitácora de Auditoría Centralizada
Registra cada acción (crear, actualizar, eliminar) en la cadena de custodia
con verificación de integridad hash
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional, cast
from uuid import uuid4

logger = logging.getLogger(__name__)


def _empty_payload() -> dict[str, Any]:
    return cast(dict[str, Any], {})

class AuditAction(str, Enum):
    """Acciones auditables en el sistema."""

    APERTURA_LOTE = "apertura_lote"
    REGISTRO_SOLUCION = "registro_solucion"
    REGISTRO_CLIMA = "registro_clima"
    REGISTRO_AGROVOLTAICO = "registro_agrovoltaico"
    REGISTRO_FITOSANITARIO = "registro_fitosanitario"
    REGISTRO_COSECHA = "registro_cosecha"
    REGISTRO_BLOCKCHAIN = "registro_blockchain"
    GENERACION_QR = "generacion_qr"
    VERIFICACION_QR = "verificacion_qr"
    CONTROL_ACTUADOR = "control_actuador"
    INGESTA_SENSORES = "ingesta_sensores"


class AuditSeverity(str, Enum):
    """Severidad de eventos de auditoría."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    """Evento de auditoría inmutable."""

    action: AuditAction
    actor_nif: str
    resource_type: str
    resource_id: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    severity: AuditSeverity = field(default=AuditSeverity.INFO)
    actor_role: str = field(default="operador")
    data: dict[str, Any] = field(default_factory=_empty_payload)
    hash_anterior: Optional[str] = field(default=None)
    hash_evento: Optional[str] = field(default=None, init=False)
    status: str = field(default="success")
    error_msg: Optional[str] = field(default=None)

    def __post_init__(self) -> None:
        self.refresh_hash()

    def compute_hash(self) -> str:
        """SHA-256 del evento actual."""
        payload: dict[str, Any] = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "action": self.action.value,
            "actor_nif": self.actor_nif,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "data": self.data,
            "hash_anterior": self.hash_anterior,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

    def refresh_hash(self) -> None:
        """Recalcular hash tras actualizar el encadenamiento."""
        self.hash_evento = self.compute_hash()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    def validate_chain(self, previous_event: Optional[AuditEvent]) -> bool:
        if previous_event is None:
            return self.hash_anterior is None
        return self.hash_anterior == previous_event.hash_evento


class AuditLogger:
    """Bitácora append-only de auditoría."""

    def __init__(self, log_dir: str = "logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit_chain.jsonl"
        self._last_event: Optional[AuditEvent] = None
        self._load_last_event()
        logger.info("Audit logger initialized at %s", self.log_file)

    def _load_last_event(self) -> None:
        if not self.log_file.exists():
            return
        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                last_line = None
                for line in handle:
                    last_line = line.strip()
            if last_line:
                self._last_event = self._dict_to_event(json.loads(last_line))
        except Exception as exc:
            logger.warning("Failed to load last audit event: %s", exc)

    @staticmethod
    def _dict_to_event(data: dict[str, Any]) -> AuditEvent:
        return AuditEvent(
            action=AuditAction(data["action"]),
            actor_nif=str(data["actor_nif"]),
            resource_type=str(data["resource_type"]),
            resource_id=str(data["resource_id"]),
            event_id=str(data["event_id"]),
            timestamp=str(data["timestamp"]),
            severity=AuditSeverity(data.get("severity", AuditSeverity.INFO.value)),
            actor_role=str(data.get("actor_role", "operador")),
            data=data.get("data", {}),
            hash_anterior=data.get("hash_anterior"),
            status=str(data.get("status", "success")),
            error_msg=data.get("error_msg"),
        )

    def log_event(self, event: AuditEvent) -> str:
        if self._last_event:
            event.hash_anterior = self._last_event.hash_evento
        event.refresh_hash()
        try:
            with open(self.log_file, "a", encoding="utf-8") as handle:
                handle.write(event.to_json() + "\n")
            self._last_event = event
            logger.info("Audit event logged: %s (action=%s)", event.event_id, event.action.value)
        except Exception as exc:
            logger.error("Failed to log audit event: %s", exc)
            raise
        return event.event_id

    def search_by_lote_id(self, lote_id: str) -> list[AuditEvent]:
        events: list[AuditEvent] = []
        if not self.log_file.exists():
            return events
        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    data = json.loads(line.strip())
                    if data.get("resource_id") == lote_id:
                        events.append(self._dict_to_event(data))
        except Exception as exc:
            logger.warning("Failed to search audit log by lote_id: %s", exc)
        return events

    def search_by_operator(self, operador_nif: str) -> list[AuditEvent]:
        events: list[AuditEvent] = []
        if not self.log_file.exists():
            return events
        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    data = json.loads(line.strip())
                    if data.get("actor_nif") == operador_nif:
                        events.append(self._dict_to_event(data))
        except Exception as exc:
            logger.warning("Failed to search audit log by operator: %s", exc)
        return events

    def search_by_action(self, action: AuditAction) -> list[AuditEvent]:
        events: list[AuditEvent] = []
        if not self.log_file.exists():
            return events
        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    data = json.loads(line.strip())
                    if data.get("action") == action.value:
                        events.append(self._dict_to_event(data))
        except Exception as exc:
            logger.warning("Failed to search audit log by action: %s", exc)
        return events

    def verify_chain_integrity(self) -> bool:
        events: list[AuditEvent] = []
        if not self.log_file.exists():
            return True
        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                for line in handle:
                    events.append(self._dict_to_event(json.loads(line.strip())))
        except Exception as exc:
            logger.error("Failed to read audit log for verification: %s", exc)
            return False

        for index, event in enumerate(events):
            previous: Optional[AuditEvent] = events[index - 1] if index > 0 else None
            if not event.validate_chain(previous):
                logger.error("Chain integrity broken at event %s", event.event_id)
                return False

        logger.info("Audit chain integrity verified (%s events)", len(events))
        return True

    def get_chain_summary(self) -> dict[str, Any]:
        if not self.log_file.exists():
            return {
                "total_events": 0,
                "earliest": None,
                "latest": None,
                "actions_count": 0,
                "actors_count": 0,
                "chain_intact": True,
                "first_event_id": None,
                "last_event_id": None,
            }

        try:
            with open(self.log_file, "r", encoding="utf-8") as handle:
                raw_events: list[dict[str, Any]] = [json.loads(line.strip()) for line in handle if line.strip()]
        except Exception as exc:
            logger.error("Failed to compute chain summary: %s", exc)
            return {}

        return {
            "total_events": len(raw_events),
            "earliest": raw_events[0]["timestamp"] if raw_events else None,
            "latest": raw_events[-1]["timestamp"] if raw_events else None,
            "first_event_id": raw_events[0]["event_id"] if raw_events else None,
            "last_event_id": raw_events[-1]["event_id"] if raw_events else None,
            "actions_count": len({event.get("action") for event in raw_events}),
            "actors_count": len({event.get("actor_nif") for event in raw_events}),
            "chain_intact": self.verify_chain_integrity(),
        }


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Obtener la instancia global del logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
