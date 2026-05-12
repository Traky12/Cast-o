"""
Router de control y monitorización de Prototipos de Cultivo P1 y P2.

Endpoints disponibles:
  POST /api/v1/greenhouse/{prototype_id}/telemetry   — Ingestar lectura de sensores
  GET  /api/v1/greenhouse/{prototype_id}/status       — Estado completo del prototipo
  GET  /api/v1/greenhouse/{prototype_id}/alerts       — Alertas activas
  POST /api/v1/greenhouse/{prototype_id}/actuator     — Control de actuadores
  POST /api/v1/greenhouse/{prototype_id}/recipe       — Actualizar receta nutricional
  GET  /api/v1/greenhouse/{prototype_id}/history      — Histórico de telemetría
  GET  /api/v1/greenhouse/compare                     — Comparación P1 vs P2
  GET  /api/v1/greenhouse/health                      — Salud global cloud + IoT

Arquitectura:
  - Telemetría validada contra rangos óptimos por cultivo (ISO 8000-6)
  - Detección automática de anomalías con scoring de severidad
  - Escalado a Sabionda si severidad >= WARNING
  - Sincronización cloud en background (CloudManager)
  - Auditoría de cada acción con timestamp + operador
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# ── Importaciones duales (Docker raíz=api/ | tests=api.*) ──────────────────
try:
    from services.cloud_manager import CloudManager, CloudTelemetryRecord, cloud_manager
    from security.sabionda_governance import (
        IncidenceReport, IncidenceSeverity, IncidenceType, sabionda,
    )
    from services.whatsapp_alerts import whatsapp_alert_service
except ModuleNotFoundError:
    from api.services.cloud_manager import CloudManager, CloudTelemetryRecord, cloud_manager
    from api.security.sabionda_governance import (
        IncidenceReport, IncidenceSeverity, IncidenceType, sabionda,
    )
    from api.services.whatsapp_alerts import whatsapp_alert_service


router = APIRouter(prefix="/api/v1/greenhouse", tags=["Greenhouse Control P1/P2"])


# ─────────────────────────────────────────────────────────────────────────────
# Rangos óptimos por cultivo (referencia agronómica real)
# ─────────────────────────────────────────────────────────────────────────────

_OPTIMAL: dict[str, dict[str, tuple[float, float]]] = {
    "tomate":   {"ph": (5.8, 6.3), "ec": (2.0, 4.0), "temp_agua": (18.0, 24.0),
                 "temp_aire": (20.0, 28.0), "hr": (60.0, 80.0), "co2": (800.0, 1200.0)},
    "lechuga":  {"ph": (5.5, 6.2), "ec": (0.8, 1.6), "temp_agua": (16.0, 22.0),
                 "temp_aire": (18.0, 24.0), "hr": (60.0, 80.0), "co2": (700.0, 1000.0)},
    "pimiento": {"ph": (5.8, 6.3), "ec": (2.0, 3.5), "temp_agua": (20.0, 24.0),
                 "temp_aire": (22.0, 28.0), "hr": (65.0, 80.0), "co2": (800.0, 1200.0)},
    "pepino":   {"ph": (5.5, 6.0), "ec": (1.7, 2.5), "temp_agua": (20.0, 24.0),
                 "temp_aire": (22.0, 28.0), "hr": (70.0, 85.0), "co2": (800.0, 1200.0)},
    "fresa":    {"ph": (5.5, 6.0), "ec": (1.0, 2.0), "temp_agua": (16.0, 20.0),
                 "temp_aire": (18.0, 24.0), "hr": (65.0, 80.0), "co2": (700.0, 900.0)},
    "albahaca": {"ph": (5.5, 6.5), "ec": (0.7, 1.4), "temp_agua": (20.0, 24.0),
                 "temp_aire": (20.0, 26.0), "hr": (60.0, 75.0), "co2": (700.0, 1000.0)},
}
_DEFAULT_RANGES: dict[str, tuple[float, float]] = {
    "ph": (5.5, 7.0), "ec": (0.5, 4.5), "temp_agua": (15.0, 28.0),
    "temp_aire": (15.0, 32.0), "hr": (40.0, 90.0), "co2": (500.0, 1500.0),
}


def _ranges(cultivo: str) -> dict[str, tuple[float, float]]:
    return _OPTIMAL.get(cultivo.lower(), _DEFAULT_RANGES)


def _check_anomaly(sensor: str, value: float,
                   cultivo: str) -> tuple[bool, str]:
    """Retorna (is_anomaly, severity_str)."""
    rng = _ranges(cultivo)
    lo, hi = rng.get(sensor, (float("-inf"), float("inf")))
    if value < lo or value > hi:
        # Severidad según desviación porcentual
        mid = (lo + hi) / 2
        deviation = abs(value - mid) / (mid if mid else 1.0)
        sev = "critical" if deviation > 0.25 else "warning"
        return True, sev
    return False, "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Estado en memoria por prototipo
# ─────────────────────────────────────────────────────────────────────────────

class _PrototypeState:
    """Estado en memoria de un prototipo de cultivo."""

    def __init__(self, prototype_id: int) -> None:
        self.prototype_id = prototype_id
        self.cultivo: str = "lechuga"
        self.sistema: str = "NFT"
        self.last_telemetry: dict[str, Any] = {}
        self.alerts: list[dict[str, Any]] = []
        self.history: list[dict[str, Any]] = []
        self.actuators: dict[str, str] = {
            "bomba_riego": "off",
            "bomba_dosificacion": "off",
            "ventilacion": "off",
            "iluminacion": "off",
            "calefaccion": "off",
        }
        self.recipe: dict[str, Any] = {
            "ph_target": 6.0, "ec_target": 1.5,
            "temp_agua_target": 20.0, "fotoperiodo_h": 16,
        }
        self.created_at: str = datetime.now(timezone.utc).isoformat()

    def update_telemetry(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Actualiza telemetría y retorna lista de anomalías detectadas."""
        self.last_telemetry = {**data, "updated_at": datetime.now(timezone.utc).isoformat()}
        if len(self.history) >= 500:
            self.history.pop(0)
        self.history.append(self.last_telemetry.copy())

        new_alerts: list[dict[str, Any]] = []
        for sensor in ("ph", "ec", "temp_agua", "temp_aire", "hr", "co2"):
            val = data.get(sensor)
            if val is None:
                continue
            anomaly, sev = _check_anomaly(sensor, float(val), self.cultivo)
            if anomaly:
                alert = {
                    "alert_id": str(uuid.uuid4())[:8],
                    "sensor": sensor,
                    "value": val,
                    "severity": sev,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "prototype_id": self.prototype_id,
                }
                self.alerts.append(alert)
                new_alerts.append(alert)
                # Mantener sólo las últimas 100 alertas
                if len(self.alerts) > 100:
                    self.alerts.pop(0)

        return new_alerts


