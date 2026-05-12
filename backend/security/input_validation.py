# -*- coding: utf-8 -*-
"""
Validación de inputs — Barreras Sabionda v6.1.
JSON Schema para IoT, regex BLOCK (SQLi/XSS/comandos), rangos normativos.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# Rangos válidos por parámetro (normativa)
IOT_SCHEMA: Dict[str, Dict[str, Any]] = {
    "farm_id": {"min": 1, "max": 9100, "norm": "ISO 17025", "action": "reject_gaia"},
    "temp": {"min": -10, "max": 50, "norm": "Reglamento UE 2018/848", "action": "alert_ctaex_block"},
    "hum": {"min": 0, "max": 100, "norm": "UNE 100021", "action": "recalibrate"},
    "soil_moisture": {"min": 0, "max": 100, "norm": "PAC 2027", "action": "validate_lims"},
    "light": {"min": 0, "max": 100_000, "norm": "ISO 17025", "action": "yield_optimizer"},
    "co2": {"min": 0, "max": 2000, "norm": "ODS 13", "action_high": "alert_over_500"},
    "energy_consumption": {"min": 0, "max": 10, "norm": "ODS 7", "action": "agrovoltaic"},
}

# Patrones bloqueados (SQLi, XSS, comandos peligrosos)
REGEX_BLOCK = re.compile(
    r"(?i)(drop\s+table|delete\s+from|union\s+select|;\s*--|xp_cmdshell|alter\s+table|"
    r"truncate\s+table|<script[^>]*>|javascript:|onload\s*=|document\.cookie|eval\s*\(|"
    r"child_process|wget\s+.*\.sh|curl\s+.*bash|python\s+-c|rm\s+-rf|exec\s+sp_|"
    r"shutdown|halt|poweroff|>\s*/dev/null|mkfifo|/bin/sh|nc\s+-lvp)",
    re.IGNORECASE,
)


def validate_iot_payload(payload: Dict[str, Any]) -> Tuple[bool, List[str], str | None]:
    """
    Valida payload IoT según schema (rangos y normativa).
    Returns: (ok, list of errors, action_if_fail)
    """
    errors: List[str] = []
    action: str | None = None
    for key, config in IOT_SCHEMA.items():
        if key not in payload:
            continue
        try:
            val = float(payload[key]) if not isinstance(payload[key], (int, float)) else payload[key]
        except (TypeError, ValueError):
            errors.append(f"{key}: valor no numérico")
            continue
        min_v = config.get("min")
        max_v = config.get("max")
        if min_v is not None and val < min_v:
            errors.append(f"{key}: {val} < {min_v} ({config.get('norm', '')})")
            action = config.get("action") or config.get("action_high")
        if max_v is not None and val > max_v:
            errors.append(f"{key}: {val} > {max_v} ({config.get('norm', '')})")
            action = config.get("action") or config.get("action_high")
        if key == "co2" and val > 500:
            action = "alert_sustainability"
    return (len(errors) == 0, errors, action)


def contains_blocked_pattern(text: str) -> bool:
    """Comprueba si el texto contiene patrones bloqueados (SQLi/XSS/comandos)."""
    if not text or not isinstance(text, str):
        return False
    return bool(REGEX_BLOCK.search(text))


def validate_input_payload(body: Any) -> Tuple[bool, str | None]:
    """
    Valida body de request: recursivo en dict/list; rechaza si aparece patrón bloqueado.
    Returns: (ok, reason_if_blocked)
    """
    if body is None:
        return True, None
    if isinstance(body, str):
        if contains_blocked_pattern(body):
            return False, "Patrón bloqueado (seguridad)"
        return True, None
    if isinstance(body, dict):
        for k, v in body.items():
            if contains_blocked_pattern(str(k)):
                return False, "Clave con patrón bloqueado"
            ok, reason = validate_input_payload(v)
            if not ok:
                return False, reason
        return True, None
    if isinstance(body, list):
        for item in body:
            ok, reason = validate_input_payload(item)
            if not ok:
                return False, reason
        return True, None
    return True, None
