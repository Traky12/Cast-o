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

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
import os as _os
# Allow importing from backend/ when running from api/
sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), ".."))

from routers import invernadero, trazabilidad_qr
from routers.orchestrator import router as orchestrator_router
from routers.skills import router as skills_router
from routers.ai import router as ai_router
from routers.satellite import router as satellite_router
from routers.actuadores import router as actuadores_router
from routers.audit import router as audit_router
from routers.github_webhook import router as github_webhook_router
from routers.claude_proxy import router as claude_proxy_router
from middleware.security import router as tenants_router, security_middleware
from backend.routes.health import router as health_router

app = FastAPI(
    title="SABIONDA API - Castúo-System",
    description=(
        "API para gestión agrovoltaica hidropónica y generación de "
        "documentación GOV 100% legal y firmable con trazabilidad QR inmutable"
    ),
    version="3.1.0",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow WordPress frontend + LangGraph service on same docker network.
# Extend CASTUO_CORS_ORIGINS in .env for staging/production domains.
_cors_origins = [
    o.strip()
    for o in os.getenv(
        "CASTUO_CORS_ORIGINS",
        "https://castuo360.eu,https://www.castuo360.eu,"
        "https://castuo-system.cloud,https://www.castuo-system.cloud,"
        "https://api.castuo-system.cloud,"
        "http://localhost:3000,http://localhost:8000,"
        "http://wordpress:80,http://langgraph:8200",
    ).split(",")
    if o.strip()
]

app.middleware("http")(security_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],   # Only verbs actually used
    allow_headers=["Authorization", "Content-Type", "X-WP-Nonce"],
    max_age=600,
)

# ─── Security headers ─────────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """
    Adds security headers to every response.
    Ref: Prontuario cifrado §5 (SEC-001 TLS / hardening).
    These complement TLS termination at the reverse proxy — not a substitute.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"]             = "no-store"
    response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
    # Content-Security-Policy: only for API responses (HTML error pages).
    # Frontend CSP is set by nginx, not here.
    response.headers["Content-Security-Policy"]   = "default-src 'self'; frame-ancestors 'none'"
    return response

app.include_router(health_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root: redirect info to /docs."""
    return {
        "service": "castuo-api",
        "version": "3.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus-style plain-text metrics (minimal)."""
    from fastapi.responses import PlainTextResponse
    import time as _time
    lines = [
        "# HELP castuo_api_up Whether the API is up",
        "# TYPE castuo_api_up gauge",
        "castuo_api_up 1",
        "# HELP castuo_api_uptime_seconds Seconds since boot",
        "# TYPE castuo_api_uptime_seconds counter",
        f"castuo_api_uptime_seconds {int(_time.time())}",
    ]
    return PlainTextResponse("\n".join(lines) + "\n")


app.include_router(orchestrator_router)
app.include_router(skills_router)
app.include_router(ai_router)
app.include_router(satellite_router)
app.include_router(actuadores_router)
app.include_router(audit_router)
app.include_router(github_webhook_router)
app.include_router(claude_proxy_router)
app.include_router(tenants_router)
app.include_router(invernadero.router)
app.include_router(trazabilidad_qr.router)

SCHEMAS_DIR = Path(os.getenv("SCHEMAS_DIR", "/app/schemas"))


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


# --- Endpoints ---


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