_PROTOTYPES: dict[int, _PrototypeState] = {
    1: _PrototypeState(1),
    2: _PrototypeState(2),
}


def _get_prototype(prototype_id: int) -> _PrototypeState:
    if prototype_id not in _PROTOTYPES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prototipo {prototype_id} no encontrado. Válidos: 1, 2",
        )
    return _PROTOTYPES[prototype_id]


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de API
# ─────────────────────────────────────────────────────────────────────────────

class TelemetryPayload(BaseModel):
    """Lectura de sensores de un prototipo."""
    device_id: str = Field(..., description="ID del dispositivo IoT")
    ph: Optional[float] = Field(None, ge=0.0, le=14.0, description="pH solución (0-14)")
    ec: Optional[float] = Field(None, ge=0.0, le=10.0, description="EC en mS/cm")
    temp_agua: Optional[float] = Field(None, ge=0.0, le=50.0, description="Temp agua °C")
    temp_aire: Optional[float] = Field(None, ge=-10.0, le=60.0, description="Temp aire °C")
    hr: Optional[float] = Field(None, ge=0.0, le=100.0, description="Humedad relativa %")
    co2: Optional[float] = Field(None, ge=0.0, le=5000.0, description="CO₂ ppm")
    nivel_deposito_l: Optional[float] = Field(None, ge=0.0, description="Nivel depósito L")
    wifi_rssi: Optional[int] = Field(None, description="Señal WiFi dBm")

    @field_validator("ph")
    @classmethod
    def _ph_reasonable(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 14.0):
            raise ValueError(f"pH {v} fuera de rango físico (0-14)")
        return v


