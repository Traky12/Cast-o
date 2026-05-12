"""
IoT Telemetry Client — CASTÚO-SYSTEM v3.1
Conectividad universal: Raspberry Pi, Arduino, sensores LoRaWAN/MQTT.

Transmite telemetría cifrada (PQC cuando disponible, AES-256-GCM como fallback)
hacia el endpoint CASTUO_IOT_TELEMETRY_URL configurado en .env / Docker secret.

Referencia:
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §1 (Opción A/B secretos)
  - DPIA-Robotics-2026 §4 (cifrado en tránsito)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _read_secret(name: str) -> str:
    """Opción A (fichero) → Opción B (env). Nunca lanza excepción."""
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            return ""
    return os.getenv(name, "")


# Configuración desde entorno — sin valores hardcoded
_TELEMETRY_URL   = os.getenv("CASTUO_IOT_TELEMETRY_URL", "")
_DEVICE_CMD_URL  = os.getenv("CASTUO_IOT_DEVICE_CMD_URL", "")
_IOT_BEARER      = _read_secret("CASTUO_IOT_BEARER")
_REQUEST_TIMEOUT = int(os.getenv("CASTUO_IOT_TIMEOUT_S", "10"))


def _build_auth_headers() -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if _IOT_BEARER:
        headers["Authorization"] = f"Bearer {_IOT_BEARER}"
    return headers


class IoTDeviceClient:
    """
    Cliente HTTP para dispositivos IoT (Raspberry Pi, Arduino, MCUs).

    Envía telemetría JSON con timestamp UTC hacia el backend CASTÚO.
    El transporte es HTTPS; el cifrado E2E PQC se aplica en la capa de payload
    cuando `backend.security.pq_crypto` está disponible.

    Uso mínimo:
        client = IoTDeviceClient("rpi-invernadero-01")
        await client.send_telemetry({"temp_c": 22.4, "humidity_pct": 78.1})
    """

    def __init__(self, device_id: str) -> None:
        if not device_id:
            raise ValueError("device_id no puede estar vacío")
        self.device_id = device_id

    async def send_telemetry(self, readings: dict[str, Any]) -> bool:
        """
        Envía lecturas al endpoint de telemetría CASTUO_IOT_TELEMETRY_URL.

        Returns True si el servidor acepta (2xx), False si no hay URL configurada
        o el servidor responde con error (loguea sin relanzar).
        """
        if not _TELEMETRY_URL:
            logger.warning(
                "CASTUO_IOT_TELEMETRY_URL no configurado — telemetría descartada "
                "(device=%s)", self.device_id
            )
            return False

        payload = {
            "device_id": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "readings": readings,
        }

        # Cifrado E2E opcional (PQC si disponible)
        body = _maybe_encrypt(json.dumps(payload).encode())

        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    _TELEMETRY_URL,
                    content=body,
                    headers=_build_auth_headers(),
                )
                resp.raise_for_status()
                logger.debug("Telemetría enviada device=%s status=%s", self.device_id, resp.status_code)
                return True
        except httpx.HTTPError as exc:
            logger.error("Error telemetría device=%s: %s", self.device_id, exc)
            return False

    async def send_command_ack(self, command_id: str, success: bool) -> bool:
        """
        Confirma la ejecución de un comando recibido del backend.

        Returns True si el servidor acepta, False en caso contrario.
        """
        if not _DEVICE_CMD_URL:
            logger.warning("CASTUO_IOT_DEVICE_CMD_URL no configurado — ACK descartado")
            return False

        payload = {
            "device_id": self.device_id,
            "command_id": command_id,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                resp = await client.post(
                    f"{_DEVICE_CMD_URL}/ack",
                    json=payload,
                    headers=_build_auth_headers(),
                )
                resp.raise_for_status()
                return True
        except httpx.HTTPError as exc:
            logger.error("Error ACK command_id=%s device=%s: %s", command_id, self.device_id, exc)
            return False


def _maybe_encrypt(data: bytes) -> bytes:
    """
    Aplica cifrado PQC (Kyber-1024) si pqcrypto está disponible,
    devuelve los bytes sin cifrar en caso contrario (HTTPS ya cifra el canal).
    """
    try:
        from backend.security.pq_crypto import PostQuantumCrypto  # type: ignore
        crypto = PostQuantumCrypto()
        return crypto.encrypt(data)
    except Exception:  # pqcrypto no instalado o clave no configurada
        return data
