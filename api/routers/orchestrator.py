"""
Orchestrator Router — CASTÚO-SYSTEM™ v3.1
Expone el estado de los servicios via CastouSovereignOrchestrator.

Endpoints:
  GET  /api/v1/orchestrator/status  — health de todos los servicios integrados
  POST /api/v1/orchestrator/task    — encolar y ejecutar una tarea orquestada
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/orchestrator", tags=["orchestrator"])


class TaskRequest(BaseModel):
    task_type: str
    payload: dict[str, Any] = {}
    priority: int = 5


@router.get("/status", summary="Estado de todos los servicios integrados")
async def orchestrator_status() -> dict:
    """
    Devuelve el health check de todos los servicios integrados:
    Mistral, SABIONDA, GaiaChain, IPFS, n8n, Prometheus, ELK, Grafana.

    No requiere autenticación (datos de disponibilidad, sin secretos).
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
        from services.orchestrator.sovereign_orchestrator import CastouSovereignOrchestrator
        orch = CastouSovereignOrchestrator()
        health = await orch.health_check_all()
        summary = orch.get_system_summary(health)
        await orch.close()
        return {
            "status": "ok",
            "summary": summary,
            "services": {
                name: {
                    "status": r.status,
                    "latency_ms": r.latency_ms,
                    "checked_at": r.checked_at,
                    "error": r.error,
                }
                for name, r in health.items()
            },
        }
    except Exception as exc:
        # Config missing (dev env without services) — return degraded status
        return {
            "status": "degraded",
            "detail": str(exc),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


@router.post("/task", summary="Ejecutar tarea orquestada")
async def run_task(req: TaskRequest) -> dict:
    """
    Ejecuta una tarea a través del orquestador central.

    task_type: ai_inference | blockchain_register | qr_generate |
               workflow_trigger | iot_alert | document_generate
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
        from services.orchestrator.sovereign_orchestrator import (
            CastouSovereignOrchestrator,
            OrchestratorTask,
        )
        task = OrchestratorTask(
            task_id=str(uuid.uuid4()),
            task_type=req.task_type,
            payload=req.payload,
            priority=req.priority,
        )
        orch = CastouSovereignOrchestrator()
        result = await orch.route_task(task)
        await orch.close()
        return result
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
