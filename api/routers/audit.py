"""
SABIONDA — API de Auditoría y Trazabilidad Inmutable
Búsqueda, verificación y reportes de la cadena de custodia.

Endpoints:
  - GET /api/v1/audit/lote/{lote_id} → Todos los eventos de un lote
  - GET /api/v1/audit/operator/{operador_nif} → Todas las acciones de un operador
  - GET /api/v1/audit/action/{action} → Todos los eventos de un tipo
  - GET /api/v1/audit/verify → Verificar integridad criptográfica
  - GET /api/v1/audit/search → Búsqueda avanzada
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.security.rbac import require_roles
from services.audit import AuditAction, AuditEvent, get_audit_logger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/audit", tags=["audit"])
audit_logger = get_audit_logger()


# ─────────────────────────────────────────────────────────────────────────────
# Modelos de Respuesta
# ─────────────────────────────────────────────────────────────────────────────


class AuditEventResponse(BaseModel):
    """Respuesta de evento auditado."""
    event_id: str
    timestamp: str
    action: str
    actor_nif: str
    actor_role: Optional[str] = None
    resource_type: str
    resource_id: str
    severity: str
    data: dict[str, Any]
    status: str
    error_msg: Optional[str] = None


class AuditTrailResponse(BaseModel):
    """Respuesta con lista de eventos auditados."""
    resource_id: str
    resource_type: str
    total_events: int
    events: list[AuditEventResponse]
    chain_verified: bool


def _event_response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        event_id=event.event_id,
        timestamp=event.timestamp,
        action=event.action.value,
        actor_nif=event.actor_nif,
        actor_role=event.actor_role,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        severity=event.severity.value,
        data=event.data,
        status=event.status,
        error_msg=event.error_msg,
    )


class ChainIntegrityReport(BaseModel):
    """Reporte de verificación de integridad criptográfica."""
    total_events: int
    chain_valid: bool
    broken_at_event: Optional[str] = None
    first_event_id: Optional[str] = None
    last_event_id: Optional[str] = None
    verification_timestamp: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/lote/{lote_id}", response_model=AuditTrailResponse,
            summary="Obtener auditoría completa de un lote",
            dependencies=[Depends(require_roles("admin_general", "administrador", "auditor", "ciso", "cumplimiento"))])
async def get_lote_audit_trail(lote_id: str) -> AuditTrailResponse:
    """
    Retorna todos los eventos auditados para un lote específico, en orden cronológico.
    Incluye apertura, registros de solución, clima, cosecha, blockchain, etc.
    Verifica la integridad criptográfica de la cadena.
    """
    try:
        events = audit_logger.search_by_lote_id(lote_id)
        if not events:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron eventos auditados para lote {lote_id}"
            )
        
        # Verificar integridad de la cadena para este lote
        chain_valid = audit_logger.verify_chain_integrity()
        
        return AuditTrailResponse(
            resource_id=lote_id,
            resource_type="lote",
            total_events=len(events),
            events=[_event_response(event) for event in events],
            chain_verified=chain_valid,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obtaining audit trail for lote {lote_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo auditoría del lote")


@router.get("/operator/{operador_nif}", response_model=AuditTrailResponse,
            summary="Obtener todas las acciones de un operador",
            dependencies=[Depends(require_roles("admin_general", "administrador", "auditor", "ciso", "cumplimiento"))])
async def get_operator_audit_trail(operador_nif: str) -> AuditTrailResponse:
    """
    Retorna todas las acciones realizadas por un operador específico.
    Útil para auditar responsabilidad y accountability.
    """
    try:
        events = audit_logger.search_by_operator(operador_nif)
        if not events:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron eventos para operador {operador_nif}"
            )
        
        chain_valid = audit_logger.verify_chain_integrity()
        
        return AuditTrailResponse(
            resource_id=operador_nif,
            resource_type="operador",
            total_events=len(events),
            events=[_event_response(event) for event in events],
            chain_verified=chain_valid,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obtaining audit trail for operator {operador_nif}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo auditoría del operador")


@router.get("/action/{action_name}", response_model=AuditTrailResponse,
            summary="Obtener todos los eventos de un tipo de acción",
            dependencies=[Depends(require_roles("admin_general", "administrador", "auditor", "ciso", "cumplimiento"))])
async def get_action_audit_trail(action_name: str) -> AuditTrailResponse:
    """
    Retorna todos los eventos de un tipo específico de acción.
    Ej: REGISTRO_COSECHA, APERTURA_LOTE, etc.
    """
    try:
        # Validar que el action_name sea válido
        try:
            action = AuditAction[action_name.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Acción no válida: {action_name}. Válidas: {[a.name for a in AuditAction]}"
            )
        
        events = audit_logger.search_by_action(action)
        if not events:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron eventos de tipo {action_name}"
            )
        
        chain_valid = audit_logger.verify_chain_integrity()
        
        return AuditTrailResponse(
            resource_id=action_name,
            resource_type="accion",
            total_events=len(events),
            events=[_event_response(event) for event in events],
            chain_verified=chain_valid,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obtaining audit trail for action {action_name}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo auditoría de acción")


@router.get("/verify", response_model=ChainIntegrityReport,
            summary="Verificar integridad criptográfica de la cadena de auditoría",
            dependencies=[Depends(require_roles("admin_general", "administrador", "auditor", "ciso", "cumplimiento"))])
async def verify_chain_integrity() -> ChainIntegrityReport:
    """
    Verifica que la cadena criptográfica de la auditoría sea íntegra.
    Detecta si algún evento ha sido modificado o eliminado.
    """
    try:
        chain_valid = audit_logger.verify_chain_integrity()
        summary = audit_logger.get_chain_summary()
        
        return ChainIntegrityReport(
            total_events=summary.get("total_events", 0),
            chain_valid=chain_valid,
            broken_at_event=None if chain_valid else summary.get("last_verified_event_id"),
            first_event_id=summary.get("first_event_id"),
            last_event_id=summary.get("last_event_id"),
            verification_timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        logger.error(f"Error verifying chain integrity: {e}")
        raise HTTPException(status_code=500, detail="Error verificando integridad de cadena")


@router.get("/search", response_model=AuditTrailResponse,
            summary="Búsqueda avanzada de auditoría",
            dependencies=[Depends(require_roles("admin_general", "administrador", "auditor", "ciso", "cumplimiento"))])
async def search_audit(
    lote_id: Optional[str] = Query(None, description="Filtrar por lote_id"),
    operador_nif: Optional[str] = Query(None, description="Filtrar por operador_nif"),
    action: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
) -> AuditTrailResponse:
    """
    Búsqueda avanzada en la auditoría con múltiples filtros.
    Puede combinar lote_id, operador_nif y acción.
    """
    if not any([lote_id, operador_nif, action]):
        raise HTTPException(
            status_code=400,
            detail="Se requiere al menos uno de: lote_id, operador_nif, action"
        )
    
    try:
        all_events: list[AuditEvent] = []
        
        if lote_id:
            all_events.extend(audit_logger.search_by_lote_id(lote_id))
        
        if operador_nif:
            all_events.extend(audit_logger.search_by_operator(operador_nif))
        
        if action:
            try:
                action_enum = AuditAction[action.upper()]
                all_events.extend(audit_logger.search_by_action(action_enum))
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Acción no válida: {action}"
                )
        
        # Deduplicar por event_id
        seen: set[str] = set()
        unique_events: list[AuditEvent] = []
        for event in all_events:
            if event.event_id not in seen:
                seen.add(event.event_id)
                unique_events.append(event)
        
        if not unique_events:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron eventos con los criterios de búsqueda"
            )
        
        # Ordenar por timestamp
        unique_events.sort(key=lambda event: event.timestamp)
        
        chain_valid = audit_logger.verify_chain_integrity()
        
        return AuditTrailResponse(
            resource_id="search_result",
            resource_type="búsqueda",
            total_events=len(unique_events),
            events=[_event_response(event) for event in unique_events],
            chain_verified=chain_valid,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching audit: {e}")
        raise HTTPException(status_code=500, detail="Error en búsqueda de auditoría")
