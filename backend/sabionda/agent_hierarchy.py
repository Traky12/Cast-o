# backend/sabionda/agent_hierarchy.py
"""12 Agentes subordinados a SABIONDA: prioridad, threshold, encriptación Kyber-1024."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

AGENTES_SUBORDINADOS: Dict[str, Dict[str, Any]] = {
    "auditoria": {"threshold": 95, "priority": 1, "encryption": "Kyber1024"},
    "vault": {"threshold": 30, "priority": 2, "encryption": "Kyber1024"},
    "monitoreo": {"threshold": 99.5, "priority": 3},
    "campo": {"threshold": 90, "priority": 4},
    "federacion": {"threshold": 100, "priority": 5},
    "blockchain": {"threshold": 100, "priority": 6},
    "ml_predict": {"threshold": 0, "priority": 7},
    "contracts": {"threshold": 100, "priority": 8},
    "anytype_sync": {"threshold": 100, "priority": 9},
    "compliance": {"threshold": 98, "priority": 10},
    "revenue": {"threshold": 0, "priority": 11},
    "alerting": {"threshold": 100, "priority": 12},
}


def get_agents_by_priority() -> List[str]:
    """Ordena agentes por prioridad (1 = mayor)."""
    return [a for a, _ in sorted(AGENTES_SUBORDINADOS.items(), key=lambda x: x[1]["priority"])]


def should_trigger_agent(agent_id: str, event: dict) -> bool:
    """True si el evento cruza el threshold del agente."""
    cfg = AGENTES_SUBORDINADOS.get(agent_id, {})
    th = cfg.get("threshold", 0)
    if th == 0:
        return True
    val = event.get("progress") or event.get("iso_pct") or event.get("consents_pct")
    if val is None:
        val = event.get("uptime_pct") or event.get("days_left")
    if val is None:
        return True
    try:
        v = float(val)
        return v < th
    except (TypeError, ValueError):
        return True


async def trigger_federated_agents(event: dict) -> List[str]:
    """Dispara agentes por prioridad; devuelve lista de ids disparados."""
    triggered: List[str] = []
    for agent_id in get_agents_by_priority():
        if should_trigger_agent(agent_id, event):
            triggered.append(agent_id)
            logger.info("Sabionda triggered agent: %s", agent_id)
    return triggered
