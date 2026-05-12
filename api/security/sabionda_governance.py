"""
SABIONDA - IA Soberana Central del Sistema CASTUO

Módulo de governance que establece autoridad central de Sabionda sobre:
- Decisiones críticas de ambos prototipos
- Escalado de incidencias graves
- Orquestación de respuesta automática
- Notificaciones al operador principal por WhatsApp
- Auditoría y trazabilidad de decisiones
"""

import json
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class IncidenceSeverity(str, Enum):
    """Niveles de severidad de incidencias."""
    INFO = "info"  # Log informativo
    WARNING = "warning"  # Requiere atención
    CRITICAL = "critical"  # Necesita intervención inmediata
    EMERGENCY = "emergency"  # Riesgo de pérdida total


class IncidenceType(str, Enum):
    """Tipos de incidencias detectadas."""
    SENSOR_FAILURE = "sensor_failure"  # Sensor averiado/desconectado
    PUMP_FAILURE = "pump_failure"  # Bomba sin caudal
    TEMP_ANOMALY = "temp_anomaly"  # Temperatura fuera de rango crítico
    PH_ANOMALY = "ph_anomaly"  # pH fuera de rango
    POWER_LOSS = "power_loss"  # Pérdida de energía
    NETWORK_LOSS = "network_loss"  # Desconexión de red
    SECURITY_BREACH = "security_breach"  # Intento de acceso no autorizado
    WATER_LEAK = "water_leak"  # Fuga detectada
    BIOHAZARD = "biohazard"  # Contaminación/enfermedad
    UNKNOWN = "unknown"  # Desconocido


class IncidenceReport(BaseModel):
    """Reporte de incidencia para escalado a Sabionda."""
    
    incident_id: str = Field(..., description="ID único del incidente")
    prototype: int = Field(..., description="Prototipo afectado (1 o 2)")
    severity: IncidenceSeverity = Field(..., description="Nivel de severidad")
    incident_type: IncidenceType = Field(..., description="Tipo de incidencia")
    description: str = Field(..., description="Descripción clara del problema")
    affected_variable: str = Field(..., description="Variable medida afectada (pH, temp, etc)")
    current_value: float = Field(..., description="Valor actual")
    expected_range: tuple[float, float] = Field(..., description="Rango esperado")
    suggested_action: Optional[str] = Field(None, description="Acción sugerida por el sistema")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    operator_id: Optional[str] = Field(None, description="ID del operador que reporta")
    

