# -*- coding: utf-8 -*-
"""Modelos Pydantic para datos IoT (bandejas hidropónicas)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class IoTSensorData(BaseModel):
    """Datos de sensores enviados por el agente IoT."""

    session_id: str
    tray_id: str
    timestamp: str
    sensors: Dict[str, Any] = Field(default_factory=dict)
    actuators: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IoTCommand(BaseModel):
    """Comando enviado a un dispositivo IoT."""

    session_id: str
    timestamp: str
    commands: Dict[str, Any] = Field(default_factory=dict)


class IoTDeviceAuth(BaseModel):
    """Datos de autenticación de dispositivo IoT."""

    tray_id: str
    device_type: str = "raspberry_pi"
    location: str = "Cáceres, Extremadura"
