# -*- coding: utf-8 -*-
"""
Control de acceso físico — Seguridad física CASTUO 5.0.
Normativas: EN 50131, ISO 28000, UNE 104008. Registro en GaiaChain.
GPIO solo en Raspberry Pi; en otros entornos se simula.
"""
import hashlib
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    GPIO = None  # type: ignore

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class PhysicalAccessControl:
    """
    Control de acceso físico: sensor puerta, alarma, verificación huella/rostro.
    Registro en GaiaChain y notificación a equipo de seguridad (Slack/Telegram).
    """

    def __init__(self) -> None:
        self.gpio_pins = {
            "door_sensor": 17,
            "alarm": 27,
            "fingerprint_sensor": 22,
            "face_camera": 23,
        }
        self.authorized_users = self._load_authorized_users()
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self._alarm_active = False
        if HAS_GPIO and GPIO:
            self._setup_gpio()
        else:
            logger.info("GPIO no disponible (no Raspberry Pi); modo simulación")

    def _setup_gpio(self) -> None:
        """Configura pines GPIO para control de acceso."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.gpio_pins["door_sensor"], GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.gpio_pins["alarm"], GPIO.OUT)
            GPIO.output(self.gpio_pins["alarm"], GPIO.LOW)
        except Exception as e:
            logger.warning("GPIO setup error: %s", e)

    def _load_authorized_users(self) -> Dict[str, Dict[str, Any]]:
        """Carga usuarios autorizados (en producción desde GaiaChain/BD)."""
        return {
            "admin": {
                "fingerprint": hashlib.sha256(b"admin_fp").hexdigest()[:12],
                "face_hash": hashlib.sha256(b"admin_face").hexdigest()[:12],
                "access_level": 5,
            },
            "technician": {
                "fingerprint": hashlib.sha256(b"tech_fp").hexdigest()[:12],
                "face_hash": hashlib.sha256(b"tech_face").hexdigest()[:12],
                "access_level": 3,
            },
        }

    def verify_fingerprint(self, fingerprint_data: str) -> Tuple[Optional[str], int]:
        """Verifica huella frente a usuarios autorizados. Retorna (usuario, nivel) o (None, 0)."""
        fp_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:12]
        for user, data in self.authorized_users.items():
            if data.get("fingerprint") == fp_hash:
                return user, data.get("access_level", 0)
        return None, 0

    def verify_face(self, face_image: bytes) -> Tuple[Optional[str], int]:
        """Verifica rostro (hash de imagen; en producción usar modelo IA local)."""
        face_hash = hashlib.sha256(face_image).hexdigest()[:12]
        for user, data in self.authorized_users.items():
            if data.get("face_hash") == face_hash:
                return user, data.get("access_level", 0)
        return None, 0

    def grant_access(self, user: str, access_level: int) -> bool:
        """Otorga acceso físico y registra en GaiaChain."""
        if access_level < 1:
            self._trigger_alarm("Intento de acceso no autorizado")
            return False
        access_log = {
            "user": user,
            "timestamp": datetime.now().isoformat(),
            "access_level": access_level,
            "location": "Puerta Principal Invernadero",
            "verification_method": "biometric",
        }
        if self.blockchain:
            self.blockchain.log_physical_access(access_log)
        logger.info("Acceso concedido a %s (nivel %s)", user, access_level)
        return True

    def _trigger_alarm(self, reason: str) -> None:
        """Activa alarma física y notifica al equipo de seguridad."""
        self._alarm_active = True
        if HAS_GPIO and GPIO:
            try:
                GPIO.output(self.gpio_pins["alarm"], GPIO.HIGH)
                import time
                time.sleep(5)
                GPIO.output(self.gpio_pins["alarm"], GPIO.LOW)
            except Exception as e:
                logger.warning("GPIO alarm error: %s", e)
        self._notify_security_team(reason)
        self._alarm_active = False

    def _notify_security_team(self, reason: str) -> None:
        """Notifica al equipo de seguridad (Slack/Telegram vía webhook)."""
        webhook = os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("CASTUO_SLACK_WEBHOOK", "")
        if not webhook:
            logger.warning("Sin webhook configurado para alertas de seguridad física")
            return
        try:
            import urllib.request
            import json
            payload = json.dumps({
                "text": "ALERTA DE SEGURIDAD FÍSICA",
                "attachments": [{
                    "title": "Intento de acceso no autorizado",
                    "color": "danger",
                    "fields": [
                        {"title": "Ubicación", "value": "Puerta Principal Invernadero 1", "short": True},
                        {"title": "Hora", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True},
                        {"title": "Razón", "value": reason, "short": False},
                    ],
                }],
            }).encode("utf-8")
            req = urllib.request.Request(
                webhook,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as r:
                r.read()
        except Exception as e:
            logger.warning("Notificación seguridad: %s", e)

    def monitor_door(self) -> None:
        """Bucle de monitoreo del sensor de puerta (en producción corre en servicio)."""
        if not HAS_GPIO or not GPIO:
            logger.info("monitor_door: modo simulación (sin GPIO)")
            return
        import time
        while True:
            try:
                if GPIO.input(self.gpio_pins["door_sensor"]) == GPIO.LOW:
                    time.sleep(0.1)
                    if GPIO.input(self.gpio_pins["door_sensor"]) == GPIO.LOW:
                        logger.warning("Puerta abierta — esperando autenticación")
                        # En producción: esperar verificación biométrica vía API/serial
                        user, level = self.verify_fingerprint("scan_placeholder")
                        if user and self.grant_access(user, level):
                            time.sleep(10)
                        else:
                            self._trigger_alarm("Puerta forzada sin autenticación")
            except Exception as e:
                logger.warning("monitor_door: %s", e)
            time.sleep(0.1)
