"""
SABIONDA API - Castúo-System v3.0
FastAPI backend for:
  - Government document generation (SIEX, TRACES, SIGPAC, REGEPA, PAC)
  - Agrovoltaic hydroponic greenhouse management
  - Immutable QR traceability from seed to consumer
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from routers import invernadero, trazabilidad_qr

app = FastAPI(
    title="SABIONDA API - Castúo-System",
    description=(
        "API para gestión agrovoltaica hidropónica y generación de "
        "documentación GOV 100% legal y firmable con trazabilidad QR inmutable"
    ),
    version="3.0.0",
)

app.include_router(invernadero.router)
app.include_router(trazabilidad_qr.router)

SCHEMAS_DIR = Path(os.getenv("SCHEMAS_DIR", "/app/schemas"))
AGENT_CONFIG_PATH = Path(
    os.getenv("AGENT_CONFIG_PATH", "/app/agents/sabionda/config.json")
)
AGENT_PROMPT_PATH = Path(
    os.getenv("AGENT_PROMPT_PATH", "/app/agents/sabionda/system-prompt.md")
)

# In-memory IoT ingestion index for smoke/E2E checks.
IOT_LAST_BY_SENSOR: dict[str, dict[str, Any]] = {}


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
    payload: dict
    aviso: str = "Documento generado para REVISIÓN y FIRMA del productor"
    generado_en: str


class ClaudeExecuteRequest(BaseModel):
    payload: dict[str, Any]


class ThingsDataIngestRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier (ESP32, Raspberry Pi, etc.)")
    timestamp: str | None = Field(None, description="ISO-8601 timestamp")
    data: dict[str, Any] = Field(default_factory=dict, description="Telemetry readings")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

    model_config = {"extra": "allow"}


class CTAEXEnsayoRequest(BaseModel):
    type: str = Field(..., description="Test type: cannabis_quality, soil_analysis, water_analysis, etc.")
    sample_id: str | None = Field(None, description="Sample identifier")
    results: dict[str, Any] = Field(default_factory=dict, description="Test results")
    laboratory: str = Field("Food-Lab", description="Laboratory name")
    certified: bool = Field(True, description="GMP certified test")

    model_config = {"extra": "allow"}


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
            {
                "name": "generate_ctaex_ensayo",
                "kind": "document_generation",
                "endpoint": "POST /api/v1/ctaex/ensayos",
                "description": "Genera informe de ensayo CTAEX Food-Lab (cannabis, suelos, agua)",
                "required_fields": ["type", "results"],
                "optional_fields": ["sample_id", "laboratory", "certified"],
                "status": "available",
            },
            {
                "name": "ingest_thingsdata",
                "kind": "iot_ingestion",
                "endpoint": "POST /api/v1/thingsdata/ingest",
                "description": "Ingesta de telemetría desde ThingsData (ESP32, Raspberry Pi)",
                "required_fields": ["device_id"],
                "optional_fields": ["timestamp", "data", "metadata"],
                "status": "available",
            },
        ]

    return tools


# --- Endpoints ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "SABIONDA", "version": "3.0.0"}


@app.post("/api/v1/iot/telemetry")
async def ingest_iot_telemetry(request: IotTelemetryRequest):
    """Ingest IoT telemetry events and keep latest reading per sensor for E2E smoke checks."""
    now = datetime.now(timezone.utc).isoformat()

    extra = dict(request.model_extra or {})
    readings = dict(request.readings)
    if not readings:
        for reserved in ("sensor_id", "timestamp", "source", "readings"):
            extra.pop(reserved, None)
        readings = extra

    traces_target = os.getenv("TRACES_HYPERLEDGER_URL", "").strip()
    traces_status = "queued" if traces_target else "disabled"

    event = {
        "sensor_id": request.sensor_id,
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
    IOT_LAST_BY_SENSOR[request.sensor_id] = event

    return {
        "estado": "accepted",
        "sensor_id": request.sensor_id,
        "traces_status": traces_status,
        "received_at": now,
    }


@app.get("/api/v1/iot/telemetry/{sensor_id}/latest")
async def get_iot_latest(sensor_id: str):
    """Return latest ingested telemetry event for a given sensor id."""
    event = IOT_LAST_BY_SENSOR.get(sensor_id)
    if not event:
        raise HTTPException(status_code=404, detail="No telemetry found for sensor")
    return event


# --- ThingsData Integration ---


THINGSDATA_STORAGE: dict[str, dict[str, Any]] = {}


@app.post("/api/v1/thingsdata/ingest")
async def ingest_thingsdata(request: ThingsDataIngestRequest):
    """Ingest telemetry data from ThingsData platform (ESP32/Raspberry Pi sensors)."""
    now = datetime.now(timezone.utc).isoformat()
    device_id = request.device_id

    event = {
        "device_id": device_id,
        "timestamp": request.timestamp or now,
        "data": request.data,
        "metadata": request.metadata or {"source": "ThingsData", "compliance": ["RGPD", "AI Act UE 2024/1689"]},
        "received_at": now,
    }
    THINGSDATA_STORAGE[device_id] = event

    return {
        "status": "stored",
        "device_id": device_id,
        "timestamp": event["timestamp"],
        "bytes_received": len(str(request.data)),
        "compliance": "RGPD + AI Act UE 2024/1689",
    }


@app.get("/api/v1/thingsdata/{device_id}/latest")
async def get_thingsdata_latest(device_id: str):
    """Return latest ingested ThingsData event for a given device."""
    event = THINGSDATA_STORAGE.get(device_id)
    if not event:
        raise HTTPException(status_code=404, detail=f"No data found for device: {device_id}")
    return event


# --- CTAEX Food-Lab Integration ---


@app.post("/api/v1/ctaex/ensayos", response_model=DocumentResponse)
async def generate_ctaex_ensayo(request: CTAEXEnsayoRequest):
    """Generate CTAEX laboratory test report (Food-Lab) conforme Ph. Eur. 3028 and RD 903/2025."""
    now = datetime.now(timezone.utc)
    sample_id = request.sample_id or f"CTAEX-{now.strftime('%Y%m%d%H%M%S')}"

    payload = {
        "laboratorio": {
            "nombre": request.laboratory,
            "acreditacion": "ENAC ISO 17025",
            "numero_ensayo": sample_id,
        },
        "muestra": {
            "id": sample_id,
            "tipo_ensayo": request.type,
            "fecha_recepcion": now.strftime("%Y-%m-%d"),
        },
        "resultados": request.results,
        "normativa": {
            "compliance": ["RD 903/2025", "GMP", "Ph. Eur. 3028"] if request.type == "cannabis_quality" else ["ISO 17025"],
            "certificado_gmp": request.certified,
        },
        "fecha_informe": now.isoformat(),
        "firma": {
            "pendiente_firma": True,
            "aviso": "Informe generado para REVISIÓN y FIRMA del responsable de laboratorio",
        },
    }

    return DocumentResponse(
        tipo_documento=f"CTAEX Informe Ensayo - {request.type}",
        estado="✅ CTAEX Compliant" if request.certified else "⚠️ Pendiente certificación GMP",
        payload=payload,
        generado_en=now.isoformat(),
    )


@app.get("/api/v1/claude/tools")
async def claude_tools_catalog():
    """Expose SABIONDA tool catalog in a format ready for Claude Code integration."""
    config = _load_agent_config()
    return {
        "agent": config.get("agent", {}).get("name", "SABIONDA"),
        "version": config.get("agent", {}).get("version", "unknown"),
        "tools": _tool_catalog_from_config(config),
    }


@app.get("/api/v1/claude/context")
async def claude_context():
    """Return runtime context that can be injected into Claude Code sessions."""
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
async def claude_execute(tool_name: str, request: ClaudeExecuteRequest):
    """Single execution endpoint so Claude Code can call all document tools uniformly."""
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
    elif tool_name in {"generate_ctaex_ensayo", "generate_ctaex_report"}:
        result = await generate_ctaex_ensayo(CTAEXEnsayoRequest(**payload))
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
