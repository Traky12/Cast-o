# -*- coding: utf-8 -*-
"""
Sensores sísmicos — Detección de excavaciones/túneles en perímetro.
EN 50131-2-8. Registro en GaiaChain (alertas y eventos de normalización).
"""
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except ImportError:
    HAS_GPIO = False
    GPIO = None  # type: ignore


class SeismicSensor:
    """
    Monitoreo de vibraciones (geófonos); en producción usar ADC para valor analógico.
    Al superar umbral: alerta en GaiaChain y notificación Slack/Telegram.
    """

    def __init__(self, gpio_pin: int = 23, threshold: float = 50.0) -> None:
        self.gpio_pin = gpio_pin
        self.threshold = threshold
        self.blockchain = GaiaChainClient() if GaiaChainClient else None
        self.alert_active = False
        if HAS_GPIO and GPIO:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_pin, GPIO.IN)
            except Exception as e:
                logger.warning("GPIO setup error: %s", e)

    def _read_vibration(self) -> float:
        """Lee nivel de vibración (0–1023 con ADC; aquí simulado si no hay GPIO)."""
        if HAS_GPIO and GPIO:
            # Digital: 0 o 1; en producción conectar ADC (MCP3008 etc.) para valor analógico
            return float(GPIO.input(self.gpio_pin)) * 500.0
        # Simulación para pruebas sin hardware
        return (time.time() % 100) * 10.0

    def _trigger_alarm(self, alert_data: Dict[str, Any]) -> None:
        if self.blockchain:
            self.blockchain.log_security_alert({
                "type": "seismic_alert",
                "node_id": "seismic",
                "severity": "high",
                **alert_data,
            })
        logger.warning("ALERTA SÍSMICA: %s", alert_data)
        webhook = os.environ.get("SLACK_WEBHOOK_URL") or os.environ.get("CASTUO_SLACK_WEBHOOK", "")
        if webhook:
            try:
                import urllib.request
                import json
                payload = json.dumps({
                    "text": "ALERTA DE INTRUSIÓN SÍSMICA",
                    "attachments": [{
                        "title": "Posible intento de excavación/túnel",
                        "color": "danger",
                        "fields": [
                            {"title": "Ubicación", "value": alert_data.get("location", ""), "short": True},
                            {"title": "Nivel", "value": f"{alert_data.get('value')} (umbral: {alert_data.get('threshold')})", "short": True},
                            {"title": "Hora", "value": alert_data.get("timestamp", ""), "short": True},
                        ],
                    }],
                }).encode("utf-8")
                req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=5) as r:
                    r.read()
            except Exception as e:
                logger.warning("Notificación Slack: %s", e)

    def monitor(self) -> None:
        """Bucle de monitoreo: alerta si vibración > umbral; registra normalización."""
        logger.info("Monitoreando sensores sísmicos GPIO %s (umbral: %s)", self.gpio_pin, self.threshold)
        try:
            while True:
                vibration_level = self._read_vibration()
                if vibration_level > self.threshold and not self.alert_active:
                    self.alert_active = True
                    alert_data = {
                        "sensor": "seismic",
                        "location": "Perímetro Invernadero 1 (Sector Norte)",
                        "value": vibration_level,
                        "threshold": self.threshold,
                        "timestamp": datetime.now().isoformat(),
                        "status": "possible_tunneling",
                    }
                    self._trigger_alarm(alert_data)
                elif vibration_level <= self.threshold and self.alert_active:
                    self.alert_active = False
                    resolve_data = {
                        "sensor": "seismic",
                        "location": "Perímetro Invernadero 1 (Sector Norte)",
                        "value": vibration_level,
                        "timestamp": datetime.now().isoformat(),
                        "status": "normalized",
                    }
                    if self.blockchain:
                        self.blockchain.log_security_event(resolve_data)
                    logger.info("Vibraciones normalizadas (%s <= %s)", vibration_level, self.threshold)
                time.sleep(0.5)
        except KeyboardInterrupt:
            if HAS_GPIO and GPIO:
                GPIO.cleanup()
            logger.info("Monitoreo sísmico detenido.")
