"""
Device Controllers — CASTÚO-SYSTEM v3.1
Controladores para actuadores de campo: bombas eléctricas, electroválvulas, sensores.

Arquitectura:
  - Cada controlador envía comandos al microservicio MQTT/LoRaWAN interno
    (configurable por entorno, sin URLs hardcoded)
  - Stub honesto: operaciones que requieren hardware real o integración con
    el gateway MQTT lanzan NotImplementedError hasta que el gateway esté desplegado.
  - Operaciones de solo-lectura (estado) y de bajo riesgo (logs) funcionan online.

Referencia:
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §1
  - DPIA-Robotics-2026 §4 (minimización de datos en actuadores)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Literal

logger = logging.getLogger(__name__)


def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            return ""
    return os.getenv(name, "")


_DEVICE_CMD_URL = os.getenv("CASTUO_IOT_DEVICE_CMD_URL", "")
_DEVICE_BEARER  = _read_secret("CASTUO_IOT_BEARER")


def _assert_gateway() -> None:
    """Lanza NotImplementedError si el gateway MQTT no está configurado."""
    if not _DEVICE_CMD_URL:
        raise NotImplementedError(
            "Requiere gateway MQTT desplegado: configurar CASTUO_IOT_DEVICE_CMD_URL "
            "en .env y desplegar el servicio mqtt-gateway en docker-compose."
        )


# ─── Bomba eléctrica ──────────────────────────────────────────────────────────

class PumpController:
    """
    Controlador para bombas eléctricas de riego/fertirrigación.

    Stub honesto: activa/desactiva la bomba vía MQTT gateway.
    Requiere CASTUO_IOT_DEVICE_CMD_URL configurado + gateway MQTT desplegado.
    """

    def __init__(self, device_id: str) -> None:
        if not device_id:
            raise ValueError("device_id no puede estar vacío")
        self.device_id = device_id

    def activate(self, flow_rate_lph: float) -> dict:
        """
        Activa la bomba con el caudal especificado en L/h.

        Raises:
            NotImplementedError: Si CASTUO_IOT_DEVICE_CMD_URL no está configurado.
            ValueError: Si flow_rate_lph <= 0.
        """
        _assert_gateway()
        if flow_rate_lph <= 0:
            raise ValueError(f"flow_rate_lph debe ser > 0, recibido: {flow_rate_lph}")

        logger.info("Activando bomba device=%s caudal=%.1f L/h", self.device_id, flow_rate_lph)
        return self._send_command("activate", {"flow_rate_lph": flow_rate_lph})

    def deactivate(self) -> dict:
        """
        Desactiva la bomba de forma segura (fail-safe = apagado).

        Raises:
            NotImplementedError: Si CASTUO_IOT_DEVICE_CMD_URL no está configurado.
        """
        _assert_gateway()
        logger.info("Desactivando bomba device=%s", self.device_id)
        return self._send_command("deactivate", {})

    def get_status(self) -> dict:
        """
        Lee el estado actual de la bomba desde el gateway.

        Raises:
            NotImplementedError: Si CASTUO_IOT_DEVICE_CMD_URL no está configurado.
        """
        _assert_gateway()
        return self._send_command("status", {})

    def _send_command(self, action: str, params: dict) -> dict:
        """Envía comando al gateway MQTT (implementación interna)."""
        import httpx

        payload = {
            "device_id": self.device_id,
            "device_type": "pump",
            "action": action,
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"Content-Type": "application/json"}
        if _DEVICE_BEARER:
            headers["Authorization"] = f"Bearer {_DEVICE_BEARER}"

        timeout = int(os.getenv("CASTUO_IOT_TIMEOUT_S", "10"))
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(_DEVICE_CMD_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()


# ─── Electroválvula ───────────────────────────────────────────────────────────

class ValveController:
    """
    Controlador para electroválvulas de riego por sectores.

    Stub honesto: controla apertura/cierre vía MQTT gateway.
    """

    ValveState = Literal["open", "closed"]

    def __init__(self, device_id: str) -> None:
        if not device_id:
            raise ValueError("device_id no puede estar vacío")
        self.device_id = device_id

    def open(self, aperture_pct: float = 100.0) -> dict:
        """
        Abre la electroválvula al porcentaje especificado.

        Args:
            aperture_pct: Porcentaje de apertura [0–100].

        Raises:
            NotImplementedError: Si gateway no configurado.
            ValueError: Si aperture_pct fuera de rango.
        """
        _assert_gateway()
        if not 0.0 < aperture_pct <= 100.0:
            raise ValueError(f"aperture_pct debe estar en (0, 100], recibido: {aperture_pct}")
        return self._send_command("open", {"aperture_pct": aperture_pct})

    def close(self) -> dict:
        """
        Cierra la electroválvula (fail-safe = cerrada).

        Raises:
            NotImplementedError: Si gateway no configurado.
        """
        _assert_gateway()
        return self._send_command("close", {})

    def get_state(self) -> dict:
        """
        Consulta el estado actual de la válvula.

        Raises:
            NotImplementedError: Si gateway no configurado.
        """
        _assert_gateway()
        return self._send_command("status", {})

    def _send_command(self, action: str, params: dict) -> dict:
        import httpx

        payload = {
            "device_id": self.device_id,
            "device_type": "valve",
            "action": action,
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"Content-Type": "application/json"}
        if _DEVICE_BEARER:
            headers["Authorization"] = f"Bearer {_DEVICE_BEARER}"

        timeout = int(os.getenv("CASTUO_IOT_TIMEOUT_S", "10"))
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(_DEVICE_CMD_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()


# ─── Sensor genérico ─────────────────────────────────────────────────────────

class SensorReader:
    """
    Lector para sensores de campo: temperatura, humedad, CO₂, EC, pH, luz.

    Stub honesto: lee datos desde el MQTT gateway.
    Compatible con: Raspberry Pi (GPIO/I2C/SPI), Arduino (USB/UART), LoRaWAN.
    """

    SUPPORTED_TYPES = ("temperature", "humidity", "co2", "ec", "ph", "light", "flow")

    def __init__(self, device_id: str, sensor_type: str) -> None:
        if not device_id:
            raise ValueError("device_id no puede estar vacío")
        if sensor_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"sensor_type '{sensor_type}' no soportado. Válidos: {self.SUPPORTED_TYPES}")
        self.device_id = device_id
        self.sensor_type = sensor_type

    def read(self) -> dict:
        """
        Lee el valor actual del sensor.

        Returns:
            dict con: device_id, sensor_type, value, unit, timestamp.

        Raises:
            NotImplementedError: Si CASTUO_IOT_DEVICE_CMD_URL no está configurado.
        """
        _assert_gateway()
        import httpx

        payload = {
            "device_id": self.device_id,
            "device_type": "sensor",
            "sensor_type": self.sensor_type,
            "action": "read",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        headers = {"Content-Type": "application/json"}
        if _DEVICE_BEARER:
            headers["Authorization"] = f"Bearer {_DEVICE_BEARER}"

        timeout = int(os.getenv("CASTUO_IOT_TIMEOUT_S", "10"))
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(_DEVICE_CMD_URL, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
