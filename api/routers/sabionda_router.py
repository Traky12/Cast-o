"""
Router para gestión de contactos de emergencia y escalado de incidencias a Sabionda.

Endpoints:
- POST /emergency-contact : Configurar número WhatsApp principal
- POST /escalate-incident : Escalar incidencia crítica a Sabionda
- GET /incident-history : Historial de incidencias
- GET /decisions : Decisiones de Sabionda
"""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

try:
    from security.sabionda_governance import (
        IncidenceReport,
        IncidenceSeverity,
        IncidenceType,
        sabionda,
    )
    from services.whatsapp_alerts import whatsapp_alert_service
except ModuleNotFoundError:
    from api.security.sabionda_governance import (
        IncidenceReport,
        IncidenceSeverity,
        IncidenceType,
        sabionda,
    )
    from api.services.whatsapp_alerts import whatsapp_alert_service


router = APIRouter(prefix="/api/v1/sabionda", tags=["Sabionda Governance"])


class SetEmergencyContactRequest(BaseModel):
    """Solicitud para configurar contacto de emergencia."""
    
    phone: str = Field(..., description="Número WhatsApp (+país + número, ej: +34693443825)")
    operator_name: Optional[str] = Field(None, description="Nombre del operador")


class EmergencyContactResponse(BaseModel):
    """Respuesta de configuración de contacto."""
    
    status: str
    message: str
    phone_masked: str
    operator_name: Optional[str]


class EscalateIncidentRequest(BaseModel):
    """Solicitud de escalado de incidencia a Sabionda."""
    
    incident_id: str = Field(..., description="ID único del incidente")
    prototype: int = Field(..., ge=1, le=2, description="Prototipo (1 o 2)")
    severity: IncidenceSeverity = Field(..., description="Nivel de severidad")
    incident_type: IncidenceType = Field(..., description="Tipo de incidencia")
    description: str = Field(..., description="Descripción clara del problema")
    affected_variable: str = Field(..., description="Variable medida (pH, temp, etc)")
    current_value: float = Field(..., description="Valor actual")
    expected_range: tuple[float, float] = Field(..., description="Rango esperado")
    suggested_action: Optional[str] = Field(None, description="Acción sugerida")
    operator_id: Optional[str] = Field(None, description="ID del operador que reporta")


class EscalateIncidentResponse(BaseModel):
    """Respuesta de escalado a Sabionda."""
    
    incident_id: str
    status: str
    sabionda_decision: str
    confidence: float
    requires_human_approval: bool
    whatsapp_notified: bool
    timestamp: str


class IncidentHistoryResponse(BaseModel):
    """Respuesta de historial de incidencias."""
    
    total: int
    prototype: Optional[int]
    severity: Optional[str]
    incidents: list[dict[str, Any]]


class SabiondaDecisionResponse(BaseModel):
    """Respuesta con decisión de Sabionda."""
    
    incident_id: str
    decision: str
    confidence: float
    requires_human_approval: bool
    whatsapp_sent: bool
    timestamp: str


# =========================================================================
# ENDPOINTS
# =========================================================================


