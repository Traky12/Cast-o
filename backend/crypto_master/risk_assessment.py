# backend/crypto_master/risk_assessment.py
# Scoring riesgo dinámico por acción y contexto.

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

RISK_WEIGHTS = {
    "god_mode": 0.9,
    "kill_all": 1.0,
    "audit_purge": 0.8,
    "kyber_rotate": 0.5,
    "restart_nodes": 0.3,
    "revenue_target": 0.2,
    "derive_key": 0.4,
    "default": 0.1,
}


def calculate_risk(action: str, context: Dict[str, Any]) -> float:
    """Riesgo 0.0-1.0 según acción y contexto."""
    base = RISK_WEIGHTS.get(action.lower(), RISK_WEIGHTS.get("default", 0.1))
    if context.get("admin") != "GREGORIO_J_JIMENEZ_BODES" and base > 0.5:
        return 1.0
    if context.get("encrypted"):
        base *= 0.5
    return min(1.0, base)
