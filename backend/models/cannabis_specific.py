# -*- coding: utf-8 -*-
"""Modelos específicos para cannabis medicinal (RD 903/2025, AEMPS)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CannabisStrain(BaseModel):
    """Variedad de cannabis medicinal con parámetros regulados."""

    strain_id: str = ""
    name: str = ""
    thc_percentage: float = Field(0.0, ge=0, le=100, description="% THC (límite UE <0.3% para no medicinal)")
    cbd_percentage: float = Field(0.0, ge=0, le=100)
    cultivation_license: str = ""  # Número de licencia AEMPS
    batch_size: int = Field(0, ge=0)
    harvest_date: Optional[datetime] = None
    certification_status: Literal["pending", "approved", "rejected"] = "pending"
    compliance_standards: List[str] = Field(
        default_factory=lambda: ["RD_903_2025", "GMP", "ISO_22000", "AEMPS_Compliance"]
    )


class CannabisBatch(BaseModel):
    """Lote de cannabis con trazabilidad completa."""

    batch_id: str = ""
    account_id: Optional[str] = None  # Cuenta Pro que creó el lote (para listados)
    strain: CannabisStrain = Field(default_factory=CannabisStrain)
    cultivation_site: str = ""
    planting_date: datetime = Field(default_factory=datetime.utcnow)
    harvest_date: Optional[datetime] = None
    weight: float = 0.0  # kg
    lab_test_results: Optional[Dict[str, Any]] = None
    blockchain_tx: Optional[str] = None
    certification_date: Optional[datetime] = None
    certification_status: Literal["pending", "approved", "rejected"] = "pending"
    status: Literal[
        "planted", "growing", "harvested", "drying", "certified", "shipped"
    ] = "planted"


class CannabisLicense(BaseModel):
    """Licencia de cultivo de cannabis medicinal (AEMPS)."""

    license_id: str = ""
    holder: str = ""
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime = Field(default_factory=datetime.utcnow)
    allowed_strains: List[str] = Field(default_factory=list)
    max_cultivation_area: float = Field(0.0, ge=0)  # m²
    aemps_reference: str = ""
    status: Literal["active", "suspended", "revoked"] = "active"
    blockchain_tx: Optional[str] = None
