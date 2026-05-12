# backend/agents/anytype_webhook.py
"""Anytype (Países Bajos) ↔ JSON API → Agentes IA → Sistemas CASTÚO. Webhook /api/anytype."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union

from fastapi import APIRouter
from pydantic import BaseModel

try:
    from . import agente_auditoria, agente_campo, agente_monitoreo, agente_vault
except ImportError:
    import agente_auditoria
    import agente_campo
    import agente_monitoreo
    import agente_vault

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Anytype IA"])

DATA_DIR = Path(os.getenv("AGENTS_DATA_DIR", "backend/agents/data"))


class AnytypeObject(BaseModel):
    """Objeto Anytype exportado (Certificación, Endpoint, Vault Key, Cliente)."""
    id: str = ""
    type: str = ""
    name: str = ""
    properties: Dict[str, Any] = {}
    relations: List[str] = []
    updated: datetime | None = None


class AgentTrigger(BaseModel):
    """Registro de agente disparado."""
    agent: str
    action: str
    triggered_at: datetime


def _save_audit_trail(payload: Dict[str, Any]) -> str:
    """Guarda JSON audit trail en backend/agents/data."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DATA_DIR / f"anytype_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str, ensure_ascii=False)
    return str(path)


@router.post("/anytype")
@router.post("/anytype/webhook")
async def anytype_sync(data: Union[dict, AnytypeObject]) -> Dict[str, Any]:
    """
    Recibe export JSON de objetos Anytype (Certificación, Endpoint, Vault Key, Cliente).
    Dispara agentes según tipo y umbrales. Guarda audit trail en backend/agents/data.
    """
    if isinstance(data, AnytypeObject):
        o = data
        data = {"id": o.id, "type": o.type, "name": o.name, "relations": o.relations or [], "updated": o.updated}
        data.update(o.properties or {})
    if data.get("updated") and hasattr(data["updated"], "isoformat"):
        data["updated"] = data["updated"].isoformat()
    obj_type = data.get("type") or data.get("objectType") or ""
    agents_triggered: List[str] = []
    results: Dict[str, Any] = {}

    if obj_type == "Certificación":
        progress = data.get("progress") or data.get("percentage") or data.get("92%")
        if progress is None and "stage1" in data:
            progress = 92.0
        r = agente_auditoria.alert_stage2(progress=progress, context=data)
        if r.get("triggered"):
            agents_triggered.append("AGENTE_AUDITOR")
        results["auditoria"] = r

    if obj_type == "Vault Key" or (obj_type == "Clave PQC" or "kyber" in str(data).lower()):
        days_left = data.get("days_left") or data.get("rotation_days_left") or data.get("daysToRotation", 28)
        r = agente_vault.rotate_kyber768(days_left=days_left, context=data)
        if r.get("triggered"):
            agents_triggered.append("AGENTE_VAULT")
        results["vault"] = r

    if obj_type == "Endpoint" or "localhost:8000" in str(data.get("url", "")):
        metrics = data.get("metrics") or agente_monitoreo.get_docker_metrics()
        uptime = metrics.get("uptime_pct") or metrics.get("uptime") or 99.9
        r = agente_monitoreo.check_uptime_and_alert(uptime_pct=uptime, metrics=metrics)
        if r.get("triggered"):
            agents_triggered.append("AGENTE_MONITOREO")
        results["monitoreo"] = r

    if obj_type == "Cliente" or "Agricultor" in str(data.get("role", "")):
        consent = data.get("consent") or data.get("consent_gdpr")
        consents_pct = 100.0 if consent else data.get("consents_pct", 85.0)
        r = agente_campo.process_consents_and_alert(consents_pct=consents_pct, context=data)
        if r.get("triggered"):
            agents_triggered.append("AGENTE_CAMPO")
        else:
            r = agente_campo.mark_consent_gdpr_ok(
                object_id=data.get("id", ""),
                qr_scanned=data.get("qr") or data.get("qr_scanned", False),
            )
        results["campo"] = r

    payload = {
        "event": "anytype_export",
        "object": data,
        "timestamp": datetime.now().isoformat(),
        "source": "anytype_p2p_sync",
        "agents_triggered": agents_triggered,
        "results": results,
    }
    data_path = _save_audit_trail(payload)

    return {
        "status": "processed",
        "object_type": obj_type,
        "agents_triggered": agents_triggered,
        "agents_triggered_count": len(agents_triggered),
        "results": results,
        "data_path": data_path,
    }


@router.get("/anytype/metrics")
@router.get("/agents/metrics")
async def anytype_agents_metrics() -> Dict[str, Any]:
    """Métricas predeterminadas de los 4 agentes (dashboard LIVE)."""
    monitoreo = agente_monitoreo.get_docker_metrics()
    return {
        "auditoria": {
            "iso_progress": 92,
            "alerts": 0,
            "metric": "ISO_27001%",
            "threshold": agente_auditoria.UMBRAL_CRITICO_PORCENTAJE,
            "action": "email_applus",
        },
        "vault": {
            "kyber_days": 28,
            "rotation_status": "healthy",
            "metric": "Rotación días",
            "threshold": agente_vault.ROTATION_DAYS_UMBRAL,
            "action": "auto_kyber768",
        },
        "monitoreo": {
            "uptime": 99.9,
            "cpu": monitoreo.get("cpu", 23),
            "metric": "Uptime%",
            "threshold": agente_monitoreo.UMBRAL_UPTIME,
            "action": "alert_telegram",
            "current": monitoreo,
        },
        "campo": {
            "consents_gdpr": 92,
            "qr_scanned": 156,
            "metric": "Consents GDPR",
            "threshold": agente_campo.UMBRAL_CONSENTS_PCT,
            "action": "qr_reenvio",
        },
    }
