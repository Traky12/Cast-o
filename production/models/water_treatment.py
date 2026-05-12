# -*- coding: utf-8 -*-
"""Modelos para tratamiento de agua y ósmosis inversa."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class WaterQualityData(BaseModel):
    """Datos de calidad del agua."""
    ec: float
    tds: float
    ph: float
    orp: float
    temperature: float
    turbidity: Optional[float] = None
    chlorine: Optional[float] = None
    timestamp: datetime


class ROSystemData(BaseModel):
    """Datos del sistema de ósmosis inversa."""
    input_water: WaterQualityData
    output_water: WaterQualityData
    rejection_rate: float
    flow_rate: float
    pressure: float
    filter_life: float
    maintenance_needed: bool
    timestamp: datetime


class WaterTreatmentLog(BaseModel):
    """Registro de tratamientos de agua."""
    treatment_id: str
    system: ROSystemData
    treatments_applied: List[str]
    post_treatment_quality: WaterQualityData
    operator: str
    timestamp: datetime
    gaiachain_tx: Optional[str] = None