@router.post("/emergency-contact", response_model=EmergencyContactResponse)
async def set_emergency_contact(request: SetEmergencyContactRequest) -> EmergencyContactResponse:
    """
    Configura el número de WhatsApp para alertas críticas de Sabionda.
    
    Este es el contacto principal que recibirá notificaciones de:
    - Fallos de sensor
    - Fallos de bomba
    - Anomalías críticas
    - Brechas de seguridad
    - Emergencias (biohazard, fugas)
    """
    
    # Validar formato de teléfono
    if not request.phone.startswith("+"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número debe empezar con + (ej: +34693443825)",
        )
    
    digits = "".join(c for c in request.phone if c.isdigit())
    if len(digits) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número debe tener al menos 10 dígitos",
        )
    
    try:
        sabionda.operator_phone = request.phone
        
        return EmergencyContactResponse(
            status="success",
            message=f"Contacto de emergencia configurado: {request.operator_name or 'Operador'}",
            phone_masked=sabionda._mask_phone(request.phone),
            operator_name=request.operator_name,
        )
    
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/escalate-incident", response_model=EscalateIncidentResponse)
async def escalate_incident(
    request: EscalateIncidentRequest,
    http_request: Request,
) -> EscalateIncidentResponse:
    """
    Escala una incidencia crítica a Sabionda.
    
    Sabionda:
    1. Analiza el incidente
    2. Toma una decisión
    3. Si es CRITICAL/EMERGENCY, notifica al operador por WhatsApp
    4. Registra todo en auditoría
    
    Niveles de severidad:
    - INFO: Log informativo
    - WARNING: Requiere atención
    - CRITICAL: Intervención inmediata + WhatsApp
    - EMERGENCY: Riesgo de pérdida total + WhatsApp + Human approval
    """
    
    # Crear reporte de incidencia
    incident_report = IncidenceReport(
        incident_id=request.incident_id,
        prototype=request.prototype,
        severity=request.severity,
        incident_type=request.incident_type,
        description=request.description,
        affected_variable=request.affected_variable,
        current_value=request.current_value,
        expected_range=request.expected_range,
        suggested_action=request.suggested_action,
        operator_id=request.operator_id or (
            http_request.client.host if http_request.client else "unknown"
        ),
    )
    
    # Sabionda analiza y toma decisión
    decision = sabionda.analyze_incident(incident_report)
    
    # Si es crítico/emergencia y hay número configurado, enviar WhatsApp
    if (
        decision.whatsapp_notification_sent
        and decision.whatsapp_recipient
        and sabionda.operator_phone
    ):
        msg_response = whatsapp_alert_service.send_critical_alert(
            to=sabionda.operator_phone,
            incident_type=request.incident_type.value,
            prototype=request.prototype,
            description=request.description,
            incident_id=request.incident_id,
        )
        
        decision.whatsapp_notification_sent = msg_response.status == "sent"
    
    return EscalateIncidentResponse(
        incident_id=decision.incident_id,
        status="escalated",
        sabionda_decision=decision.decision,
        confidence=decision.confidence,
        requires_human_approval=decision.requires_human_approval,
        whatsapp_notified=decision.whatsapp_notification_sent,
        timestamp=decision.timestamp,
    )


@router.get("/incident-history", response_model=IncidentHistoryResponse)
async def get_incident_history(
    prototype: Optional[int] = None,
    severity: Optional[str] = None,
    limit: int = 100,
) -> IncidentHistoryResponse:
    """
    Obtiene historial de incidencias reportadas a Sabionda.
    
    Filtrable por prototipo y severidad.
    """
    
    severity_enum = None
    if severity:
        try:
            severity_enum = IncidenceSeverity(severity)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Severity debe ser uno de: {[s.value for s in IncidenceSeverity]}",
            )
    
    incidents = sabionda.get_incident_history(
        prototype=prototype,
        severity=severity_enum,
        limit=limit,
    )
    
    return IncidentHistoryResponse(
        total=len(incidents),
        prototype=prototype,
        severity=severity,
        incidents=[i.dict() for i in incidents],
    )


@router.get("/decisions", response_model=list[SabiondaDecisionResponse])
async def get_decisions(
    incident_id: Optional[str] = None,
    limit: int = 100,
) -> list[SabiondaDecisionResponse]:
    """
    Obtiene historial de decisiones tomadas por Sabionda.
    
    Cada decisión incluye:
    - Acción recomendada
    - Confianza de la decisión
    - Si requiere aprobación humana
    - Si se notificó al operador
    """
    
    decisions = sabionda.get_decision_history(
        incident_id=incident_id,
        limit=limit,
    )
    
    return [
        SabiondaDecisionResponse(
            incident_id=d.incident_id,
            decision=d.decision,
            confidence=d.confidence,
            requires_human_approval=d.requires_human_approval,
            whatsapp_sent=d.whatsapp_notification_sent,
            timestamp=d.timestamp,
        )
        for d in decisions
    ]


@router.get("/audit-log")
async def export_audit_log() -> dict[str, Any]:
    """
    Exporta log de auditoría completo de Sabionda.
    
    Incluye todas las incidencias y decisiones para compliance/análisis.
    """
    
    import json
    
    audit_json = sabionda.export_audit_log()
    return json.loads(audit_json)


@router.get("/status")
async def sabionda_status() -> dict[str, Any]:
    """
    Status actual de Sabionda.
    """
    
    return {
        "status": "operational",
        "operator_phone": sabionda._mask_phone(sabionda.operator_phone) if sabionda.operator_phone else "not configured",
        "whatsapp_enabled": whatsapp_alert_service.is_enabled(),
        "total_incidents": len(sabionda.incident_history),
        "total_decisions": len(sabionda.decision_history),
        "critical_incidents": len(
            [i for i in sabionda.incident_history if i.severity == IncidenceSeverity.CRITICAL]
        ),
        "emergency_incidents": len(
            [i for i in sabionda.incident_history if i.severity == IncidenceSeverity.EMERGENCY]
        ),
    }
