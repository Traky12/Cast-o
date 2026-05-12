# -*- coding: utf-8 -*-
"""Validador de cumplimiento con normativas canadienses (Health Canada, GPP, SFCR)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict


class CanadaComplianceValidator:
    """Valida cumplimiento con normativas canadienses."""

    def validate_health_canada(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida un lote de cannabis según Health Canada."""
        requirements = {
            "health_canada_license": batch_data.get("health_canada_license", False),
            "thc_under_03": batch_data.get("thc", 0.0) <= 0.3,
            "seed_to_sale_traceability": batch_data.get("blockchain_tx") is not None,
            "child_resistant_packaging": batch_data.get("child_resistant_packaging", False),
            "contaminant_testing": batch_data.get("contaminant_testing", False),
        }
        return {
            "standard": "CA_HealthCanada",
            "compliant": all(requirements.values()),
            "details": requirements,
            "validation_timestamp": datetime.utcnow().isoformat(),
        }

    def validate_canada_organic(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida un lote según Canada Organic Regime."""
        requirements = {
            "no_synthetic_pesticides": batch_data.get("no_synthetic_pesticides", False),
            "soil_building": batch_data.get("soil_building", False),
            "crop_rotation": batch_data.get("crop_rotation", False),
            "annual_inspections": batch_data.get("annual_inspections", False),
            "buffer_zones": batch_data.get("buffer_zones", False),
        }
        return {
            "standard": "CA_Organic",
            "compliant": all(requirements.values()),
            "details": requirements,
            "validation_timestamp": datetime.utcnow().isoformat(),
        }

    def validate_sfcr(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida un lote de microgreens según SFCR."""
        requirements = {
            "preventive_control_plan": batch_data.get("preventive_control_plan", False),
            "microbiological_testing": batch_data.get("microbiological_testing", False),
            "traceability_records": batch_data.get("traceability_records", False),
            "sanitation_program": batch_data.get("sanitation_program", False),
        }
        return {
            "standard": "CA_SFCR",
            "compliant": all(requirements.values()),
            "details": requirements,
            "validation_timestamp": datetime.utcnow().isoformat(),
        }
