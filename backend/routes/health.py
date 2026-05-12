"""
Health Router — CASTÚO-SYSTEM v3.1
Expone chain_status y estado del lab neuromórfico sin autenticación.

DPIA-Robotics-2026 §6:
  "GET /health expone chain_status (disabled | ready | misconfigured)
   y si el lab neuromórfico está activo, sin Bearer ni secretos."

Consumido por:
  - docker-compose healthcheck
  - Prometheus scraper (uptime metric)
  - Operadores y auditores externos
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


def _chain_status() -> str:
    """
    Calcula el estado blockchain sin revelar secretos.
    disabled     → CASTUO_ROBOTICS_LAB_CHAIN_REGISTER != "1"
    ready         → flag activo y todas las vars GAIA_CHAIN_* presentes
    misconfigured → flag activo pero alguna var requerida falta
    """
    if os.getenv("CASTUO_ROBOTICS_LAB_CHAIN_REGISTER", "0") != "1":
        return "disabled"
    required = [
        "GAIA_CHAIN_RPC",
        "GAIA_CHAIN_AUDIT_CONTRACT",
        "GAIA_CHAIN_AUDIT_ABI",
        "GAIA_CHAIN_PRIVATE_KEY",
    ]
    missing = [v for v in required if not os.getenv(v)]
    return "ready" if not missing else "misconfigured"


@router.get("/health")
async def health() -> dict:
    """
    Healthcheck principal de CASTÚO-SYSTEM.
    Responde sin autenticación; no expone secretos.

    chain_status values:
      disabled      — blockchain off (por defecto, seguro)
      ready         — blockchain activo y correctamente configurado
      misconfigured — blockchain activado pero vars faltantes
    """
    return {
        "status": "ok",
        "service": "castuo-api",
        # legacy fields — kept for backwards compatibility with existing tests/clients
        "agent": "SABIONDA",
        "version": "3.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        # DPIA-Robotics-2026 §6 fields
        "chain_status": _chain_status(),
        "neuromorphic_lab": os.getenv("CASTUO_NEUROMORPHIC_LAB", "0") == "1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
