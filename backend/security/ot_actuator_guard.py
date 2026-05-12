# -*- coding: utf-8 -*-
"""
Barrera OT lógica antes de traducir intención API → campo (PLC/MQTT/Modbus).
No sustituye segmentación de red, PLC maestro ni parada física; reduce superficie de abuso remoto.
"""
from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from backend.config import actuators_config

logger = logging.getLogger(__name__)

_DEFAULT_CRITICAL = frozenset({"valvula_agua", "valvula_nutrientes"})


def _truthy(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "on"}


def killswitch_energize_blocked() -> bool:
    """Bloquea ENERGIZAR (state=True) desde API; OFF y emergency siguen siendo alcanzables."""
    return _truthy(os.getenv("OT_ACTUATOR_KILLSWITCH", ""))


def remote_energize_allowed() -> bool:
    """Si False, no se permite state=True salvo política de laboratorio explícita."""
    raw = os.getenv("OT_REMOTE_ACTUATOR_WRITES", "")
    if raw.strip() == "":
        return True
    return _truthy(raw)


def critical_actuator_ids() -> frozenset:
    raw = os.getenv("OT_CRITICAL_ACTUATOR_IDS", "").strip()
    if not raw:
        return _DEFAULT_CRITICAL
    return frozenset(x.strip() for x in raw.split(",") if x.strip())


def lab_auth_bypass() -> bool:
    return os.getenv("AUTH_DISABLED", "").strip().lower() in {"1", "true", "yes"}


class OTActuatorPolicyError(Exception):
    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(detail)


_rate_bucket: Dict[Tuple[str, str], List[float]] = defaultdict(list)


def _rate_allow(zone_id: str, actuator_id: str) -> bool:
    max_c = int(os.getenv("OT_ACTUATOR_RATE_MAX", "30"))
    window = float(os.getenv("OT_ACTUATOR_RATE_WINDOW_S", "60"))
    now = time.time()
    key = (zone_id, actuator_id)
    bucket = _rate_bucket[key]
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= max_c:
        return False
    bucket.append(now)
    return True


def check_actuator_command(
    zone_id: str,
    actuator_id: str,
    state: bool,
    *,
    roles: Optional[List[str]] = None,
    subject: str = "unknown",
) -> None:
    """
    Valida energización remota. Des-energizar (state=False) se permite para recuperación segura
    salvo política futura OT_ACTUATOR_BLOCK_ALL_API=1.
    """
    if os.getenv("OT_ACTUATOR_BLOCK_ALL_API", "").strip().lower() in {"1", "true", "yes"}:
        raise OTActuatorPolicyError(
            "api_blocked",
            "OT_ACTUATOR_BLOCK_ALL_API: comandos de actuador deshabilitados en esta instancia",
        )
    if not state:
        if not _rate_allow(zone_id, actuator_id):
            raise OTActuatorPolicyError("rate_limit", "Exceso de comandos OT; use PLC local o espere ventana")
        log_audit(
            "actuator_command_deenergize_allowed",
            {
                "zone_id": zone_id,
                "actuator_id": actuator_id,
                "subject": subject,
            },
        )
        return
    if killswitch_energize_blocked():
        raise OTActuatorPolicyError(
            "killswitch",
            "OT_ACTUATOR_KILLSWITCH: energización remota bloqueada; desactivar solo en mantenimiento supervisado",
        )
    if not remote_energize_allowed():
        raise OTActuatorPolicyError(
            "writes_disabled",
            "OT_REMOTE_ACTUATOR_WRITES=false: energización solo desde PLC/borde certificado",
        )
    crit = critical_actuator_ids()
    if actuator_id in crit:
        allowed = {"admin", "owner"}
        r = set(roles or [])
        if lab_auth_bypass():
            if (r & allowed) or _truthy(os.getenv("OT_ALLOW_CRITICAL_ENERGIZE_IN_LAB", "")):
                logger.warning(
                    "ot.lab_critical_energize zone=%s actuator=%s subject=%s",
                    zone_id,
                    actuator_id,
                    subject,
                )
            else:
                raise OTActuatorPolicyError(
                    "critical_lab",
                    "Actuador crítico en labor: requiere rol admin/owner en token o OT_ALLOW_CRITICAL_ENERGIZE_IN_LAB=1",
                )
        elif not (r & allowed):
            raise OTActuatorPolicyError(
                "privilege",
                "Actuador crítico: se requiere rol Keycloak admin u owner para energizar",
            )
        if not actuators_config.safe_mode_allows_critical_energize():
            raise OTActuatorPolicyError(
                "safe_window",
                "Fuera de ventana OT_SAFE_MODE_WINDOWS (UTC) para energizar actuador crítico",
            )
    if not _rate_allow(zone_id, actuator_id):
        raise OTActuatorPolicyError(
            "rate_limit",
            "Exceso de comandos OT en ventana; mitigación anti pulsación errónea",
        )
    log_audit(
        "actuator_command_energize_allowed",
        {
            "zone_id": zone_id,
            "actuator_id": actuator_id,
            "subject": subject,
            "roles": roles or [],
        },
    )
    if OT_CRITICAL_COMMANDS is not None and actuator_id in critical_actuator_ids():
        OT_CRITICAL_COMMANDS.labels(actuator_id=actuator_id, direction="energize").inc()


def check_emergency_stop(*, subject: str = "unknown") -> None:
    if not _truthy(os.getenv("OT_EMERGENCY_API_ENABLED", "true")):
        raise OTActuatorPolicyError(
            "emergency_disabled",
            "OT_EMERGENCY_API_ENABLED=false: usar parada física o PLC",
        )
    log_audit("emergency_stop_invoked", {"subject": subject})


def log_audit(event: str, payload: Dict[str, Any]) -> None:
    logger.info("ot_actuator_audit event=%s payload=%s", event, payload)


try:
    from prometheus_client import Counter

    OT_ACTUATOR_DENIALS = Counter(
        "castuo_ot_actuator_denials_total",
        "Denegaciones política OT (actuadores API)",
        ["code"],
    )
    OT_CRITICAL_COMMANDS = Counter(
        "ot_critical_actuator_commands_total",
        "Comandos de energización hacia actuadores críticos (post-validación OT)",
        ["actuator_id", "direction"],
    )
except ImportError:
    OT_ACTUATOR_DENIALS = None  # type: ignore[misc,assignment]
    OT_CRITICAL_COMMANDS = None  # type: ignore[misc,assignment]


def record_denial(code: str) -> None:
    if OT_ACTUATOR_DENIALS is not None:
        OT_ACTUATOR_DENIALS.labels(code).inc()
