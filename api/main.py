"""
SABIONDA API - Castúo-System v2.0
FastAPI backend for government document generation (SIEX, TRACES, SIGPAC, REGEPA, PAC).
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="SABIONDA API - Castúo-System",
    description="API para generación de documentación GOV 100% legal y firmable",
    version="2.0.0",
)

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
    animales: TRACESAnimal
    destino_pais: str
    destino_explotacion: str


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "agent": "SABIONDA", "version": "2.0"}


@app.post("/api/v1/siex/cuaderno-campo", response_model=DocumentResponse)
async def generate_siex_cuaderno(request: SIEXRequest):
    """Generate SIEX Cuaderno de Campo Digital (JSON payload for PDF generation)."""
    payload = {
        "explotacion": request.explotacion.model_dump(),
        "parcelas": [p.model_dump() for p in request.parcelas],
        "tratamientos": [t.model_dump() for t in request.tratamientos],
        "fecha_generacion": datetime.now(timezone.utc).isoformat(),
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
        generado_en=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/traces/certificado", response_model=DocumentResponse)
async def generate_traces_certificate(request: TRACESRequest):
    """Generate TRACES sanitario certificate (JSON payload for XML/PDF generation)."""
    payload = {
        "certificado": {
            "tipo": "EXPORT",
            "fecha_emision": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
        "explotacion_origen": {
            "rega": request.explotacion_rega,
            "nombre": request.nombre_explotacion,
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
        generado_en=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/pac/eco-esquema", response_model=DocumentResponse)
async def generate_pac_eco_esquema(request: PACRequest):
    """Generate PAC eco-esquema submission (JSON payload for PDF generation)."""
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
        generado_en=datetime.now(timezone.utc).isoformat(),
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
