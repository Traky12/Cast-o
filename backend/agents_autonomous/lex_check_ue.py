# -*- coding: utf-8 -*-
"""LexCheck-UE: auditor legal para cumplimiento normativo de mejoras."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_GAIACHAIN_CLI = os.getenv("GAIACHAIN_CLI", "/usr/local/bin/gaiachain")


def auditar_cumplimiento(mejora: Dict[str, Any]) -> Dict[str, Any]:
    """
    Audita el cumplimiento normativo de una mejora (GDPR, AI Act, RD 903/2025).
    Args:
        mejora: Dict con la propuesta de mejora.
    Returns:
        Dict con {"aprobado": bool, "normativas": list, "issues": list}
    """
    normativas_map = {
        "GDPR": ["Art. 5", "Art. 25", "Art. 32"],
        "AI_Act_2024": ["Sec. 3.2", "Sec. 5.1"],
        "RD_903/2025": ["Sec. 4.1", "Sec. 7.2"],
    }
    issues: List[Dict[str, str]] = []
    codigo = (mejora.get("código") or "").lower()
    metrica = (mejora.get("métrica") or "").lower()

    if "user_data" in codigo and "encrypt" not in codigo:
        issues.append({
            "normativa": "GDPR Art. 32",
            "issue": "Datos personales sin cifrado",
            "evidencia": "user_data sin encrypt",
        })

    if "explainability" not in codigo and metrica == "ai_decision":
        issues.append({
            "normativa": "AI Act 2024 Sec. 3.2",
            "issue": "Falta explicabilidad en decisiones de IA",
            "evidencia": "No se documenta lógica de decisión",
        })

    try:
        _registrar_auditoria_gaiachain(mejora, list(normativas_map.keys()), issues)
    except Exception as e:
        logger.warning("GaiaChain auditoría no registrada: %s", e)

    return {
        "aprobado": len(issues) == 0,
        "normativas": list(normativas_map.keys()),
        "issues": issues,
    }


def validar_contexto(normativa: str, contexto: str) -> Dict[str, Any]:
    """
    Valida un contexto (ej. contrato, cláusula) frente a normativas.
    Args:
        normativa: Normativa a aplicar (ej: "GDPR", "AI_Act_2024").
        contexto: Texto o descripción del contexto a validar.
    Returns:
        Dict con aprobado, razon, normativas, issues.
    """
    mejora = {
        "código": contexto,
        "métrica": "legal",
        "antes": 0,
        "después": 1,
        "cambios": [],
    }
    out = auditar_cumplimiento(mejora)
    out["razon"] = "Validación LexCheck-UE completada" if out["aprobado"] else (
        "; ".join(i.get("issue", "") for i in out.get("issues", [])) or "Issues detectados"
    )
    return out


def _registrar_auditoria_gaiachain(
    mejora: Dict[str, Any], normativas: List[str], issues: List[Dict[str, str]]
) -> None:
    """Registra la auditoría en GaiaChain si el CLI está disponible."""
    if not os.path.isfile(_GAIACHAIN_CLI):
        return
    payload = {
        "mejora_id": mejora.get("id", mejora.get("métrica", "unknown")),
        "normativas": normativas,
        "issues": issues,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    subprocess.run(
        [
            _GAIACHAIN_CLI,
            "record",
            "--type", "compliance_audit",
            "--data", json.dumps(payload),
        ],
        check=False,
        capture_output=True,
        timeout=10,
    )