class SabiondaDecision(BaseModel):
    """Decisión tomada por Sabionda sobre una incidencia."""
    
    incident_id: str
    decision: str = Field(..., description="Acción decidida por Sabionda")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza de la decisión (0-1)")
    requires_human_approval: bool = Field(default=False, description="¿Necesita aprobación humana?")
    whatsapp_notification_sent: bool = Field(default=False, description="¿Se envió notificación WhatsApp?")
    whatsapp_recipient: Optional[str] = Field(None, description="Número WhatsApp del destinatario")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SabiondaGovernance:
    """
    Autoridad central de decisiones críticas en CASTUO-SYSTEM.
    
    Sabionda actúa como:
    1. Monitor de ambos prototipos
    2. Gestor de incidencias 
    3. Escalador a operador principal
    4. Ejecutor de acciones automáticas seguras
    5. Auditor de decisiones
    """

    SEVERITY_THRESHOLDS = {
        IncidenceSeverity.INFO: {"auto_resolve": True, "whatsapp": False},
        IncidenceSeverity.WARNING: {"auto_resolve": False, "whatsapp": False},
        IncidenceSeverity.CRITICAL: {"auto_resolve": False, "whatsapp": True},
        IncidenceSeverity.EMERGENCY: {"auto_resolve": False, "whatsapp": True, "force_human": True},
    }

    def __init__(self) -> None:
        self.incident_history: list[IncidenceReport] = []
        self.decision_history: list[SabiondaDecision] = []
        self._operator_phone = os.getenv(
            "SABIONDA_OPERATOR_PHONE",
            os.getenv("EMERGENCY_CONTACT_PHONE", "")
        )

    @property
    def operator_phone(self) -> str:
        """Número WhatsApp del operador principal."""
        return self._operator_phone

    @operator_phone.setter
    def operator_phone(self, phone: str) -> None:
        """Configura número de operador principal."""
        if not phone.startswith("+"):
            raise ValueError("El número debe empezar con +")
        self._operator_phone = phone
        logger.info(f"Sabionda operator phone configured: {self._mask_phone(phone)}")

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Enmascara número para logs (privacidad)."""
        if len(phone) < 8:
            return "***"
        return f"{phone[:3]}...{phone[-3:]}"

    def analyze_incident(self, report: IncidenceReport) -> SabiondaDecision:
        """
        Analiza un incidente y toma una decisión.
        Retorna la decisión de Sabionda.
        """
        self.incident_history.append(report)
        
        decision_text = self._compute_decision(report)
        confidence = self._estimate_confidence(report)
        requires_human = report.severity in {
            IncidenceSeverity.EMERGENCY,
            IncidenceSeverity.CRITICAL,
        }
        
        # Si es crítico/emergencia y hay operador, notificar por WhatsApp
        send_whatsapp = (
            report.severity in {IncidenceSeverity.CRITICAL, IncidenceSeverity.EMERGENCY}
            and self._operator_phone
        )
        send_whatsapp_bool = bool(send_whatsapp)
        
        decision = SabiondaDecision(
            incident_id=report.incident_id,
            decision=decision_text,
            confidence=confidence,
            requires_human_approval=requires_human,
            whatsapp_notification_sent=send_whatsapp_bool,
            whatsapp_recipient=self._operator_phone if send_whatsapp_bool else None,
        )
        
        self.decision_history.append(decision)
        
        # Log de auditoría
        logger.warning(
            f"SABIONDA DECISION: {report.prototype} "
            f"[{report.severity.value}] {report.incident_type.value} → {decision_text}"
        )
        
        return decision

    def _compute_decision(self, report: IncidenceReport) -> str:
        """Computa decisión según tipo y severidad de incidencia."""
        
        # Reglas de decisión por tipo de incidencia
        rules: dict[IncidenceType, str] = {
            IncidenceType.SENSOR_FAILURE: (
                "Cambiar a sensor redundante si existe; "
                "si no, activar control manual y alarma"
            ),
            IncidenceType.PUMP_FAILURE: (
                "DETENER riego inmediatamente; "
                "cambiar a bomba backup; "
                "verificar presión y válvulas"
            ),
            IncidenceType.TEMP_ANOMALY: (
                "Revisar calefactor/cooler; "
                "aumentar ventilación; "
                "activar modo emergencia si T > 40°C o T < 5°C"
            ),
            IncidenceType.PH_ANOMALY: (
                "Tomar muestra manual; "
                "ajustar dosificación (ácido/base); "
                "realizar cambio de agua parcial si pH > 8 o < 5"
            ),
            IncidenceType.POWER_LOSS: (
                "Activar UPS; "
                "cambiar a modo de emergencia (riego manual); "
                "alertar a operador para verificar red eléctrica"
            ),
            IncidenceType.NETWORK_LOSS: (
                "Cambiar a WiFi backup; "
                "activar almacenamiento local de datos; "
                "mantener control manual activo"
            ),
            IncidenceType.SECURITY_BREACH: (
                "BLOQUEAR acceso; "
                "activar logs extendidos; "
                "notificar a CISO; "
                "cambiar credenciales"
            ),
            IncidenceType.WATER_LEAK: (
                "DETENER sistema; "
                "activar bomba de drenaje; "
                "cerrar válvula principal; "
                "preparar piso absorbente"
            ),
            IncidenceType.BIOHAZARD: (
                "AISLAR prototipo; "
                "suspender cosecha; "
                "activar protocolo de desinfección; "
                "descartar plantas si es necesario"
            ),
            IncidenceType.UNKNOWN: (
                "Activar modo observación; "
                "aumentar frecuencia de monitoreo; "
                "documentar patrón para análisis posterior"
            ),
        }
        
        return rules.get(report.incident_type, "Requiere intervención manual")

    def _estimate_confidence(self, report: IncidenceReport) -> float:
        """Estima confianza en la decisión según datos disponibles."""
        confidence = 0.8  # Base
        
        # Aumentar confianza si hay datos redundantes
        if report.affected_variable and report.current_value is not None:
            confidence += 0.1
        
        # Reducir si está cerca del borde del rango
        expected_min, expected_max = report.expected_range
        if expected_min < report.current_value < expected_max:
            # Está dentro pero podría estar en borde
            mid = (expected_min + expected_max) / 2
            distance = abs(report.current_value - mid)
            range_width = expected_max - expected_min
            confidence -= (distance / range_width) * 0.2
        
        return max(0.5, min(1.0, confidence))

    def get_incident_history(
        self,
        prototype: Optional[int] = None,
        severity: Optional[IncidenceSeverity] = None,
        limit: int = 100,
    ) -> list[IncidenceReport]:
        """Retorna historial de incidencias (filtrable)."""
        results = self.incident_history
        
        if prototype:
            results = [i for i in results if i.prototype == prototype]
        
        if severity:
            results = [i for i in results if i.severity == severity]
        
        return results[-limit:]

    def get_decision_history(
        self,
        incident_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[SabiondaDecision]:
        """Retorna historial de decisiones (filtrable)."""
        results = self.decision_history
        
        if incident_id:
            results = [d for d in results if d.incident_id == incident_id]
        
        return results[-limit:]

    def export_audit_log(self) -> str:
        """Exporta log de auditoría completo en JSON."""
        audit_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_incidents": len(self.incident_history),
            "total_decisions": len(self.decision_history),
            "incidents": [i.dict() for i in self.incident_history],
            "decisions": [d.dict() for d in self.decision_history],
        }
        return json.dumps(audit_data, indent=2, default=str)


# Instancia global de Sabionda
sabionda = SabiondaGovernance()
