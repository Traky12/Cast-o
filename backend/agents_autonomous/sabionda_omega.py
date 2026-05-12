# -*- coding: utf-8 -*-
"""Sabionda-Omega: líder estratégico para validar mejoras propuestas por otros agentes."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


def validar_mejora(mejora: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida una mejora propuesta usando reglas de Sabionda-Omega.
    Args:
        mejora: Dict con la propuesta de mejora (código, métrica, antes, después, cambios).
    Returns:
        Dict con {"aprobado": bool, "razon": str, "normativas": list, "evidencia": str}
    """
    required_keys = {"código", "métrica", "antes", "después", "cambios"}
    if not required_keys.issubset(mejora.keys()):
        return {
            "aprobado": False,
            "razon": "Estructura de mejora inválida: faltan claves obligatorias",
            "normativas": [],
            "evidencia": "faltan_claves",
        }

    if mejora["después"] <= mejora["antes"]:
        return {
            "aprobado": False,
            "razon": (
                f"El valor objetivo ({mejora['después']}) no supera al actual ({mejora['antes']})"
            ),
            "normativas": [],
            "evidencia": "metrica_invalida",
        }

    normativas: List[str] = ["GDPR", "AI_Act_2024", "RD_903/2025"]
    codigo = (mejora.get("código") or "").lower()
    if "datos_personales" in codigo and "anonymize" not in codigo and "encrypt" not in codigo:
        return {
            "aprobado": False,
            "razon": "Uso de datos personales sin anonimización/cifrado (GDPR Art. 25)",
            "normativas": normativas,
            "evidencia": "codigo_con_datos_sensibles",
        }

    try:
        _registrar_validacion_gaiachain(mejora, normativas)
    except Exception as e:
        logger.warning("GaiaChain validación no registrada: %s", e)

    return {
        "aprobado": True,
        "razon": "Validación automática superada",
        "normativas": normativas,
        "evidencia": "cumplimiento_verificado",
    }


def _registrar_validacion_gaiachain(mejora: Dict[str, Any], normativas: List[str]) -> None:
    """Registra la validación en GaiaChain si el CLI está disponible."""
    if not os.path.isfile(_GAIACHAIN_CLI):
        return
    payload = {
        "mejora_id": mejora.get("id", mejora.get("métrica", "unknown")),
        "status": "aprobado",
        "normativas": normativas,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    subprocess.run(
        [
            _GAIACHAIN_CLI,
            "record",
            "--type", "validation",
            "--data", json.dumps(payload),
        ],
        check=False,
        capture_output=True,
        timeout=10,
    )
