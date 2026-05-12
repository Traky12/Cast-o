# -*- coding: utf-8 -*-
"""Modelos para microgreens y brotes con trazabilidad."""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class MicrogreenVariety(BaseModel):
    """Variedad de microgreen con parámetros específicos."""
    name: str
    scientific_name: str
    germination_days: int
    harvest_days: int
    ideal_temperature: Dict[str, float]
    ideal_humidity: Dict[str, float]
    ideal_ec: Dict[str, float]
    ideal_ph: Dict[str, float]
    light_requirements: Dict[str, float]
    seed_density: float
    yield_kg_per_m2: float


class MicrogreenBatch(BaseModel):
    """Lote de microgreens con trazabilidad completa."""
    batch_id: str
    variety: MicrogreenVariety
    tray_id: str
    start_date: datetime
    germination_date: Optional[datetime] = None
    harvest_date: Optional[datetime] = None
    status: str  # "seeding", "germinating", "growing", "harvested"
    environmental_data: List[Dict] = []
    quality_checks: List[Dict] = []
    gaiachain_tx: Optional[str] = None
    certificate: Optional[str] = None
