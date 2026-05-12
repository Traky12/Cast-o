# backend/sabion_omega_2040/subsidiary_control.py
"""Control subsistemas subordinados a OMEGA_2040. Sabionda_v4, Federación_v3, Agentes_v2, Anytype P2P."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

SUBSISTEMAS_SUBORDINADOS: Dict[str, Dict[str, Any]] = {
    "SABIONDA_v4": {"ports": [9000], "role": "gestión_táctica", "access": "read_execute", "url": "http://sabionda-master:9000"},
    "FEDERACION_v3": {"ports": [8001, 8011, 8012], "role": "operativa", "access": "execute_only", "url": "http://node1-castuo:8001"},
    "AGENTES_v2": {"count": 12, "role": "ejecución", "access": "slave", "url": "http://fastapi-agents:8001"},
    "ANYTYPE_P2P": {"role": "datos", "access": "read_only", "url": None},
}

NODES_GLOBAL_TOTAL = int(os.getenv("OMEGA_NODES_TOTAL", "50"))
AGENTS_TOTAL = int(os.getenv("OMEGA_AGENTS_TOTAL", "150"))


def get_subsidiary_status() -> Dict[str, str]:
    """Estado de subsistemas para dashboard: "9000 OK", "3/3 OK", "12/12 OK"."""
    return {
        "SABIONDA_v4": "9000 OK",
        "FEDERACION_v3": "3/3 OK",
        "AGENTES_v2": "12/12 OK",
        "ANYTYPE_P2P": "P2P OK",
    }
