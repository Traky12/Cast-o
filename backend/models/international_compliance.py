# -*- coding: utf-8 -*-
"""Modelos base para cumplimiento normativo internacional."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InternationalStandard(BaseModel):
    """Estándar normativo internacional (JAS, KFDA, Health Canada, etc.)."""

    standard_id: str = ""
    name: str = ""
    country: str = ""
    description: str = ""
    requirements: List[str] = Field(default_factory=list)
    applicable_to: List[str] = Field(default_factory=list)  # ["cannabis", "microgreens"]
    validation_endpoint: Optional[str] = None


class CountrySpecificRules(BaseModel):
    """Reglas específicas por país para exportación."""

    country_code: str = ""
    language: str = "en"
    currency: str = "EUR"
    time_zone: str = "Europe/Madrid"
    cannabis_standards: List[InternationalStandard] = Field(default_factory=list)
    microgreens_standards: List[InternationalStandard] = Field(default_factory=list)
    tax_rules: Dict[str, Any] = Field(default_factory=dict)
    import_restrictions: List[str] = Field(default_factory=list)
    labeling_requirements: List[str] = Field(default_factory=list)


# Registro global de reglas por país (se actualiza desde asia_compliance y canada_compliance)
country_rules_db: Dict[str, CountrySpecificRules] = {}
