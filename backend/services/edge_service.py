# -*- coding: utf-8 -*-
"""
Puente lógico API → campo: validación duplicada útil en broker edge o worker sin FastAPI.
La ejecución física (Modbus/MQTT) debe ocurrir en gateway OT; aquí solo stub y trazas.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from backend.config import actuators_config
from backend.security.ot_actuator_guard import critical_actuator_ids, killswitch_energize_blocked, remote_energize_allowed

logger = logging.getLogger(__name__)


class EdgeService:
    """Validación previa a reenvío hacia PLC/gateway; `send_to_actuator` es stub hasta drivers OT."""

    @staticmethod
    def validate_forward_payload(
        zone_id: str,
        actuator_id: str,
        *,
        energize: bool,
        command: str,
        value: Optional[float] = None,
    ) -> Dict[str, Any]:
        if energize:
            if killswitch_energize_blocked():
                raise ValueError("OT_ACTUATOR_KILLSWITCH: energización bloqueada")
            if not remote_energize_allowed():
                raise ValueError("OT_REMOTE_ACTUATOR_WRITES: energización remota deshabilitada")
            if actuator_id in critical_actuator_ids():
                if not actuators_config.safe_mode_allows_critical_energize():
                    raise ValueError(
                        "Ventana OT segura (OT_SAFE_MODE_WINDOWS) no permite energizar actuador crítico ahora"
                    )
        if command not in {"on", "off", "set"}:
            raise ValueError(f"Comando no válido: {command}")
        if command == "set":
            if value is None or value < 0 or value > 100:
                raise ValueError("Valor set debe estar en [0,100]")
        return {
            "status": "valid",
            "zone_id": zone_id,
            "actuator_id": actuator_id,
            "command": command,
            "value": value,
        }

    @staticmethod
    def map_bool_to_command(state: bool, intensity: Optional[float]) -> tuple[str, Optional[float]]:
        if intensity is not None:
            return "set", float(intensity)
        return ("on" if state else "off"), None

    @staticmethod
    def send_to_actuator(
        actuator_id: str,
        command: str,
        value: Optional[float],
        protocol: str,
        topic_or_register: str,
        zone_id: str = "",
    ) -> Dict[str, Any]:
        if os.getenv("OT_EDGE_SEND_STUB_ONLY", "true").strip().lower() in {"1", "true", "yes"}:
            logger.info(
                "edge.send_stub actuator=%s cmd=%s protocol=%s target=%s zone=%s",
                actuator_id,
                command,
                protocol,
                topic_or_register,
                zone_id,
            )
            return {
                "status": "stub",
                "actuator_id": actuator_id,
                "command": command,
                "value": value,
                "protocol": protocol,
                "target": topic_or_register,
                "zone_id": zone_id,
                "detail": "Sustituir por cliente Modbus/MQTT en gateway OT aislado",
            }
        raise NotImplementedError("OT_EDGE_SEND_STUB_ONLY=false requiere drivers de campo")
