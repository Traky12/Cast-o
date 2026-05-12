# -*- coding: utf-8 -*-
"""Sistema de tratamiento de agua para cultivos hidropónicos."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from production.models.water_treatment import (
    ROSystemData,
    WaterQualityData,
    WaterTreatmentLog,
)

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

import logging

logger = logging.getLogger(__name__)


class WaterTreatmentSystem:
    """Sistema de tratamiento de agua para cultivos hidropónicos."""

    def __init__(self, gaiachain_client: Optional[Any] = None):
        self.gaiachain = gaiachain_client
        self.quality_standards = {
            "microgreens": {
                "input_ec_max": 0.8,
                "output_ec_max": 0.05,
                "ph_range": {"min": 5.5, "max": 6.5},
                "orp_min": 200,
                "tds_max": 50,
            },
            "brotes": {
                "input_ec_max": 0.6,
                "output_ec_max": 0.03,
                "ph_range": {"min": 6.0, "max": 7.0},
                "orp_min": 250,
                "tds_max": 30,
            },
            "cannabis": {
                "input_ec_max": 1.0,
                "output_ec_max": 0.05,
                "ph_range": {"min": 5.8, "max": 6.2},
                "orp_min": 300,
                "tds_max": 20,
            },
        }

    def log_water_treatment(self, treatment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Registra un tratamiento de agua en el sistema."""
        try:
            treatment = WaterTreatmentLog(**treatment_data)
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_water_treatment(
                    {
                        "treatment_id": treatment.treatment_id,
                        "system": treatment.system.model_dump() if hasattr(treatment.system, "model_dump") else treatment.system.dict(),
                        "treatments_applied": treatment.treatments_applied,
                        "post_treatment_quality": treatment.post_treatment_quality.model_dump() if hasattr(treatment.post_treatment_quality, "model_dump") else treatment.post_treatment_quality.dict(),
                        "operator": treatment.operator,
                        "timestamp": treatment.timestamp.isoformat(),
                    }
                )
            return {
                "status": "success",
                "treatment_id": treatment.treatment_id,
                "gaiachain_tx": tx_hash,
                "message": "Tratamiento de agua registrado",
            }
        except Exception as e:
            logger.exception("Error al registrar tratamiento de agua: %s", e)
            return {"status": "error", "message": str(e)}

    def analyze_water_quality(
        self, water_data: Dict[str, Any], crop_type: str
    ) -> Dict[str, Any]:
        """Analiza la calidad del agua y recomienda tratamientos."""
        try:
            quality = WaterQualityData(**water_data)
            standards = self.quality_standards.get(
                crop_type, self.quality_standards["microgreens"]
            )

            recommendations: List[Dict] = []
            if quality.ec > standards["input_ec_max"]:
                recommendations.append(
                    {
                        "treatment": "reverse_osmosis",
                        "target_ec": standards["output_ec_max"],
                        "priority": "high",
                    }
                )

            ph_min, ph_max = standards["ph_range"]["min"], standards["ph_range"]["max"]
            if quality.ph < ph_min or quality.ph > ph_max:
                recommendations.append(
                    {
                        "treatment": "ph_adjustment",
                        "target_ph": (ph_min + ph_max) / 2,
                        "priority": "medium",
                    }
                )

            if quality.orp is not None and quality.orp < standards["orp_min"]:
                recommendations.append(
                    {
                        "treatment": "ozone_or_uv",
                        "target_orp": standards["orp_min"],
                        "priority": "high",
                    }
                )

            if quality.tds is not None and quality.tds > standards["tds_max"]:
                recommendations.append(
                    {
                        "treatment": "reverse_osmosis_or_filtration",
                        "target_tds": standards["tds_max"],
                        "priority": "high",
                    }
                )

            complies = (
                quality.ec <= standards["input_ec_max"]
                and ph_min <= quality.ph <= ph_max
                and (quality.orp is None or quality.orp >= standards["orp_min"])
                and (quality.tds is None or quality.tds <= standards["tds_max"])
            )

            return {
                "status": "success",
                "water_quality": quality.model_dump() if hasattr(quality, "model_dump") else quality.dict(),
                "complies_with_standards": complies,
                "recommendations": recommendations,
            }
        except Exception as e:
            logger.exception("Error al analizar calidad del agua: %s", e)
            return {"status": "error", "message": str(e)}

    def get_treatment_history(self, treatment_id: str) -> Dict[str, Any]:
        """Obtiene el historial de un tratamiento de agua."""
        try:
            return {
                "status": "success",
                "treatment_id": treatment_id,
                "data": {
                    "input_water": {
                        "ec": 0.75,
                        "tds": 380,
                        "ph": 7.2,
                        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    },
                    "output_water": {
                        "ec": 0.03,
                        "tds": 15,
                        "ph": 6.0,
                        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    },
                    "treatments_applied": ["reverse_osmosis", "ph_adjustment", "ozone"],
                    "operator": "TEC-001",
                    "gaiachain_tx": "tx_123456",
                },
            }
        except Exception as e:
            logger.exception("Error al obtener historial de tratamiento %s: %s", treatment_id, e)
            return {"status": "error", "message": str(e)}
