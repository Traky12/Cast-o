# -*- coding: utf-8 -*-
"""
Endpoints FastAPI para recibir datos IoT de bandejas hidropónicas.
Registro en GaiaChain, análisis de sensores y comandos a actuadores.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient
from .iot_models import IoTSensorData, IoTDeviceAuth

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_gaiachain() -> GaiaChainClient:
    """Dependencia: cliente GaiaChain para registro de datos IoT."""
    return GaiaChainClient()


def _analyze_sensor_data(sensors: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza datos de sensores y genera comandos para actuadores.
    Control de riego (humedad), luz (etapa), alertas (temp, EC/pH).
    """
    commands: Dict[str, Any] = {}

    humidity = sensors.get("humidity") if sensors.get("humidity") is not None else 70
    if humidity < 60:
        commands["water_pump"] = 1
    else:
        commands["water_pump"] = 0

    growth_stage = (metadata.get("growth_stage") or "vegetative").lower()
    if growth_stage == "flowering":
        commands["grow_light"] = 100
    elif growth_stage == "vegetative" or growth_stage == "vegetativo":
        commands["grow_light"] = 80
    else:
        commands["grow_light"] = 50

    temperature = sensors.get("temperature") if sensors.get("temperature") is not None else 22
    if temperature < 18 or temperature > 28:
        commands["alert"] = {
            "type": "temperature",
            "message": f"Temperatura fuera de rango: {temperature}°C (óptimo: 18-28°C)",
            "severity": "high" if temperature < 15 or temperature > 30 else "medium",
        }

    ec = sensors.get("ec")
    ph = sensors.get("ph")
    if ec is not None and (ec < 1.0 or ec > 2.0):
        commands["alert"] = commands.get("alert") or {
            "type": "ec",
            "message": f"EC fuera de rango: {ec} mS/cm (óptimo: 1.0-2.0)",
            "severity": "high",
        }
    if ph is not None and (ph < 5.5 or ph > 6.5):
        commands["alert"] = commands.get("alert") or {
            "type": "ph",
            "message": f"pH fuera de rango: {ph} (óptimo: 5.5-6.5)",
            "severity": "high",
        }

    return commands


@router.post("/data", summary="Recibir datos de sensores IoT")
async def receive_iot_data(
    request: Request,
    data: Dict[str, Any],
    gaiachain: GaiaChainClient = Depends(get_gaiachain),
):
    """
    Recibe datos de sensores desde bandejas (Raspberry Pi).
    Registra en GaiaChain y devuelve comandos para actuadores.
    """
    try:
        session_id = data.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="Falta session_id")
        tray_id = data.get("tray_id")
        if not tray_id:
            raise HTTPException(status_code=400, detail="Falta tray_id")

        sensors = data.get("sensors", {})
        metadata = data.get("metadata", {})
        timestamp = data.get("timestamp", datetime.now().isoformat())

        tx_id = gaiachain.log_iot_data({
            "tray_id": tray_id,
            "timestamp": timestamp,
            "sensors": sensors,
            "metadata": metadata,
            "session_id": session_id,
        })

        commands = _analyze_sensor_data(sensors, metadata)

        return {
            "status": "success",
            "message": "Datos recibidos y procesados",
            "gaiachain_tx": tx_id,
            "commands": commands,
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error al procesar datos IoT")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/iot", summary="Autenticar dispositivo IoT")
async def authenticate_iot_device(
    request: Request,
    device_data: Dict[str, Any],
    gaiachain: GaiaChainClient = Depends(get_gaiachain),
):
    """
    Autentica un dispositivo IoT (Raspberry Pi) y devuelve session_id.
    """
    try:
        tray_id = device_data.get("tray_id")
        if not tray_id:
            raise HTTPException(status_code=400, detail="Falta tray_id")

        session_id = hashlib.sha256(
            f"{tray_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        gaiachain.log_iot_auth({
            "tray_id": tray_id,
            "session_id": session_id,
            "device_type": device_data.get("device_type", "raspberry_pi"),
            "location": device_data.get("location", "unknown"),
            "timestamp": datetime.now().isoformat(),
        })

        return {
            "status": "success",
            "session_id": session_id,
            "message": "Dispositivo IoT autenticado",
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error en autenticación IoT")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices", summary="Listar dispositivos IoT (stub)")
async def list_iot_devices(gaiachain: GaiaChainClient = Depends(get_gaiachain)):
    """Lista dispositivos activos (en producción: desde BD o GaiaChain)."""
    return {
        "devices": [
            {
                "tray_id": "CASTUO-TRAY-001",
                "status": "active",
                "last_seen": datetime.now().isoformat(),
                "location": "Invernadero Piloto, Cáceres",
            }
        ],
        "total": 1,
    }
