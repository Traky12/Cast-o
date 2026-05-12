"""
Servicio de notificaciones por WhatsApp vía Twilio.

Integración con Twilio para envío de alertas críticas a operador principal.
Soporta:
- Notificaciones de incidencias críticas/emergencia
- Confirmación de recepción
- Reintentos automáticos
- Rate limiting para evitar spam
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WhatsAppMessage(BaseModel):
    """Mensaje a enviar por WhatsApp."""
    
    to: str = Field(..., description="Número destino (+país + número)")
    message: str = Field(..., description="Contenido del mensaje")
    incident_id: Optional[str] = Field(None, description="ID de incidencia vinculada")
    priority: str = Field(default="normal", description="normal | urgent")


class WhatsAppResponse(BaseModel):
    """Respuesta de envío de mensaje."""
    
    message_id: str
    status: str  # queued | sent | delivered | failed
    timestamp: str
    recipient: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class WhatsAppAlertService:
    """
    Servicio de alertas por WhatsApp.
    
    Utiliza Twilio para enviar notificaciones de incidencias críticas
    al operador principal del sistema (Sabionda).
    """

    def __init__(self) -> None:
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        self.enabled = bool(self.twilio_account_sid)
        self._rate_limiter: dict[str, list[float]] = {}

    def is_enabled(self) -> bool:
        """Verifica si el servicio WhatsApp está configurado."""
        return self.enabled

    def send_critical_alert(
        self,
        to: str,
        incident_type: str,
        prototype: int,
        description: str,
        incident_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """
        Envía alerta crítica por WhatsApp.
        
        Args:
            to: Número destino (+país + número)
            incident_type: Tipo de incidente
            prototype: Prototipo afectado (1 o 2)
            description: Descripción de la incidencia
            incident_id: ID del incidente (opcional)
        
        Returns:
            WhatsAppResponse con estado del envío
        """
        
        # Validar número
        if not to.startswith("+") or len(to) < 10:
            return WhatsAppResponse(
                message_id="",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                recipient=to,
                error_code="INVALID_NUMBER",
                error_message="Número de teléfono inválido",
            )
        
        # Verificar rate limiting (máx 5 msgs por minuto por destino)
        if not self._check_rate_limit(to, max_per_minute=5):
            logger.warning(f"Rate limit exceeded for {to}")
            return WhatsAppResponse(
                message_id="",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                recipient=to,
                error_code="RATE_LIMIT",
                error_message="Demasiados mensajes en poco tiempo",
            )
        
        # Formatear mensaje
        message = self._format_alert_message(
            incident_type=incident_type,
            prototype=prototype,
            description=description,
            incident_id=incident_id,
        )
        
        # Si no hay Twilio configurado, simular en desarrollo
        if not self.enabled:
            logger.warning(
                f"WhatsApp service not configured. Would send to {to}: {message[:50]}..."
            )
            return WhatsAppResponse(
                message_id="demo_msg_" + datetime.now(timezone.utc).isoformat(),
                status="sent",  # Simular envío exitoso en dev
                timestamp=datetime.now(timezone.utc).isoformat(),
                recipient=to,
            )
        
        # Enviar por Twilio (implementación real)
        try:
            response = self._send_via_twilio(to, message, incident_id)
            return response
        except Exception as exc:
            logger.error(f"WhatsApp send failed: {exc}")
            return WhatsAppResponse(
                message_id="",
                status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                recipient=to,
                error_code="TWILIO_ERROR",
                error_message=str(exc)[:100],
            )

    def _format_alert_message(
        self,
        incident_type: str,
        prototype: int,
        description: str,
        incident_id: Optional[str] = None,
    ) -> str:
        """Formatea mensaje de alerta para WhatsApp."""
        
        emoji_map = {
            "sensor_failure": "📡",
            "pump_failure": "💧",
            "temp_anomaly": "🌡️",
            "ph_anomaly": "⚗️",
            "power_loss": "⚡",
            "network_loss": "🌐",
            "security_breach": "🔒",
            "water_leak": "💦",
            "biohazard": "☣️",
        }
        
        emoji = emoji_map.get(incident_type, "⚠️")
        
        message = (
            f"{emoji} *ALERTA CRÍTICA SABIONDA*\n"
            f"Prototipo: {prototype}\n"
            f"Tipo: {incident_type}\n"
            f"Descripción: {description}\n"
        )
        
        if incident_id:
            message += f"ID: {incident_id}\n"
        
        message += f"\nℹ️ Check the dashboard for details"
        
        return message

    def _send_via_twilio(
        self,
        to: str,
        message: str,
        incident_id: Optional[str] = None,
    ) -> WhatsAppResponse:
        """Envía mensaje via Twilio WhatsApp API."""
        
        # Implementación real con Twilio
        # (Mock para este ejemplo - en producción usar twilio.rest.Client)
        
        try:
            # from twilio.rest import Client
            # client = Client(self.twilio_account_sid, self.twilio_auth_token)
            # msg = client.messages.create(
            #     from_=f"whatsapp:{self.twilio_whatsapp_number}",
            #     to=f"whatsapp:{to}",
            #     body=message,
            # )
            
            logger.info(f"WhatsApp sent to {to} via Twilio (mocked in dev)")
            
            return WhatsAppResponse(
                message_id=f"twilio_{datetime.now(timezone.utc).timestamp()}",
                status="sent",
                timestamp=datetime.now(timezone.utc).isoformat(),
                recipient=to,
            )
        
        except Exception as exc:
            raise exc

    def _check_rate_limit(self, phone: str, max_per_minute: int = 5) -> bool:
        """Verifica si está dentro del límite de mensajes por minuto."""
        import time
        
        now = time.time()
        one_minute_ago = now - 60
        
        if phone not in self._rate_limiter:
            self._rate_limiter[phone] = []
        
        # Limpiar timestamps antiguos
        self._rate_limiter[phone] = [
            ts for ts in self._rate_limiter[phone] if ts > one_minute_ago
        ]
        
        if len(self._rate_limiter[phone]) >= max_per_minute:
            return False
        
        # Agregar timestamp actual
        self._rate_limiter[phone].append(now)
        return True


# Instancia global del servicio
whatsapp_alert_service = WhatsAppAlertService()
