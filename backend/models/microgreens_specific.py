# -*- coding: utf-8 -*-
"""Modelos específicos para microgreens (alta rotación, GlobalGAP)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


class MicrogreenVariety(BaseModel):
    """Variedad de microgreen con parámetros de cultivo."""

    variety_id: str = ""
    name: str = ""
    scientific_name: str = ""
    growth_cycle: int = Field(7, ge=1, le=30)  # días hasta cosecha
    ideal_ph: float = Field(6.0, ge=4.0, le=8.0)
    ideal_ec: float = Field(1.2, ge=0, le=5.0)  # mS/cm
    ideal_temperature: Tuple[float, float] = (18.0, 22.0)  # °C min, max
    ideal_humidity: Tuple[float, float] = (60.0, 70.0)  # % min, max
    nutritional_value: Dict[str, str] = Field(default_factory=dict)
    certification_standards: List[str] = Field(
        default_factory=lambda: ["ISO_22000", "GlobalGAP", "Organic_EU"]
    )


class MicrogreenBatch(BaseModel):
    """Lote de microgreens con trazabilidad."""

    batch_id: str = ""
    account_id: Optional[str] = None  # Cuenta Pro (para listados)
    variety: MicrogreenVariety = Field(default_factory=MicrogreenVariety)
    tray_id: str = ""
    planting_date: datetime = Field(default_factory=datetime.utcnow)
    harvest_date: Optional[datetime] = None
    weight: Optional[float] = None  # gramos
    environmental_data: Optional[Dict[str, float]] = None
    blockchain_tx: Optional[str] = None
    certification_status: Literal["pending", "approved", "rejected"] = "pending"
    status: Literal[
        "planted", "germinating", "growing", "harvested", "packed", "shipped"
    ] = "planted"


class MicrogreenCertificate(BaseModel):
    """Certificado de calidad para microgreens."""

    certificate_id: str = ""
    batch_id: str = ""
    variety: str = ""
    weight: float = 0.0  # gramos
    harvest_date: datetime = Field(default_factory=datetime.utcnow)
    environmental_compliance: Dict[str, Any] = Field(default_factory=dict)
    organic_status: bool = True
    blockchain_tx: str = ""
    issued_by: str = ""
    issue_date: datetime = Field(default_factory=datetime.utcnow)
    expiration_date: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(days=365)
    )
    qr_code: str = ""
