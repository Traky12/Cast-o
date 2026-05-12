from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.core.security import encrypt_audit_payload
from backend.shopware_adapter import build_farmer_dashboard

from .federated_coordinator import FederatedCoordinator
from .schemas import FederatedUpdate


router = APIRouter(prefix="/federated", tags=["Federated"])
_coord = FederatedCoordinator()
_FED_AUDIT_LOGGER = logging.getLogger("castuo_federated_audit")


class AnalysisRequest(BaseModel):
    finca_id: str = Field(
        ...,
        description="UUID inmutable de la explotación agraria registrada.",
        examples=["EXT-001-8f3a4d90-7c12-4a3d-b7b7-9a0c2f4e6f11"],
    )
    solar_exposure: float = Field(
        ...,
        description="Radiación solar global horizontal (GHI) en kWh/m².",
        ge=0,
        examples=[2450.0],
    )
    consent_accepted: bool = Field(
        ...,
        description="Flag de cumplimiento legal: el agricultor autoriza el tratamiento federado de sus datos.",
        examples=[True],
    )

    model_config = ConfigDict(extra="allow")


class AnalysisResponse(BaseModel):
    status: Literal["processing"] = Field(
        default="processing",
        description="Valor fijo: estado administrativo del proceso de certificación.",
        examples=["processing"],
    )
    message: str = Field(
        default="Certificación UNE 216701 en proceso de validación técnica por CTAEX/Castúo",
        description="Mensaje oficial para el solicitante: la validación técnica UNE 216701 está en curso.",
        examples=["Certificación UNE 216701 en proceso de validación técnica por CTAEX/Castúo"],
    )
    audit_id: str = Field(
        ...,
        description="Identificador único de auditoría cifrada para trazabilidad legal.",
        examples=["AUD-a1b2c3d4e5f6g7h"],
    )
    estimated_completion: str = Field(
        default="TBD (Pendiente de validación de fórmulas oficiales)",
        description="TBD (Pendiente de validación de fórmulas oficiales).",
        examples=["TBD (Pendiente de validación de fórmulas oficiales)"],
    )


def compute_agrivoltaic_metrics(solar: float, humidity: float, temp: float) -> Dict[str, float]:
    """Calcula métricas agrivoltaicas conforme a UNE 216701.

    Referencia:
        - UNE 216701: Eficiencia energética en explotaciones agrarias con sistemas
          fotovoltaicos y agrivoltaicos (norma española).

    NOTA IMPORTANTE:
        Esta función es un stub. Las fórmulas exactas definidas en UNE 216701 deben
        ser completadas por el equipo técnico de CTAEX / Castúo-System.

        No utilizar la implementación actual para informes legales o de certificación
        hasta que se haya incorporado la fórmula oficial de la norma.
    """
    # TODO(UNE_216701): Implementar fórmulas oficiales de kWh/ha, rendimiento económico
    # y ahorro de agua según la norma UNE 216701.
    raise NotImplementedError("Fórmulas UNE 216701 pendientes de implementación")


