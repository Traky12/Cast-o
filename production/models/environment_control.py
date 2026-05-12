# -*- coding: utf-8 -*-
"""Modelos de datos para sensores de control ambiental (ozono, ósmosis, UV, nutrientes)."""
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel


class OzoneSensorData(BaseModel):
    """Datos del sensor de ozono (ppm)."""
    value: float
    threshold_min: float
    threshold_max: float
    status: str  # "normal", "warning", "critical"
    timestamp: datetime


class ReverseOsmosisData(BaseModel):
    """Datos del sistema de ósmosis inversa."""
    input_ec: float
    output_ec: float
    rejection_rate: float
    flow_rate: float
    filter_life: float
    timestamp: datetime


class UVLightData(BaseModel):
    """Datos de luz UV para esterilización."""
    intensity: float
    exposure_time: float
    status: str  # "on", "off", "fault"
    timestamp: datetime


class NutrientSolutionData(BaseModel):
    """Datos de la solución nutritiva para microgreens/brotes."""
    ec: float
    ph: float
    temperature: float
    orp: float
    do: Optional[float] = None
    timestamp: datetime


class EnvironmentalControlData(BaseModel):
    """Datos integrados de control ambiental."""
    tray_id: str
    crop_type: str
    growth_stage: str
    ozone: OzoneSensorData
    reverse_osmosis: ReverseOsmosisData
    uv_light: UVLightData
    nutrients: NutrientSolutionData
    co2: float
    temperature: float
    humidity: float
    timestamp: datetime
    gaiachain_tx: Optional[str] = None