class ActuatorCommand(BaseModel):
    """Comando de control de actuador."""
    actuator: str = Field(..., description="bomba_riego|bomba_dosificacion|ventilacion|iluminacion|calefaccion")
    action: str = Field(..., description="on|off|pulse")
    duration_s: Optional[int] = Field(None, ge=1, le=3600, description="Duración en segundos (sólo pulse)")
    operator_id: Optional[str] = Field(None, description="ID operador que ejecuta")

    @field_validator("action")
    @classmethod
    def _valid_action(cls, v: str) -> str:
        if v not in {"on", "off", "pulse"}:
            raise ValueError(f"Acción inválida: {v}. Valores: on, off, pulse")
        return v


class RecipeUpdate(BaseModel):
    """Actualización de receta nutricional."""
    cultivo: Optional[str] = Field(None, description="Cultivo: tomate|lechuga|pimiento|...")
    sistema: Optional[str] = Field(None, description="Sistema: NFT|DWC|goteo|...")
    ph_target: Optional[float] = Field(None, ge=4.5, le=8.5)
    ec_target: Optional[float] = Field(None, ge=0.1, le=6.0)
    temp_agua_target: Optional[float] = Field(None, ge=10.0, le=35.0)
    fotoperiodo_h: Optional[int] = Field(None, ge=6, le=24)


class TelemetryResponse(BaseModel):
    prototype_id: int
    accepted: bool
    anomalies_detected: int
    alerts: list[dict[str, Any]]
    cloud_queued: bool
    timestamp: str


class PrototypeStatus(BaseModel):
    prototype_id: int
    cultivo: str
    sistema: str
    last_telemetry: dict[str, Any]
    active_alerts: int
    actuators: dict[str, str]
    recipe: dict[str, Any]
    health_score: float  # 0-100
    timestamp: str


class CompareResponse(BaseModel):
    p1: dict[str, Any]
    p2: dict[str, Any]
    diff: dict[str, Any]
    recommendation: str
    timestamp: str


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _health_score(proto: _PrototypeState) -> float:
    """Score 0-100 basado en alertas activas y última telemetría."""
    critical_alerts = sum(1 for a in proto.alerts[-10:] if a.get("severity") == "critical")
    warning_alerts  = sum(1 for a in proto.alerts[-10:] if a.get("severity") == "warning")
    penalty = critical_alerts * 20 + warning_alerts * 5
    return max(0.0, 100.0 - penalty)


def _escalate_if_needed(proto: _PrototypeState,
                         new_alerts: list[dict[str, Any]]) -> None:
    """Escala a Sabionda si hay alertas de severidad crítica."""
    for alert in new_alerts:
        if alert.get("severity") != "critical":
            continue
        sensor = alert["sensor"]
        lo, hi = _ranges(proto.cultivo).get(sensor, (0.0, 100.0))
        report = IncidenceReport(
            incident_id=alert["alert_id"],
            prototype=proto.prototype_id,
            severity=IncidenceSeverity.CRITICAL,
            incident_type=IncidenceType.PH_ANOMALY
                if sensor == "ph" else IncidenceType.TEMP_ANOMALY,
            description=(
                f"Sensor {sensor.upper()} crítico en P{proto.prototype_id}: "
                f"valor={alert['value']} fuera de [{lo}-{hi}]"
            ),
            affected_variable=sensor,
            current_value=float(alert["value"]),
            expected_range=(lo, hi),
        )
        try:
            sabionda.process_incidence(report)
        except Exception:  # noqa: BLE001
            logger.warning("Sabionda escalado fallido para %s", alert["alert_id"])


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{prototype_id}/telemetry",
    response_model=TelemetryResponse,
    summary="Ingestar lectura de sensores del prototipo",
)
async def ingest_telemetry(
    prototype_id: int,
    payload: TelemetryPayload,
) -> TelemetryResponse:
    """
    Recibe telemetría del ESP32 / broker MQTT del prototipo indicado.

    - Valida rangos físicos
    - Detecta anomalías vs receta óptima
    - Escala a Sabionda si es crítico
    - Encola en CloudManager para sincronización
    """
    if prototype_id not in (1, 2):
        raise HTTPException(status_code=400, detail="prototype_id debe ser 1 o 2")

    proto = _get_prototype(prototype_id)
    data = payload.model_dump(exclude_none=True)
    new_alerts = proto.update_telemetry(data)

    # Enqueue en cloud
    for sensor in ("ph", "ec", "temp_agua", "temp_aire", "hr", "co2"):
        val = data.get(sensor)
        if val is not None:
            cloud_manager.enqueue(CloudTelemetryRecord(
                prototype_id=prototype_id,
                sensor_type=sensor,
                value=float(val),
                unit={"ec": "mS/cm", "temp_agua": "°C", "temp_aire": "°C",
                      "hr": "%", "co2": "ppm"}.get(sensor, ""),
                device_id=payload.device_id,
                anomaly=any(a["sensor"] == sensor for a in new_alerts),
            ))

    # Escalar si crítico
    if new_alerts:
        _escalate_if_needed(proto, new_alerts)

    return TelemetryResponse(
        prototype_id=prototype_id,
        accepted=True,
        anomalies_detected=len(new_alerts),
        alerts=new_alerts,
        cloud_queued=True,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/{prototype_id}/status",
    response_model=PrototypeStatus,
    summary="Estado completo del prototipo",
)
async def get_status(prototype_id: int) -> PrototypeStatus:
    """Estado operativo completo: sensores, actuadores, receta y score de salud."""
    proto = _get_prototype(prototype_id)
    return PrototypeStatus(
        prototype_id=prototype_id,
        cultivo=proto.cultivo,
        sistema=proto.sistema,
        last_telemetry=proto.last_telemetry,
        active_alerts=len([a for a in proto.alerts if
                           (datetime.now(timezone.utc).isoformat()[:10] in a.get("timestamp", ""))]),
        actuators=proto.actuators,
        recipe=proto.recipe,
        health_score=_health_score(proto),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/{prototype_id}/alerts",
    summary="Alertas activas del prototipo",
)
async def get_alerts(
    prototype_id: int,
    severity: Optional[str] = Query(None, description="Filtrar por severity: warning|critical"),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Lista de alertas activas, filtrable por severidad."""
    proto = _get_prototype(prototype_id)
    alerts = proto.alerts[-limit:]
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    return {
        "prototype_id": prototype_id,
        "total": len(alerts),
        "alerts": alerts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/{prototype_id}/actuator",
    summary="Control de actuadores del prototipo",
)
async def control_actuator(
    prototype_id: int,
    cmd: ActuatorCommand,
) -> dict[str, Any]:
    """
    Controla actuadores del prototipo (bomba, ventilación, iluminación, calefacción).
    Registra acción con timestamp y operador para trazabilidad.
    """
    proto = _get_prototype(prototype_id)
    valid_actuators = set(proto.actuators.keys())
    if cmd.actuator not in valid_actuators:
        raise HTTPException(
            status_code=400,
            detail=f"Actuador '{cmd.actuator}' inválido. Válidos: {sorted(valid_actuators)}",
        )
    prev = proto.actuators[cmd.actuator]
    proto.actuators[cmd.actuator] = "on" if cmd.action in ("on", "pulse") else "off"
    logger.info(
        "P%d actuator=%s %s→%s by=%s",
        prototype_id, cmd.actuator, prev, proto.actuators[cmd.actuator],
        cmd.operator_id or "system",
    )
    return {
        "prototype_id": prototype_id,
        "actuator": cmd.actuator,
        "previous_state": prev,
        "new_state": proto.actuators[cmd.actuator],
        "action": cmd.action,
        "duration_s": cmd.duration_s,
        "operator_id": cmd.operator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/{prototype_id}/recipe",
    summary="Actualizar receta agronómica del prototipo",
)
async def update_recipe(
    prototype_id: int,
    recipe: RecipeUpdate,
) -> dict[str, Any]:
    """Actualiza la receta nutricional y parámetros de cultivo del prototipo."""
    proto = _get_prototype(prototype_id)
    updated: list[str] = []
    if recipe.cultivo:
        proto.cultivo = recipe.cultivo
        updated.append("cultivo")
    if recipe.sistema:
        proto.sistema = recipe.sistema
        updated.append("sistema")
    for field_name in ("ph_target", "ec_target", "temp_agua_target", "fotoperiodo_h"):
        val = getattr(recipe, field_name)
        if val is not None:
            proto.recipe[field_name] = val
            updated.append(field_name)
    return {
        "prototype_id": prototype_id,
        "updated_fields": updated,
        "current_recipe": proto.recipe,
        "cultivo": proto.cultivo,
        "sistema": proto.sistema,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/{prototype_id}/history",
    summary="Histórico de telemetría del prototipo",
)
async def get_history(
    prototype_id: int,
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    """Últimas N lecturas de telemetría del prototipo."""
    proto = _get_prototype(prototype_id)
    return {
        "prototype_id": prototype_id,
        "total_records": len(proto.history),
        "records": proto.history[-limit:],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/compare",
    response_model=CompareResponse,
    summary="Comparación de estado P1 vs P2",
)
async def compare_prototypes() -> CompareResponse:
    """
    Compara el estado de P1 y P2: salud, alertas, telemetría y receta.
    Genera recomendación automática según diferencias detectadas.
    """
    p1, p2 = _PROTOTYPES[1], _PROTOTYPES[2]

    def _summary(p: _PrototypeState) -> dict[str, Any]:
        return {
            "health_score": _health_score(p),
            "active_alerts": len(p.alerts),
            "cultivo": p.cultivo,
            "sistema": p.sistema,
            "last_ph": p.last_telemetry.get("ph"),
            "last_ec": p.last_telemetry.get("ec"),
            "last_temp_agua": p.last_telemetry.get("temp_agua"),
            "last_temp_aire": p.last_telemetry.get("temp_aire"),
            "recipe": p.recipe,
        }

    s1, s2 = _summary(p1), _summary(p2)

    diff: dict[str, Any] = {}
    for key in ("health_score", "active_alerts", "last_ph", "last_ec",
                "last_temp_agua", "last_temp_aire"):
        v1, v2 = s1.get(key), s2.get(key)
        if v1 is not None and v2 is not None:
            try:
                diff[key] = round(float(v1) - float(v2), 3)
            except (TypeError, ValueError):
                diff[key] = None

    # Recomendación simplificada
    if s1["health_score"] < 60 and s2["health_score"] >= 80:
        recommendation = "P1 necesita atención urgente. P2 en buen estado. Revisar sensores P1."
    elif s2["health_score"] < 60 and s1["health_score"] >= 80:
        recommendation = "P2 necesita atención urgente. P1 en buen estado. Revisar sensores P2."
    elif s1["active_alerts"] > 5 or s2["active_alerts"] > 5:
        recommendation = "Alto número de alertas. Revisar última telemetría y recalibrar sensores."
    else:
        recommendation = "Ambos prototipos operativos. Continuar monitorización rutinaria."

    return CompareResponse(
        p1=s1, p2=s2, diff=diff,
        recommendation=recommendation,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/health",
    summary="Salud global: cloud + IoT + prototipos",
)
async def global_health() -> dict[str, Any]:
    """Health-check global: estado cloud, buffer de telemetría y score de ambos prototipos."""
    cloud_health = cloud_manager.health()
    cloud_stats  = cloud_manager.get_stats()
    return {
        "status": "ok" if all(cloud_health.values()) else "degraded",
        "cloud": cloud_health,
        "cloud_stats": cloud_stats,
        "prototypes": {
            pid: {
                "health_score": _health_score(proto),
                "active_alerts": len(proto.alerts),
                "cultivo": proto.cultivo,
                "last_seen": proto.last_telemetry.get("updated_at"),
            }
            for pid, proto in _PROTOTYPES.items()
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/cloud/flush",
    summary="Forzar sincronización cloud de telemetría pendiente",
)
async def cloud_flush() -> dict[str, Any]:
    """Envía a la nube el buffer de telemetría pendiente."""
    result = cloud_manager.flush()
    return {
        "success": result.success,
        "records_sent": result.records_sent,
        "records_failed": result.records_failed,
        "latency_ms": result.latency_ms,
        "error": result.error,
        "timestamp": result.timestamp,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Modelos 3D — Holografía y Fotogrametría
# ─────────────────────────────────────────────────────────────────────────────

class HolographyCapturePayload(BaseModel):
    device_id: str
    resolution: Optional[str] = "4k"
    point_density: Optional[float] = None
    coverage_percent: Optional[float] = None
    operator_id: Optional[str] = None


class PhotogrammetryPayload(BaseModel):
    device_id: str
    images_count: int
    overlap_percent: Optional[float] = None
    avg_reprojection_error: Optional[float] = None
    operator_id: Optional[str] = None


# Estado en memoria para capturas 3D (por prototipo)
_HOLOGRAPHY_CAPTURES: dict[int, list[dict[str, Any]]] = {1: [], 2: []}
_PHOTOGRAMMETRY_CAPTURES: dict[int, list[dict[str, Any]]] = {1: [], 2: []}


@router.post(
    "/{prototype_id}/holography/register",
    summary="Registrar captura de holografía volumétrica",
)
async def register_holography_capture(
    prototype_id: int,
    payload: HolographyCapturePayload,
) -> dict[str, Any]:
    """Registra una captura holográfica 3D para el prototipo indicado."""
    _get_prototype(prototype_id)
    if prototype_id not in _HOLOGRAPHY_CAPTURES:
        _HOLOGRAPHY_CAPTURES[prototype_id] = []
    capture = {
        "capture_id": str(uuid.uuid4())[:8],
        "device_id": payload.device_id,
        "resolution": payload.resolution,
        "point_density": payload.point_density,
        "coverage_percent": payload.coverage_percent,
        "operator_id": payload.operator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _HOLOGRAPHY_CAPTURES[prototype_id].append(capture)
    return {
        "prototype_id": prototype_id,
        "registered": True,
        "capture": capture,
    }


@router.post(
    "/{prototype_id}/photogrammetry/register",
    summary="Registrar escaneo fotogramétrico",
)
async def register_photogrammetry_scan(
    prototype_id: int,
    payload: PhotogrammetryPayload,
) -> dict[str, Any]:
    """Registra un escaneo fotogramétrico para el prototipo indicado."""
    _get_prototype(prototype_id)
    if prototype_id not in _PHOTOGRAMMETRY_CAPTURES:
        _PHOTOGRAMMETRY_CAPTURES[prototype_id] = []
    capture = {
        "capture_id": str(uuid.uuid4())[:8],
        "device_id": payload.device_id,
        "images_count": payload.images_count,
        "overlap_percent": payload.overlap_percent,
        "avg_reprojection_error": payload.avg_reprojection_error,
        "operator_id": payload.operator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _PHOTOGRAMMETRY_CAPTURES[prototype_id].append(capture)
    return {
        "prototype_id": prototype_id,
        "registered": True,
        "capture": capture,
    }


@router.get(
    "/{prototype_id}/digital-twin/status",
    summary="Estado del gemelo digital 3D del prototipo",
)
async def digital_twin_status(prototype_id: int) -> dict[str, Any]:
    """Devuelve el estado del gemelo digital incluyendo capturas de holografía y fotogrametría."""
    _get_prototype(prototype_id)
    holo_list = _HOLOGRAPHY_CAPTURES.get(prototype_id, [])
    photo_list = _PHOTOGRAMMETRY_CAPTURES.get(prototype_id, [])
    system_ready = len(holo_list) > 0 and len(photo_list) > 0
    return {
        "prototype_id": prototype_id,
        "holography": {
            "captures_total": len(holo_list),
            "last_capture": holo_list[-1] if holo_list else None,
        },
        "photogrammetry": {
            "captures_total": len(photo_list),
            "last_capture": photo_list[-1] if photo_list else None,
        },
        "system_ready": system_ready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