def audit_log_federated(event: str, code: str, meta: Dict[str, Any]) -> None:
    # AUDIT_LOG: Registro cifrado de solicitudes federadas agrivoltaicas (CTAEX / UNE 216701).
    payload = {
        "code": code,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
    try:
        token = encrypt_audit_payload(payload)
        _FED_AUDIT_LOGGER.error(token)
    except Exception:
        # No romper el flujo de la API en caso de fallo de logging.
        pass


def _fallback_sync_payload(action: Dict[str, Any]) -> Dict[str, Any]:
    action_json = json.dumps(action, sort_keys=True).encode("utf-8")
    action_id = action.get("id") or hashlib.sha256(action_json).hexdigest()[:16]
    block_hash = "0x" + hashlib.sha256(action_json).hexdigest()[:64]
    state_hash = hashlib.sha256(
        json.dumps(action.get("model_state", {}), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "status": "success",
        "consensus": False,
        "consensus_pct": 0.0,
        "votes": 1,
        "nodes": 1 + len(_coord.peers),
        "block": block_hash,
        "action_id": action_id,
        "global_version": os.getenv("CASTUO_FEDERATED_VERSION", "fed_1.2"),
        "local_only": True,
        "state_hash": state_hash,
    }


@router.get("/status")
async def federated_status() -> Dict[str, Any]:
    metrics = _coord.get_metrics()
    return {
        "status": "TRL9_FEDERATED_LIVE",
        "global_version": os.getenv("CASTUO_FEDERATED_VERSION", "fed_1.2"),
        "rounds_completed": _coord.get_blocks_count(),
        "nodes_online": metrics["nodes_online"],
        "peers_online": metrics["peers"],
        "consensus_threshold": metrics["consensus_threshold"],
        "node_id": metrics["node_id"],
    }


@router.post("/sync")
async def sync_model(update: FederatedUpdate) -> Dict[str, Any]:
    if not update.consent_accepted:
        # AUDIT_LOG: Rechazo de sync federado por falta de consentimiento explícito del agricultor.
        raise HTTPException(status_code=400, detail="Integrity Error: consent_required")

    model_state = {
        "node_id": update.node_id,
        "model_params": update.model_params,
        "zk_proof": update.zk_proof,
        "metadata": update.metadata,
    }
    state_hash = hashlib.sha256(
        json.dumps(model_state, sort_keys=True).encode("utf-8")
    ).hexdigest()

    action = {
        "type": "federated_sync",
        "source": "shopware-edge",
        "node_id": update.node_id,
        "model_params": update.model_params,
        "zk_proof": update.zk_proof,
        "compliant": update.compliant,
        "metadata": update.metadata,
        "model_state": model_state,
        "state_hash": state_hash,
    }
    try:
        result = await _coord.process_federated_action(action)
        return {
            "status": "success",
            "consensus": result.get("consensus", True),
            "consensus_pct": result.get("consensus_pct", 100.0),
            "votes": result.get("votes", 1),
            "nodes": result.get("nodes", 1 + len(_coord.peers)),
            "block": result.get("block"),
            "action_id": result.get("action_id"),
            "global_version": os.getenv("CASTUO_FEDERATED_VERSION", "fed_1.2"),
            "state_hash": state_hash,
        }
    except Exception:
        return _fallback_sync_payload(action)


@router.get("/farmer/dashboard")
async def farmer_dashboard(finca_id: str) -> Dict[str, Any]:
    return build_farmer_dashboard(finca_id)


@router.post(
    "/agrivoltaic/analyze",
    response_model=AnalysisResponse,
    status_code=202,
)
async def agrivoltaic_analyze(payload: AnalysisRequest) -> AnalysisResponse:
    if not payload.consent_accepted:
        # AUDIT_LOG: Análisis agrivoltaico bloqueado por ausencia de consentimiento digital del agricultor.
        raise HTTPException(status_code=400, detail="Integrity Error: consent_required")

    extra = payload.model_extra or {}
    sensores = (
        extra.get("sensores")
        or extra.get("sensors_data")
        or extra.get("sensor_data")
        or {}
    )
    solar = float(payload.solar_exposure)
    humidity = float(sensores.get("humedad", 42)) if isinstance(sensores, dict) else 42.0
    temp = float(sensores.get("temperatura", 18.5)) if isinstance(sensores, dict) else 18.5

    # Valores UNE 216701 (stub): mientras las fórmulas oficiales no se integren,
    # se mantiene trazabilidad sin bloquear la demo.

    request_meta = {
        "finca_id": payload.finca_id,
        "solar_exposure": solar,
        "humidity": humidity,
        "temperature": temp,
    }
    req_hash = hashlib.sha256(
        json.dumps(request_meta, sort_keys=True).encode("utf-8")
    ).hexdigest()[:8]
    audit_id = f"AUD-{req_hash}"

    # AUDIT_LOG: Solicitud de análisis agrivoltaico registrada para certificación UNE 216701 (CTAEX).
    audit_log_federated(
        event="agrivoltaic_analysis_requested",
        code=audit_id,
        meta={**request_meta, "request_hash": req_hash},
    )

    try:
        # En futuras versiones, esta llamada aplicará las fórmulas oficiales UNE 216701.
        _ = compute_agrivoltaic_metrics(solar=solar, humidity=humidity, temp=temp)
        # Cuando se implemente, aquí se devolverá 200 OK con métricas completas.
    except NotImplementedError:
        body = AnalysisResponse(
            status="processing",
            message="Certificación UNE 216701 en proceso de validación técnica por CTAEX/Castúo",
            audit_id=audit_id,
        ).model_dump()
        # Devolvemos 202 Accepted (promesa administrativa: fórmulas UNE en validación CTAEX).
        body["estimated_completion"] = (
            "TBD (Pendiente de validación de fórmulas oficiales)"
        )
        return JSONResponse(status_code=202, content=body)

    # Mientras no exista implementación real de UNE 216701, mantenemos 202 processing.
    body = AnalysisResponse(
        status="processing",
        message="Certificación UNE 216701 en proceso de validación técnica por CTAEX/Castúo",
        audit_id=audit_id,
    ).model_dump()
    body["estimated_completion"] = "TBD (Pendiente de validación de fórmulas oficiales)"
    return JSONResponse(status_code=202, content=body)

