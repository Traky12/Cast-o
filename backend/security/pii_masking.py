# -*- coding: utf-8 -*-
"""
Enmascaramiento PII ampliado — Barreras Sabionda v6.1 (GDPR Art.25, PCI DSS, LOPDGDD).
Passport, credit_card, geolocation (3 decimales), dni, nie, ip_address.
"""
from __future__ import annotations

import re
from typing import Any, Dict

# Placeholders para respuestas
PASSPORT_MASK = "[PASSPORT_MASCARA]"
TARJETA_MASK = "[TARJETA_MASCARA]"
DNI_MASK = "[DNI_MASCARA]"
NIE_MASK = "[NIE_MASCARA]"

# Patrones para detectar PII (no capturar valor real en logs)
RE_PASSPORT = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b", re.IGNORECASE)
RE_CREDIT = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
RE_DNI = re.compile(r"\b\d{8}[A-Z]\b", re.IGNORECASE)
RE_NIE = re.compile(r"\b[XYZ]\d{7}[A-Z]\b", re.IGNORECASE)
RE_IP = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}\b")
RE_GEOLOCATION = re.compile(r"(-?\d+\.\d{4,})")  # Reducir a 3 decimales


def mask_passport(value: str) -> str:
    if not value:
        return value
    return PASSPORT_MASK


def mask_credit_card(value: str) -> str:
    if not value:
        return value
    return TARJETA_MASK


def mask_dni(value: str) -> str:
    if not value or len(value) < 4:
        return "****"
    return "*****" + value[-4:] if len(value) >= 4 else DNI_MASK


def mask_nie(value: str) -> str:
    if not value or len(value) < 4:
        return "****"
    return "*****" + value[-4:] if len(value) >= 4 else NIE_MASK


def mask_ip(value: str) -> str:
    """Últimos 3 dígitos enmascarados: 192.168.1.100 → 192.168.1.X"""
    if not value:
        return value
    match = RE_IP.match(value.strip())
    if match:
        return match.group(1) + ".X"
    return "***.***.***.***"


def reduce_geolocation_precision(value: float | str, decimals: int = 3) -> str:
    """Precisión reducida para GDPR Art. 25 (ej. 39.471234 → 39.471)."""
    try:
        v = float(value)
        return f"{v:.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)[: (decimals + 2)]


def mask_pii_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recorre dict y aplica enmascaramiento a campos PII conocidos."""
    if not isinstance(data, dict):
        return data
    out = {}
    for k, v in data.items():
        key_lower = k.lower()
        if key_lower in ("passport", "passport_number", "passport_number"):
            out[k] = mask_passport(str(v))
        elif key_lower in ("credit_card", "tarjeta", "card_number", "creditcard"):
            out[k] = mask_credit_card(str(v))
        elif key_lower == "dni":
            out[k] = mask_dni(str(v))
        elif key_lower == "nie":
            out[k] = mask_nie(str(v))
        elif key_lower in ("ip", "ip_address", "client_ip"):
            out[k] = mask_ip(str(v))
        elif key_lower in ("latitude", "lat", "longitude", "lng", "geolocation"):
            out[k] = reduce_geolocation_precision(v)
        elif isinstance(v, dict):
            out[k] = mask_pii_in_dict(v)
        elif isinstance(v, list):
            out[k] = [mask_pii_in_dict(x) if isinstance(x, dict) else x for x in v]
        else:
            out[k] = v
    return out
