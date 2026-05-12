"""
CASTÚO-SYSTEM™ v3.1 — Router de Auditoría Inmutable
Consulta y verificación de la bitácora de cadena de custodia.

Endpoints:
  GET  /api/v1/audit/lote/{lote_id}         — Cadena completa de un lote
  GET  /api/v1/audit/operator/{actor_nif}   — Accountability: acciones de un operador
  GET  /api/v1/audit/action/{tipo}          — Todos los eventos de un tipo de acción
  GET  /api/v1/audit/verify                 — Verificar integridad criptográfica
  GET  /api/v1/audit/search                 — Búsqueda multi-filtro

Autenticación: JWT HS256 — roles requeridos: admin | editor | api
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from services.audit.audit_logger import AuditAction, get_audit_logger

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])
_bearer = HTTPBearer(auto_error=False)


# ── Auth ───────────────────────────────────────────────────────────────────────

def _verify_jwt(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    import jwt as pyjwt

    def _secret() -> str:
        path = os.getenv("JWT_SECRET_FILE", "")
        if path:
            try:
                with open(path) as f:
                    return f.read().strip()
            except OSError:
                pass
        return os.getenv("JWT_SECRET", "")

    secret = _secret()
    if not secret:
        return {"sub": "dev-mode", "role": "admin"}

    if not credentials:
        raise HTTPException(status_code=401, detail="Token JWT requerido")

    try:
        payload = pyjwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Token inválido: {exc}")

    role = payload.get("role", "")
    if role not in ("admin", "editor", "api"):
        raise HTTPException(status_code=403, detail=f"Rol '{role}' no autorizado")

    return payload


# ── Modelos de respuesta ───────────────────────────────────────────────────────

class AuditEventOut(BaseModel):
    evento_id: str
    accion: str
    lote_id: str
    actor_nif: str
    recurso: str
    datos: dict
    timestamp: str
    hash_anterior: str
    hash_propio: str


class AuditListResponse(BaseModel):
    total: int
    eventos: List[AuditEventOut]
    timestamp: str


class VerifyResponse(BaseModel):
    ok: bool
    total_eventos: int
    errores: list
    ultimo_hash: str
    mensaje: str
    timestamp: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/lote/{lote_id}", response_model=AuditListResponse,
            summary="Cadena de custodia completa de un lote")
async def get_audit_by_lote(
    lote_id: str,
    _jwt: dict = Depends(_verify_jwt),
) -> AuditListResponse:
    """
    Retorna todos los eventos de auditoría asociados a un lote_id,
    desde la apertura hasta la cosecha, en orden cronológico.
    Permite al operador y al auditor ver la cadena de custodia completa.
    """
    audit = get_audit_logger()
    eventos = audit.get_by_lote(lote_id)
    return AuditListResponse(
        total=len(eventos),
        eventos=[AuditEventOut(**e) for e in eventos],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/operator/{actor_nif}", response_model=AuditListResponse,
            summary="Accountability: todas las acciones de un operador")
async def get_audit_by_operator(
    actor_nif: str,
    limit: int = Query(100, ge=1, le=1000),
    _jwt: dict = Depends(_verify_jwt),
) -> AuditListResponse:
    """
    Retorna las últimas N acciones realizadas por un operador (actor_nif).
    Esencial para accountability y auditorías GDPR/AI Act.
    """
    audit = get_audit_logger()
    eventos = audit.get_by_operator(actor_nif, limit=limit)
    return AuditListResponse(
        total=len(eventos),
        eventos=[AuditEventOut(**e) for e in eventos],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/action/{tipo}", response_model=AuditListResponse,
            summary="Todos los eventos de un tipo de acción")
async def get_audit_by_action(
    tipo: str,
    limit: int = Query(200, ge=1, le=1000),
    _jwt: dict = Depends(_verify_jwt),
) -> AuditListResponse:
    """
    Retorna los últimos N eventos de una acción específica.
    Ej: tipo=REGISTRO_COSECHA → todas las cosechas registradas.
    Tipos válidos: APERTURA_LOTE, REGISTRO_SOLUCION, REGISTRO_CLIMA,
    REGISTRO_FITOSANITARIO, REGISTRO_COSECHA, CONTROL_ACTUADOR, etc.
    """
    # Validar tipo
    valid_tipos = {a.value for a in AuditAction}
    if tipo not in valid_tipos:
        raise HTTPException(
            status_code=422,
            detail=f"Tipo de acción '{tipo}' no válido. Opciones: {sorted(valid_tipos)}",
        )
    audit = get_audit_logger()
    eventos = audit.get_by_action(tipo, limit=limit)
    return AuditListResponse(
        total=len(eventos),
        eventos=[AuditEventOut(**e) for e in eventos],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/verify", response_model=VerifyResponse,
            summary="Verificar integridad criptográfica de la cadena")
async def verify_audit_chain(
    _jwt: dict = Depends(_verify_jwt),
) -> VerifyResponse:
    """
    Recorre toda la bitácora y verifica que cada evento:
    1. hash_anterior coincide con el hash_propio del evento anterior
    2. hash_propio es correcto (recalculado con los datos del evento)

    Si algún evento fue manipulado, se detecta aquí.
    """
    audit = get_audit_logger()
    result = audit.verify_chain()
    return VerifyResponse(
        ok=result["ok"],
        total_eventos=result["total_eventos"],
        errores=result["errores"],
        ultimo_hash=result.get("ultimo_hash", ""),
        mensaje=result["mensaje"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/search", response_model=AuditListResponse,
            summary="Búsqueda multi-filtro en la bitácora")
async def search_audit(
    lote_id: Optional[str] = Query(None),
    actor_nif: Optional[str] = Query(None),
    accion: Optional[str] = Query(None),
    desde: Optional[str] = Query(None, description="ISO-8601 timestamp inicio"),
    hasta: Optional[str] = Query(None, description="ISO-8601 timestamp fin"),
    limit: int = Query(100, ge=1, le=1000),
    _jwt: dict = Depends(_verify_jwt),
) -> AuditListResponse:
    """
    Búsqueda avanzada con cualquier combinación de filtros:
    lote_id, actor_nif, accion, rango de fechas (desde/hasta ISO-8601).
    """
    if not any([lote_id, actor_nif, accion, desde, hasta]):
        raise HTTPException(
            status_code=422,
            detail="Al menos un filtro de búsqueda es requerido",
        )
    audit = get_audit_logger()
    eventos = audit.search(
        lote_id=lote_id,
        actor_nif=actor_nif,
        accion=accion,
        desde=desde,
        hasta=hasta,
        limit=limit,
    )
    return AuditListResponse(
        total=len(eventos),
        eventos=[AuditEventOut(**e) for e in eventos],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/actions",
            summary="Listar todos los tipos de acción disponibles")
async def list_actions() -> dict:
    """Retorna el catálogo de acciones auditables. Sin autenticación."""
    return {
        "acciones": [
            {"id": a.value, "descripcion": _action_desc(a.value)}
            for a in AuditAction
        ]
    }


def _action_desc(a: str) -> str:
    desc = {
        "APERTURA_LOTE":          "Apertura de nuevo lote de cultivo hidropónico",
        "CIERRE_LOTE":            "Cierre / cosecha final del lote",
        "REGISTRO_SOLUCION":      "Lectura de pH, EC, O₂ y nutrientes",
        "REGISTRO_CLIMA":         "Lectura de temperatura, HR, CO₂ y VPD",
        "REGISTRO_AGROVOLTAICO":  "Lectura de irradiancia y producción solar",
        "REGISTRO_FITOSANITARIO": "Aplicación o inspección fitosanitaria",
        "REGISTRO_COSECHA":       "Cierre de ciclo con datos de cosecha",
        "CONTROL_ACTUADOR":       "Activación o ajuste de actuador",
        "EMERGENCIA_STOP":        "Parada de emergencia de actuadores",
        "VALIDACION_LOTE":        "Validación y registro blockchain del lote",
        "GENERACION_QR":          "Generación de QR para consumidor final",
        "ACCESO_API":             "Acceso a la API (registro de autenticación)",
    }
    return desc.get(a, a)
