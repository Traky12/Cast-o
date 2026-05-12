from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from security.rbac import authorize_token, token_from_authorization_header
    from security.sabionda_governance import (
        IncidenceReport,
        IncidenceSeverity,
        IncidenceType,
        sabionda,
    )
    from metrics.prometheus import (
        record_holo_haptics_command,
        record_holo_render,
        record_holo_tracking_frame,
        set_holo_active_sessions,
    )
except ModuleNotFoundError:  # pragma: no cover
    from api.security.rbac import authorize_token, token_from_authorization_header
    from api.security.sabionda_governance import (
        IncidenceReport,
        IncidenceSeverity,
        IncidenceType,
        sabionda,
    )
    from api.metrics.prometheus import (
        record_holo_haptics_command,
        record_holo_render,
        record_holo_tracking_frame,
        set_holo_active_sessions,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/holo", tags=["HoloPy + Ultraleap Sovereign"])

_PRIVILEGED_ROLES = {
    "admin_general",
    "administrador",
    "ciso",
    "cumplimiento",
    "devops",
}

_HISTORY_LIMIT = 200

_TRACKING_FRAMES: dict[str, list[dict[str, Any]]] = {}
_HAPTIC_COMMANDS: dict[str, list[dict[str, Any]]] = {}
_HOLO_RENDERS: dict[str, list[dict[str, Any]]] = {}


def _runtime_env() -> str:
    return os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _require_privileged_access(authorization: str | None, operation: str) -> None:
    if _runtime_env() != "production":
        return
    token = token_from_authorization_header(authorization)
    if not token:
        raise HTTPException(
            status_code=401,
            detail=f"Authorization Bearer requerido para {operation}",
        )
    authorize_token(token, _PRIVILEGED_ROLES)


def _require_integration_enabled(flag_name: str, integration_name: str) -> None:
    if _runtime_env() != "production":
        return
    if not _env_flag_enabled(flag_name, default=False):
        raise HTTPException(
            status_code=503,
            detail=f"Integracion {integration_name} deshabilitada por politica",
        )


def _append_limited(target: dict[str, list[dict[str, Any]]], key: str, item: dict[str, Any]) -> None:
    if key not in target:
        target[key] = []
    target[key].append(item)
    if len(target[key]) > _HISTORY_LIMIT:
        target[key] = target[key][-_HISTORY_LIMIT:]


def _refresh_active_sessions_metric() -> None:
    active_farms = set(_HOLO_RENDERS) | set(_TRACKING_FRAMES) | set(_HAPTIC_COMMANDS)
    set_holo_active_sessions(len(active_farms))


def _build_sabionda_context(farm_id: str) -> dict[str, Any]:
    renders = _HOLO_RENDERS.get(farm_id, [])
    tracking = _TRACKING_FRAMES.get(farm_id, [])
    haptics = _HAPTIC_COMMANDS.get(farm_id, [])

    readiness = 0.0
    readiness += 0.34 if renders else 0.0
    readiness += 0.33 if tracking else 0.0
    readiness += 0.33 if haptics else 0.0
    last_confidence = float(tracking[-1].get("confidence", 0.0)) if tracking else 0.0
    if tracking:
        readiness *= max(0.4, min(1.0, last_confidence + 0.2))

    severity = IncidenceSeverity.INFO
    incident_type = IncidenceType.UNKNOWN
    if readiness < 0.35:
        severity = IncidenceSeverity.CRITICAL
        incident_type = IncidenceType.SENSOR_FAILURE
    elif readiness < 0.7:
        severity = IncidenceSeverity.WARNING
        incident_type = IncidenceType.NETWORK_LOSS

    recommended_action = (
        "Mantener operacion actual y continuar monitorizacion"
        if severity == IncidenceSeverity.INFO
        else "Revisar tracking/haptics y reintentar calibracion"
        if severity == IncidenceSeverity.WARNING
        else "Escalar a Sabionda y activar protocolo de contingencia"
    )

    return {
        "farm_id": farm_id,
        "severity": severity.value,
        "incident_type": incident_type.value,
        "recommended_action": recommended_action,
        "metrics": {
            "renders_total": len(renders),
            "tracking_frames_total": len(tracking),
            "haptics_commands_total": len(haptics),
            "last_tracking_confidence": last_confidence,
            "readiness_score": round(readiness, 3),
        },
    }


def _holopy_engine() -> dict[str, Any]:
    try:
        import holopy  # type: ignore

        return {
            "name": "holopy",
            "available": True,
            "version": getattr(holopy, "__version__", "unknown"),
            "runtime": "python",
        }
    except Exception:
        return {
            "name": "holopy",
            "available": False,
            "version": "not-installed",
            "runtime": "simulation",
        }


def _ultraleap_engine() -> dict[str, Any]:
    try:
        import ultraleap  # type: ignore

        return {
            "name": "ultraleap",
            "available": True,
            "version": getattr(ultraleap, "__version__", "unknown"),
        }
    except Exception:
        return {
            "name": "ultraleap",
            "available": False,
            "version": "not-installed",
        }


class HoloRenderRequest(BaseModel):
    farm_id: str = Field(..., min_length=3, max_length=120)
    prototype_id: int = Field(..., ge=1)
    scene: str = Field(..., min_length=3, max_length=100)
    sensor_data: dict[str, float] = Field(default_factory=dict)


class TrackingFrameRequest(BaseModel):
    farm_id: str = Field(..., min_length=3, max_length=120)
    device_id: str = Field(..., min_length=3, max_length=120)
    hand_present: bool = True
    gesture: str = Field(default="unknown", max_length=120)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    position: dict[str, float] | None = None


class HapticsPulseRequest(BaseModel):
    farm_id: str = Field(..., min_length=3, max_length=120)
    device_id: str = Field(..., min_length=3, max_length=120)
    intensity: float = Field(..., ge=0.0, le=1.0)
    frequency_hz: float = Field(..., ge=20.0, le=500.0)
    duration_ms: int = Field(..., ge=20, le=2000)
    pattern: str = Field(default="short_confirm", max_length=80)


@router.post("/render")
async def render_hologram(
    request: HoloRenderRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_privileged_access(authorization, "holographic render")
    _require_integration_enabled("ENABLE_HOLOPY_INTEGRATION", "HoloPy")

    engine = _holopy_engine()
    render_id = str(uuid.uuid4())[:12]
    render_event = {
        "render_id": render_id,
        "farm_id": request.farm_id,
        "prototype_id": request.prototype_id,
        "scene": request.scene,
        "points": max(5000, len(request.sensor_data) * 3500),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_limited(_HOLO_RENDERS, request.farm_id, render_event)
    record_holo_render(request.farm_id, request.scene)
    _refresh_active_sessions_metric()

    return {
        "status": "ok",
        "farm_id": request.farm_id,
        "render": render_event,
        "engine": engine,
        "sovereignty": {
            "region": "EU",
            "compute": "Hetzner-DE",
            "ai": "Mistral-France",
            "policy": "gdpr-eu-ai-act",
        },
    }


@router.post("/tracking/frame")
async def register_tracking_frame(
    request: TrackingFrameRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_privileged_access(authorization, "ultraleap tracking")
    _require_integration_enabled("ENABLE_ULTRALEAP_INTEGRATION", "Ultraleap")

    engine = _ultraleap_engine()
    frame = {
        "frame_id": str(uuid.uuid4())[:12],
        "device_id": request.device_id,
        "hand_present": request.hand_present,
        "gesture": request.gesture,
        "confidence": request.confidence,
        "position": request.position,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_limited(_TRACKING_FRAMES, request.farm_id, frame)
    record_holo_tracking_frame(request.farm_id, request.gesture)
    _refresh_active_sessions_metric()
    return {
        "status": "captured",
        "farm_id": request.farm_id,
        "frame": frame,
        "engine": engine,
    }


@router.post("/haptics/pulse")
async def trigger_haptic_pulse(
    request: HapticsPulseRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_privileged_access(authorization, "ultraleap haptics")
    _require_integration_enabled("ENABLE_ULTRALEAP_INTEGRATION", "Ultraleap")

    command = {
        "command_id": str(uuid.uuid4())[:12],
        "device_id": request.device_id,
        "intensity": request.intensity,
        "frequency_hz": request.frequency_hz,
        "duration_ms": request.duration_ms,
        "pattern": request.pattern,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _append_limited(_HAPTIC_COMMANDS, request.farm_id, command)
    record_holo_haptics_command(request.farm_id, request.pattern)
    _refresh_active_sessions_metric()
    return {
        "status": "scheduled",
        "farm_id": request.farm_id,
        "haptics": command,
    }


@router.get("/session/{farm_id}")
async def get_session_status(farm_id: str) -> dict[str, Any]:
    renders = _HOLO_RENDERS.get(farm_id, [])
    tracking = _TRACKING_FRAMES.get(farm_id, [])
    haptics = _HAPTIC_COMMANDS.get(farm_id, [])
    return {
        "farm_id": farm_id,
        "system_ready": bool(renders and tracking and haptics),
        "holography": {
            "renders_total": len(renders),
            "last_render": renders[-1] if renders else None,
        },
        "tracking": {
            "frames_total": len(tracking),
            "last_frame": tracking[-1] if tracking else None,
        },
        "haptics": {
            "commands_total": len(haptics),
            "last_command": haptics[-1] if haptics else None,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health")
async def integration_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "holopy": _holopy_engine(),
        "ultraleap": _ultraleap_engine(),
        "region": "EU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/sabionda/{farm_id}/context")
async def sabionda_context_from_holo_metrics(farm_id: str) -> dict[str, Any]:
    context = _build_sabionda_context(farm_id)
    return {
        **context,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/sabionda/{farm_id}/escalate")
async def escalate_holo_to_sabionda(
    farm_id: str,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    _require_privileged_access(authorization, "sabionda escalation")

    context = _build_sabionda_context(farm_id)
    severity = IncidenceSeverity(context["severity"])
    incident_type = IncidenceType(context["incident_type"])
    metrics = context["metrics"]

    report = IncidenceReport(
        incident_id=f"holo-{farm_id}-{str(uuid.uuid4())[:8]}",
        prototype=1,
        severity=severity,
        incident_type=incident_type,
        description="Escalado automatico desde metricas holograficas",
        affected_variable="holo_readiness_score",
        current_value=float(metrics["readiness_score"]),
        expected_range=(0.8, 1.0),
        suggested_action=context["recommended_action"],
        operator_id="holo-router",
    )
    decision = sabionda.analyze_incident(report)

    return {
        "status": "escalated",
        "farm_id": farm_id,
        "severity": severity.value,
        "decision": decision.decision,
        "confidence": decision.confidence,
        "requires_human_approval": decision.requires_human_approval,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }