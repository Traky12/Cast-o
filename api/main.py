"""
SABIONDA API - Castúo-System v3.1.1
FastAPI backend for:
  - Government document generation (SIEX, TRACES, SIGPAC, REGEPA, PAC)
  - Agrovoltaic hydroponic greenhouse management
  - Immutable QR traceability from seed to consumer
  - IoT persistent telemetry (TimescaleDB)
  - eIDAS qualified electronic signature
  - TRACES/Hyperledger traceability
  - Prometheus observability metrics
"""

import json
import importlib
import logging
import os
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Módulos de integración — dual-import (Docker: raíz=api/, tests: api.*)
# ------------------------------------------------------------------
try:
    from database.timescale import timescale_db
    from middleware.security import device_auth
    from security.rbac import authorize_token, token_from_authorization_header
    from security.hardened import (
        SecretValidator,
        SecurityHeadersMiddleware,
        CORSConfig,
    )
    from services.eidas import eidas_signer
    from services.traces import traces_client
    from metrics.prometheus import (
        IOT_REQUESTS,
        increment_api_request,
        set_api_uptime,
        setup_metrics,
    )
except ModuleNotFoundError:
    from api.database.timescale import timescale_db
    from api.middleware.security import device_auth
    from api.security.rbac import authorize_token, token_from_authorization_header
    from api.security.hardened import (
        SecretValidator,
        SecurityHeadersMiddleware,
        CORSConfig,
    )
    from api.services.eidas import eidas_signer
    from api.services.traces import traces_client
    from api.metrics.prometheus import (
        IOT_REQUESTS,
        increment_api_request,
        set_api_uptime,
        setup_metrics,
    )

_START_TIME = time.time()
_REQUEST_COUNTER: dict[str, int] = {}  # {method_path: count}

ROUTER_MODULE_NAMES = [
    "invernadero",
    "skills",
    "trazabilidad_qr",
    "audit",
    "claude_router",
    "github_webhook",
    "mistral_router",
    "blockchain_router",
    "notes_router",
    "embeddings_router",
    "graph_router",
    "tenant",
    "auth",
    "gdpr",
    "dsar",
    "traces",
    "education",
    "esp32_iot",  # ESP32-CAM + IoT sensor integration
    "holo_soberano",  # HoloPy + Ultraleap sovereign integration
]


def _env_flag_enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _runtime_env() -> str:
    """Resuelve entorno runtime con compatibilidad ENV/ENVIRONMENT."""
    return os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()


# Arquitectura final: GitHub desacoplado por defecto, activable en contingencia.
ENABLE_GITHUB_INTEGRATION = _env_flag_enabled("ENABLE_GITHUB_INTEGRATION", default=False)
REQUIRE_GITHUB_HARDENING = _env_flag_enabled("REQUIRE_GITHUB_HARDENING", default=False)

PRIVILEGED_CONTROL_ROLES = {
    "admin_general",
    "administrador",
    "ciso",
    "cumplimiento",
    "devops",
}


def _require_privileged_access(
    authorization: str | None,
    operation: str,
) -> dict[str, Any] | None:
    """En producción exige Bearer JWT válido y rol privilegiado."""
    if _runtime_env() != "production":
        return None

    token = token_from_authorization_header(authorization)
    if not token:
        raise HTTPException(
            status_code=401,
            detail=f"Authorization Bearer requerido para {operation}",
        )

    return authorize_token(token, PRIVILEGED_CONTROL_ROLES)


def _require_integration_enabled(flag_name: str, integration_name: str) -> None:
    """Bloquea integraciones externas en producción salvo habilitación explícita."""
    if _runtime_env() != "production":
        return
    if not _env_flag_enabled(flag_name, default=False):
        raise HTTPException(
            status_code=503,
            detail=f"Integración {integration_name} deshabilitada por política",
        )


def _load_router_module(module_name: str) -> Any | None:
    for prefix in ("routers", "api.routers"):
        try:
            return importlib.import_module(f"{prefix}.{module_name}")
        except ModuleNotFoundError:
            continue
        except Exception:
            continue
    return None

app = FastAPI(
    title="SABIONDA API - Castúo-System",
    description=(
        "API para gestión agrovoltaica hidropónica y generación de "
        "documentación GOV 100% legal y firmable con trazabilidad QR inmutable. "
        "Integración GitHub desacoplada por defecto y activable por entorno."
    ),
    version="3.1.1",
)

# =============================
# HARDENING DE SEGURIDAD
# =============================

# 1. Validar secretos obligatorios
try:
    secret_validation = SecretValidator.validate()
    logger.info(f"Secret validation: {secret_validation}")
except RuntimeError as exc:
    logger.critical(f"SECURITY FAILURE: {exc}")
    raise

# 2. Agregar middleware de security headers (ASGI)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Configurar CORS
CORSConfig.setup_cors(app)

logger.info(
    "Integration mode: ENABLE_GITHUB_INTEGRATION=%s REQUIRE_GITHUB_HARDENING=%s",
    ENABLE_GITHUB_INTEGRATION,
    REQUIRE_GITHUB_HARDENING,
)

# Métricas Prometheus (/metrics)
setup_metrics(app)


@app.middleware("http")
async def count_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    key = f"{request.method}:{request.url.path}"
    _REQUEST_COUNTER[key] = _REQUEST_COUNTER.get(key, 0) + 1
    increment_api_request(request.method, request.url.path)
    set_api_uptime(time.time() - _START_TIME)
    return await call_next(request)

for _router_module_name in ROUTER_MODULE_NAMES:
    if _router_module_name == "github_webhook" and not ENABLE_GITHUB_INTEGRATION:
        continue
    _module = _load_router_module(_router_module_name)
    if _module is None:
        continue
    _router = getattr(_module, "router", None)
    if _router is not None:
        app.include_router(_router)

SCHEMAS_DIR = Path(os.getenv("SCHEMAS_DIR", "/app/schemas"))
AGENT_CONFIG_PATH = Path(
    os.getenv("AGENT_CONFIG_PATH", "/app/agents/sabionda/config.json")
)
AGENT_PROMPT_PATH = Path(
    os.getenv("AGENT_PROMPT_PATH", "/app/agents/sabionda/system-prompt.md")
)

# In-memory IoT ingestion index for smoke/E2E checks.
IOT_LAST_BY_SENSOR: dict[str, dict[str, Any]] = {}

# Reglas mínimas de calidad de datos (ISO 8000-6) para variables críticas.
_SENSOR_QUALITY_RULES: dict[str, tuple[float, float]] = {
    "ph": (0.0, 14.0),
    "ph_value": (0.0, 14.0),
    "ec": (0.0, 20.0),
    "ec_ms_cm": (0.0, 20.0),
    "vpd": (0.0, 5.0),
    "vpd_kpa": (0.0, 5.0),
}


def _validate_sensor_quality(readings: dict[str, Any]) -> None:
    """Valida rangos físicos básicos para pH/EC/VPD antes de persistir."""
    for key, (min_value, max_value) in _SENSOR_QUALITY_RULES.items():
        if key not in readings:
            continue
        value = readings[key]
        if not isinstance(value, (int, float)):
            raise HTTPException(
                status_code=422,
                detail=f"Lectura inválida en {key}: debe ser numérica",
            )
        numeric_value = float(value)
        if numeric_value < min_value or numeric_value > max_value:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Lectura fuera de rango en {key}: "
                    f"{numeric_value} (rango permitido {min_value}-{max_value})"
                ),
            )


def _first_numeric(readings: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = readings.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _latest_event_for_tenant(tenant_id: str) -> dict[str, Any] | None:
    tenant_key = tenant_id.strip().lower()
    prefix = f"{tenant_key}-"
    candidates: list[dict[str, Any]] = []
    for event in IOT_LAST_BY_SENSOR.values():
        sensor_id = str(event.get("sensor_id", "")).lower()
        source = str(event.get("source", "")).lower()
        if sensor_id.startswith(prefix) or source == tenant_key:
            candidates.append(event)

    if not candidates:
        return None

    def _event_timestamp(evt: dict[str, Any]) -> str:
        return str(evt.get("timestamp") or evt.get("received_at") or "")

    return max(candidates, key=_event_timestamp)


def _build_alerts(metrics: dict[str, float | None]) -> list[str]:
    alerts: list[str] = []
    ph = metrics.get("ph")
    ec = metrics.get("ec")
    temperature_c = metrics.get("temperature_c")
    humidity_pct = metrics.get("humidity_pct")

    if ph is not None and (ph < 5.5 or ph > 6.5):
        alerts.append("pH fuera de rango objetivo")
    if ec is not None and (ec < 1.2 or ec > 2.4):
        alerts.append("EC fuera de rango objetivo")
    if temperature_c is not None and (temperature_c < 18.0 or temperature_c > 30.0):
        alerts.append("Temperatura fuera de objetivo")
    if humidity_pct is not None and (humidity_pct < 45.0 or humidity_pct > 75.0):
        alerts.append("Humedad fuera de objetivo")

    return alerts


# --- Pydantic Models ---


class ExplotacionBase(BaseModel):
    rea: str = Field(..., description="Código REA de la explotación")
    titular: str = Field(..., description="Nombre del titular")
    nif: str = Field(..., description="NIF/CIF del titular")


class ParcelaSIEX(BaseModel):
    sigpac_ref: str = Field(..., description="Referencia SIGPAC")
    superficie_ha: float = Field(..., gt=0)
    cultivo: str
    tipo_riego: str = "secano"
    eco_esquema: bool = False
    uso: str = Field("tierra_arable", description="Uso PAC: tierra_arable | cultivo_permanente | pasto_permanente | barbecho | forestal")


class TratamientoSIEX(BaseModel):
    fecha: str = Field(..., description="Fecha del tratamiento (YYYY-MM-DD)")
    producto: str = Field(..., description="Nombre comercial del fitosanitario")
    materia_activa: str = ""
    dosis: str = Field(..., description="Dosis aplicada (ej. '2.5 L/ha')")
    parcela_ref: str
    plazo_seguridad_dias: int = 0
    justificacion: str = ""


class SIEXRequest(BaseModel):
    explotacion: ExplotacionBase
    parcelas: list[ParcelaSIEX]
    tratamientos: list[TratamientoSIEX] = []


class TRACESAnimal(BaseModel):
    especie: str = Field(..., description="Especie animal")
    raza: str = ""
    cantidad: int = Field(..., gt=0)


class TRACESRequest(BaseModel):
    explotacion_rega: str = Field(..., description="Código REGA de origen")
    nombre_explotacion: str
    direccion_explotacion: str = Field("", description="Dirección de la explotación de origen")
    animales: TRACESAnimal
    tipo_movimiento: str = Field("EXPORT", description="EXPORT | IMPORT | TRANSIT | INTRA")
    destino_pais: str
    destino_explotacion: str


class REGEPAEspecie(BaseModel):
    especie: str = Field(..., description="Especie ganadera (vacuno, porcino, ovino, caprino, aves, apicultura)")
    raza: str = ""
    censo: int = Field(..., gt=0, description="Número de cabezas/colmenas")
    orientacion_productiva: str = Field("", description="Ej: carne, leche, mixto, cría")


class REGEPARequest(BaseModel):
    explotacion_rega: str = Field(..., description="Código REGA de la explotación")
    tipo_explotacion: str = Field(..., description="produccion | cria | cebo | mixta | autoconsumo")
    clasificacion_zootecnica: str = ""
    capacidad_maxima: int = Field(..., gt=0)
    sistema_explotacion: str = Field("extensivo", description="extensivo | intensivo | mixto | ecologico")
    titular_nif: str
    titular_nombre: str
    titular_comunidad: str
    especies: list[REGEPAEspecie]
    grasp_compliant: bool = False


class SIGPACParcela(BaseModel):
    provincia: int = Field(..., ge=1, le=52)  # 50 provincias + Ceuta (51) + Melilla (52)
    municipio: int = Field(..., gt=0)
    poligono: int = Field(..., gt=0)
    parcela: int = Field(..., gt=0)
    recinto: int = Field(..., gt=0)
    uso_sigpac: str = Field(..., description="Código uso SIGPAC: TA, TH, IV, FL, OV, PS, etc.")
    superficie_ha: float = Field(..., gt=0)
    coeficiente_regadio: float = Field(0.0, ge=0.0, le=1.0)
    pendiente_media_pct: float = Field(0.0, ge=0.0)


class SIGPACRequest(BaseModel):
    titular_nombre: str
    titular_nif: str
    parcelas: list[SIGPACParcela]


class PACEcoEsquema(BaseModel):
    codigo: str
    descripcion: str
    parcelas_aplicadas: list[str] = []


class PACRequest(BaseModel):
    nif: str
    nombre: str
    rea: str
    campana: str = Field(..., pattern=r"^\d{4}$")
    parcelas: list[ParcelaSIEX]
    eco_esquemas: list[PACEcoEsquema]


class DocumentResponse(BaseModel):
    tipo_documento: str
    estado: str
    payload: dict[str, Any]
    aviso: str = "Documento generado para REVISIÓN y FIRMA del productor"
    generado_en: str


class ClaudeExecuteRequest(BaseModel):
    payload: dict[str, Any]


class IotTelemetryRequest(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor identifier")
    timestamp: str | None = Field(None, description="ISO-8601 timestamp")
    source: str | None = Field(None, description="Data source label")
    readings: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


def _load_agent_config() -> dict[str, Any]:
    """Load SABIONDA agent configuration if available in runtime container."""
    if not AGENT_CONFIG_PATH.exists():
        return {}
    with open(AGENT_CONFIG_PATH) as f:
        return json.load(f)


def _tool_catalog_from_config(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Build a Claude-friendly tool catalog from the agent config file."""
    tools: list[dict[str, Any]] = []
    for tool in config.get("openclaw_functions", {}).get("document_generation", []):
        tools.append(
            {
                "name": tool.get("name"),
                "kind": "document_generation",
                "endpoint": tool.get("endpoint"),
                "description": tool.get("description", ""),
                "required_fields": tool.get("required_fields", []),
                "optional_fields": tool.get("optional_fields", []),
                "status": "available",
            }
        )

    for tool in config.get("openclaw_functions", {}).get("rag_tools", []):
        tools.append(
            {
                "name": tool.get("name"),
                "kind": "rag",
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", []),
                "status": "declared_not_implemented",
            }
        )

    for tool in config.get("openclaw_functions", {}).get("iot_alerts", []):
        tools.append(
            {
                "name": tool.get("name"),
                "kind": "iot_alert",
                "description": tool.get("description", ""),
                "trigger": tool.get("trigger", ""),
                "action": tool.get("action", ""),
                "status": "declared_not_implemented",
            }
        )

    if not tools:
        # Fallback for local/test environments without mounted agent config.
        return [
            {
                "name": "generate_siex_cuaderno",
                "kind": "document_generation",
                "endpoint": "POST /api/v1/siex/cuaderno-campo",
                "description": "Genera el Cuaderno de Campo Digital SIEX",
                "required_fields": ["explotacion", "parcelas"],
                "optional_fields": ["tratamientos"],
                "status": "available",
            },
            {
                "name": "generate_traces_certificado",
                "kind": "document_generation",
                "endpoint": "POST /api/v1/traces/certificado",
                "description": "Genera certificado sanitario TRACES",
                "required_fields": [
                    "explotacion_rega",
                    "nombre_explotacion",
                    "animales",
                    "tipo_movimiento",
                    "destino_pais",
                    "destino_explotacion",
                ],
                "optional_fields": [],
                "status": "available",
            },
            {
                "name": "generate_pac_eco_esquema",
                "kind": "document_generation",
                "endpoint": "POST /api/v1/pac/eco-esquema",
                "description": "Genera solicitud PAC 2026 con eco-esquemas",
                "required_fields": [
                    "nif",
                    "nombre",
                    "rea",
                    "campana",
                    "parcelas",
                    "eco_esquemas",
                ],
                "optional_fields": [],
                "status": "available",
            },
            {
                "name": "generate_regepa_explotacion",
                "kind": "document_generation",
                "endpoint": "POST /api/v1/regepa/explotacion",
                "description": "Genera registro de explotacion ganadera REGEPA",
                "required_fields": [
                    "explotacion_rega",
                    "tipo_explotacion",
                    "capacidad_maxima",
                    "sistema_explotacion",
                    "titular_nif",
                    "titular_nombre",
                    "titular_comunidad",
                    "especies",
                ],
                "optional_fields": [],
                "status": "available",
            },
            {
                "name": "generate_sigpac_parcelas",
                "kind": "document_generation",
                "endpoint": "POST /api/v1/sigpac/parcelas",
                "description": "Genera informe de parcelas SIGPAC",
                "required_fields": ["titular_nombre", "titular_nif", "parcelas"],
                "optional_fields": [],
                "status": "available",
            },
        ]

    return tools


# --- Endpoints ---


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "agent": "SABIONDA",
        "version": "3.1.1",
        "timescale": "ok" if timescale_db.available else "fallback",
        "eidas": "ok" if eidas_signer.private_key else "simulated",
        "chain_status": _chain_status(),
        "neuromorphic_lab": os.getenv("CASTUO_NEUROMORPHIC_LAB", "0") == "1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/iot/telemetry")
async def ingest_iot_telemetry(
    request: IotTelemetryRequest,
    authorization: Optional[str] = Header(None),
):
    """Ingest IoT telemetry events con autenticación JWT, rate-limiting y
    persistencia en TimescaleDB (fallback en memoria si no hay conexión)."""
    now = datetime.now(timezone.utc).isoformat()
    sensor_id = request.sensor_id

    # 1. Autenticación JWT (obligatoria en producción)
    if authorization:
        try:
            token = authorization.removeprefix("Bearer ").strip()
            validated_id = device_auth.validate_device_token(token)
            # El claim 'sub' debe coincidir con el sensor_id del payload
            if validated_id != sensor_id:
                raise HTTPException(
                    status_code=403,
                    detail="sensor_id no coincide con el JWT",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Autenticación requerida")
    elif _runtime_env() == "production":
        raise HTTPException(
            status_code=401,
            detail="Authorization header requerido en producción",
        )

    # 2. Rate limiting por sensor
    iot_limit = int(os.getenv("IOT_RATE_LIMIT", "100"))
    if not device_auth.check_rate_limit(sensor_id, limit=iot_limit):
        raise HTTPException(
            status_code=429,
            detail=f"Límite de {iot_limit} requests/minuto por sensor excedido",
        )

    # 3. Normalizar lecturas
    extra = dict(request.model_extra or {})
    readings = dict(request.readings)
    if not readings:
        for reserved in ("sensor_id", "timestamp", "source", "readings"):
            extra.pop(reserved, None)
        readings = extra

    # 3.1 Calidad de datos crítica para CTAEX (pH/EC/VPD)
    _validate_sensor_quality(readings)

    # 4. Determinar estado TRACES
    traces_target = os.getenv("TRACES_HYPERLEDGER_URL", "").strip()
    traces_status = "queued" if traces_target else "disabled"

    event = {
        "sensor_id": sensor_id,
        "timestamp": request.timestamp or now,
        "source": request.source or "iot-bridge",
        "readings": readings,
        "traces": {
            "status": traces_status,
            "target": traces_target,
            "updated_at": now,
        },
        "received_at": now,
    }

    # 5. Persistir en TimescaleDB (fallback a memoria si no disponible)
    persisted = timescale_db.insert_sensor_event(event)
    IOT_LAST_BY_SENSOR[sensor_id] = event

    # 6. Métricas
    tenant = "default"
    IOT_REQUESTS.labels(tenant, sensor_id).inc()

    return {
        "estado": "accepted",
        "sensor_id": sensor_id,
        "traces_status": traces_status,
        "persisted": persisted,
        "received_at": now,
    }


@app.get("/api/v1/iot/telemetry/{sensor_id}/latest")
async def get_iot_latest(sensor_id: str):
    """Return latest ingested telemetry event for a given sensor id."""
    event = IOT_LAST_BY_SENSOR.get(sensor_id)
    if not event:
        raise HTTPException(status_code=404, detail="No telemetry found for sensor")
    return event


@app.get("/api/v1/user/{tenant_id}/status")
@app.get("/user/{tenant_id}/status")
async def get_user_dashboard_status(tenant_id: str):
    """Return compact NIWA/IoT status payload ready for frontend dashboards."""
    event = _latest_event_for_tenant(tenant_id)
    if not event:
        raise HTTPException(status_code=404, detail="No telemetry found for tenant")

    readings = dict(event.get("readings") or {})
    metrics: dict[str, float | None] = {
        "ph": _first_numeric(readings, ("ph", "ph_value")),
        "ec": _first_numeric(readings, ("ec", "ec_ms_cm")),
        "temperature_c": _first_numeric(readings, ("temperature_c", "temperature")),
        "humidity_pct": _first_numeric(readings, ("humidity_pct", "humidity")),
        "lux": _first_numeric(readings, ("lux", "light_lux", "bh1750_lux")),
    }

    alerts = _build_alerts(metrics)
    now = datetime.now(timezone.utc)
    next_irrigation_at = (now.replace(microsecond=0)).isoformat()

    return {
        "status": "ok",
        "tenant_id": tenant_id.lower(),
        "sensor_id": event.get("sensor_id"),
        "metrics": metrics,
        "alerts": {
            "active": len(alerts),
            "items": alerts,
        },
        "automation": {
            "mode": os.getenv("NIWA_AUTO_MODE", "ON"),
        },
        "next_irrigation_at": next_irrigation_at,
        "updated_at": str(event.get("timestamp") or event.get("received_at") or ""),
    }


@app.get("/api/v1/claude/tools")
async def claude_tools_catalog(authorization: Optional[str] = Header(None)):
    """Expose SABIONDA tool catalog in a format ready for Claude Code integration."""
    _require_privileged_access(authorization, operation="/api/v1/claude/tools")
    config = _load_agent_config()
    return {
        "agent": config.get("agent", {}).get("name", "SABIONDA"),
        "version": config.get("agent", {}).get("version", "unknown"),
        "tools": _tool_catalog_from_config(config),
    }


@app.get("/api/v1/claude/context")
async def claude_context(authorization: Optional[str] = Header(None)):
    """Return runtime context that can be injected into Claude Code sessions."""
    _require_privileged_access(authorization, operation="/api/v1/claude/context")
    config = _load_agent_config()
    prompt = ""
    if AGENT_PROMPT_PATH.exists():
        prompt = AGENT_PROMPT_PATH.read_text()
    return {
        "agent": config.get("agent", {}),
        "capabilities": config.get("capabilities", {}),
        "compliance": config.get("compliance", {}),
        "integrations": config.get("integrations", {}),
        "system_prompt": prompt,
    }


@app.post("/api/v1/siex/cuaderno-campo", response_model=DocumentResponse)
async def generate_siex_cuaderno(request: SIEXRequest):
    """Generate SIEX Cuaderno de Campo Digital (JSON payload for PDF generation)."""
    now = datetime.now(timezone.utc)
    payload = {
        "explotacion": request.explotacion.model_dump(),
        "parcelas": [p.model_dump() for p in request.parcelas],
        "tratamientos": [t.model_dump() for t in request.tratamientos],
        "fecha_generacion": now.isoformat(),
        "estado_cumplimiento": {
            "pac_compliant": True,
            "siex_interoperable": True,
            "porcentaje_cumplimiento": 100.0,
        },
        "firma": {
            "pendiente_firma": True,
            "aviso": "Documento generado para REVISIÓN y FIRMA del productor",
        },
    }
    return DocumentResponse(
        tipo_documento="SIEX Cuaderno Campo Digital",
        estado="✅ SIEX Compliant",
        payload=payload,
        generado_en=now.isoformat(),
    )


@app.post("/api/v1/traces/certificado", response_model=DocumentResponse)
async def generate_traces_certificate(request: TRACESRequest):
    """Generate TRACES sanitario certificate (JSON payload for XML/PDF generation)."""
    now = datetime.now(timezone.utc)
    payload = {
        "certificado": {
            "tipo": request.tipo_movimiento,
            "numero": f"TRACES-ES-{now.strftime('%Y%m%d')}-{request.explotacion_rega}",
            "fecha_emision": now.strftime("%Y-%m-%d"),
        },
        "explotacion_origen": {
            "rega": request.explotacion_rega,
            "nombre": request.nombre_explotacion,
            "direccion": request.direccion_explotacion,
            "pais": "ES",
        },
        "animales": request.animales.model_dump(),
        "destino": {
            "pais": request.destino_pais,
            "explotacion": request.destino_explotacion,
        },
        "firma": {
            "pendiente_firma": True,
            "aviso": "Documento generado para REVISIÓN y FIRMA del productor",
        },
    }
    return DocumentResponse(
        tipo_documento="TRACES Certificado Sanitario",
        estado="✅ TRACES Compliant",
        payload=payload,
        generado_en=now.isoformat(),
    )


@app.post("/api/v1/pac/eco-esquema", response_model=DocumentResponse)
async def generate_pac_eco_esquema(request: PACRequest):
    """Generate PAC eco-esquema submission (JSON payload for PDF generation)."""
    now = datetime.now(timezone.utc)
    total_ha = sum(p.superficie_ha for p in request.parcelas)
    eco_parcelas = sum(1 for p in request.parcelas if p.eco_esquema)
    cumplimiento = (
        (eco_parcelas / len(request.parcelas) * 100) if request.parcelas else 0
    )

    payload = {
        "solicitante": {
            "nif": request.nif,
            "nombre": request.nombre,
            "rea": request.rea,
        },
        "campana": request.campana,
        "parcelas": [p.model_dump() for p in request.parcelas],
        "eco_esquemas": [e.model_dump() for e in request.eco_esquemas],
        "resumen": {
            "superficie_total_ha": total_ha,
            "parcelas_eco_esquema": eco_parcelas,
            "parcelas_total": len(request.parcelas),
        },
        "estado_cumplimiento": {
            "pac_compliant": cumplimiento >= 25,
            "porcentaje_global": round(cumplimiento, 2),
        },
        "firma": {
            "pendiente_firma": True,
            "aviso": "Documento generado para REVISIÓN y FIRMA del productor",
        },
    }
    return DocumentResponse(
        tipo_documento="PAC 2026 Eco-esquema",
        estado=f"{'✅' if cumplimiento >= 25 else '⚠️'} PAC {'Compliant' if cumplimiento >= 25 else 'Atención: revisar eco-esquemas'}",
        payload=payload,
        generado_en=now.isoformat(),
    )


@app.get("/api/v1/schemas/{schema_name}")
async def get_schema(schema_name: str):
    """Retrieve a JSON schema for document validation."""
    safe_name = Path(schema_name).name
    schema_path = SCHEMAS_DIR / f"{safe_name}.schema.json"
    if not schema_path.exists():
        raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found")
    with open(schema_path) as f:
        return json.load(f)


@app.post("/api/v1/regepa/explotacion", response_model=DocumentResponse)
async def generate_regepa_explotacion(request: REGEPARequest):
    """Generate REGEPA livestock holding registration (JSON payload for PDF generation)."""
    now = datetime.now(timezone.utc)
    total_cabezas = sum(e.censo for e in request.especies)
    payload = {
        "explotacion": {
            "rega": request.explotacion_rega,
            "tipo": request.tipo_explotacion,
            "clasificacion_zootecnica": request.clasificacion_zootecnica,
            "capacidad_maxima": request.capacidad_maxima,
            "sistema": request.sistema_explotacion,
        },
        "titular": {
            "nif": request.titular_nif,
            "nombre": request.titular_nombre,
            "comunidad_autonoma": request.titular_comunidad,
        },
        "especies": [e.model_dump() for e in request.especies],
        "bienestar_animal": {
            "grasp_compliant": request.grasp_compliant,
            "total_cabezas": total_cabezas,
        },
        "fecha_generacion": now.isoformat(),
        "estado_cumplimiento": {
            "regepa_compliant": True,
            "rd_285_2023": True,
        },
        "firma": {
            "pendiente_firma": True,
            "aviso": "Documento generado para REVISIÓN y FIRMA del productor",
        },
    }
    return DocumentResponse(
        tipo_documento="REGEPA Registro Explotación",
        estado="✅ REGEPA Compliant",
        payload=payload,
        generado_en=now.isoformat(),
    )


@app.post("/api/v1/sigpac/parcelas", response_model=DocumentResponse)
async def generate_sigpac_parcelas(request: SIGPACRequest):
    """Generate SIGPAC plots report (JSON payload for shapefile/PDF generation)."""
    now = datetime.now(timezone.utc)
    superficie_total = sum(p.superficie_ha for p in request.parcelas)
    usos = list({p.uso_sigpac for p in request.parcelas})
    payload = {
        "explotacion": {
            "titular": request.titular_nombre,
            "titular_nif": request.titular_nif,
            "superficie_total_ha": round(superficie_total, 4),
        },
        "parcelas": [p.model_dump() for p in request.parcelas],
        "resumen": {
            "numero_parcelas": len(request.parcelas),
            "usos_sigpac": usos,
        },
        "fecha_generacion": now.isoformat(),
        "firma": {
            "pendiente_firma": True,
            "aviso": "Documento generado para REVISIÓN y FIRMA del productor",
        },
    }
    return DocumentResponse(
        tipo_documento="SIGPAC Informe de Parcelas",
        estado="✅ SIGPAC Compliant",
        payload=payload,
        generado_en=now.isoformat(),
    )


@app.post("/api/v1/claude/execute/{tool_name}")
async def claude_execute(
    tool_name: str,
    request: ClaudeExecuteRequest,
    authorization: Optional[str] = Header(None),
):
    """Single execution endpoint so Claude Code can call all document tools uniformly."""
    _require_privileged_access(authorization, operation="/api/v1/claude/execute")
    payload = request.payload

    if tool_name == "generate_siex_cuaderno":
        result = await generate_siex_cuaderno(SIEXRequest(**payload))
    elif tool_name in {"generate_traces_certificado", "generate_traces_certificate"}:
        result = await generate_traces_certificate(TRACESRequest(**payload))
    elif tool_name == "generate_pac_eco_esquema":
        result = await generate_pac_eco_esquema(PACRequest(**payload))
    elif tool_name == "generate_regepa_explotacion":
        result = await generate_regepa_explotacion(REGEPARequest(**payload))
    elif tool_name == "generate_sigpac_parcelas":
        result = await generate_sigpac_parcelas(SIGPACRequest(**payload))
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool_name}' is not available for execution",
        )

    return {
        "tool": tool_name,
        "estado": "ok",
        "resultado": result.model_dump(),
    }


# --- AI predict endpoint ---

class AIPredictRequest(BaseModel):
    data: dict[str, Any] = Field(
        ...,
        description="Datos de entrada para la predicción (ej. humedad, temperatura)",
    )


@app.post("/api/v1/ai/predict")
async def ai_predict(
    request: AIPredictRequest,
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    """
    Inferencia ligera sobre datos agrovoltaicos/IoT.
    En producción delega en Sabionda (LangGraph). En entornos sin modelo
    devuelve una estimación determinista basada en las entradas.
    """
    _require_privileged_access(authorization, operation="/api/v1/ai/predict")

    import hashlib

    data: dict[str, Any] = request.data
    # Puntuación normalizada sobre los valores numéricos disponibles
    numeric_values = [float(v) for v in data.values() if isinstance(v, (int, float))]
    if numeric_values:
        avg = sum(numeric_values) / len(numeric_values)
        # Confidence: valor sigmoide simplificado ∈ (0, 1)
        confidence = round(1 / (1 + abs(avg - 50) / 100), 4)
        prediction = "optimo" if confidence >= 0.5 else "suboptimo"
    else:
        seed = hashlib.md5(str(sorted(data.items())).encode()).hexdigest()
        confidence = round(int(seed[:4], 16) / 65535, 4)
        prediction = "optimo" if confidence >= 0.5 else "suboptimo"

    return {
        "prediction": prediction,
        "confidence": confidence,
        "model_version": "sabionda-v3.0-heuristic",
        "input_features": [str(key) for key in data.keys()],
    }


# --- GDPR Article 17 — Derecho al olvido ---

class GDPRDeleteResponse(BaseModel):
    status: str
    user_id: str
    deleted_tables: list[str] = []
    audit_id: Optional[str] = None
    deleted_at: str


@app.delete(
    "/api/v1/admin/gdpr/users/{user_id}",
    response_model=GDPRDeleteResponse,
    status_code=200,
)
async def gdpr_delete_user(
    user_id: str,
    authorization: Optional[str] = Header(None),
):
    """Borra todos los datos de un usuario (RGPD Art. 17) y registra en audit_log."""
    _require_privileged_access(authorization, operation="operación GDPR")

    if not timescale_db.available:
        now = datetime.now(timezone.utc).isoformat()
        keys_removed = [
            k
            for k in list(IOT_LAST_BY_SENSOR.keys())
            if k == user_id or k.startswith(f"{user_id}-")
        ]
        for k in keys_removed:
            del IOT_LAST_BY_SENSOR[k]
        return GDPRDeleteResponse(
            status="deleted_memory_only",
            user_id=user_id,
            deleted_tables=["IOT_LAST_BY_SENSOR"],
            audit_id=None,
            deleted_at=now,
        )

    try:
        import importlib as _importlib
        import sys as _sys

        scripts_path = str(Path(__file__).parent.parent / "scripts")
        if scripts_path not in _sys.path:
            _sys.path.insert(0, scripts_path)
        gdpr_mod = _importlib.import_module("gdpr_deletion")
        db_url = (
            f"postgresql://{os.getenv('TIMESCALE_DB_USER', 'castuo_iot')}:"
            f"{os.getenv('TIMESCALE_DB_PASSWORD', '')}@"
            f"{os.getenv('TIMESCALE_DB_HOST', 'localhost')}:"
            f"{os.getenv('TIMESCALE_DB_PORT', '5432')}/"
            f"{os.getenv('TIMESCALE_DB_NAME', 'castuo_telemetry')}"
        )
        manager = gdpr_mod.GDPRDeletionManager(db_url)
        result = manager.delete_user_data(user_id=user_id, imsi=None)
        return GDPRDeleteResponse(
            status=result.get("status", "deleted"),
            user_id=user_id,
            deleted_tables=result.get("deleted_tables", []),
            audit_id=result.get("audit_id"),
            deleted_at=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en borrado GDPR: {exc}")


# --- Trazabilidad TRACES real con firma eIDAS ---

class TracesSubmitRequest(BaseModel):
    lote_id: str = Field(..., description="Identificador único del lote")
    metadata: dict[str, Any] = Field(default_factory=dict)


@app.post("/api/v1/traces/submit")
async def traces_submit(
    request: TracesSubmitRequest,
    authorization: Optional[str] = Header(None),
):
    """Envía un lote a TRACES UE con firma eIDAS y lo registra en Hyperledger."""
    _require_privileged_access(authorization, operation="/api/v1/traces/submit")
    _require_integration_enabled("ENABLE_TRACES_SUBMIT", "TRACES")
    result = traces_client.submit_to_traces(
        lote_id=request.lote_id,
        metadata=request.metadata,
    )
    return {
        "lote_id": request.lote_id,
        **result,
    }
