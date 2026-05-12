# -*- coding: utf-8 -*-
"""Sistema de control ambiental para cultivos hidropónicos (ozono, ósmosis, UV, nutrientes)."""
from datetime import datetime
from typing import Any, Dict, Optional

from production.models.environment_control import EnvironmentalControlData

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

import logging

logger = logging.getLogger(__name__)


class EnvironmentalControlSystem:
    """Sistema de control ambiental para cultivos hidropónicos avanzados."""

    def __init__(self, gaiachain_client: Optional[Any] = None):
        self.gaiachain = gaiachain_client
        self.thresholds = {
            "microgreens": {
                "ozone": {"min": 0.01, "max": 0.05},
                "ec": {"min": 0.8, "max": 1.2},
                "ph": {"min": 5.8, "max": 6.2},
                "temperature": {"min": 18, "max": 22},
                "humidity": {"min": 60, "max": 70},
                "co2": {"min": 400, "max": 800},
                "uv_intensity": {"min": 100, "max": 500},
                "orp": {"min": 200, "max": 400},
            },
            "brotes": {
                "ozone": {"min": 0.005, "max": 0.03},
                "ec": {"min": 0.6, "max": 1.0},
                "ph": {"min": 6.0, "max": 6.5},
                "temperature": {"min": 20, "max": 24},
                "humidity": {"min": 70, "max": 80},
                "co2": {"min": 300, "max": 600},
                "uv_intensity": {"min": 50, "max": 300},
            },
            "cannabis_vegetative": {
                "ozone": {"min": 0.01, "max": 0.04},
                "ec": {"min": 1.2, "max": 1.8},
                "ph": {"min": 5.5, "max": 6.0},
                "temperature": {"min": 20, "max": 26},
                "humidity": {"min": 50, "max": 70},
                "co2": {"min": 800, "max": 1200},
            },
        }

    def process_environmental_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa datos ambientales y genera comandos para actuadores."""
        try:
            env_data = EnvironmentalControlData(**data)
            crop_thresholds = self.thresholds.get(
                env_data.crop_type, self.thresholds["microgreens"]
            )

            commands: Dict[str, Any] = {}
            alerts: list = []

            if env_data.ozone.value < crop_thresholds["ozone"]["min"]:
                commands["ozone_generator"] = {
                    "action": "increase",
                    "target": crop_thresholds["ozone"]["min"],
                }
                alerts.append(
                    {
                        "type": "ozone_low",
                        "message": f"Nivel de ozono bajo: {env_data.ozone.value} ppm",
                        "severity": "warning",
                    }
                )
            elif env_data.ozone.value > crop_thresholds["ozone"]["max"]:
                commands["ozone_generator"] = {
                    "action": "decrease",
                    "target": crop_thresholds["ozone"]["max"],
                }
                alerts.append(
                    {
                        "type": "ozone_high",
                        "message": f"Nivel de ozono alto: {env_data.ozone.value} ppm",
                        "severity": "critical",
                    }
                )

            if env_data.reverse_osmosis.rejection_rate < 95:
                alerts.append(
                    {
                        "type": "ro_filter",
                        "message": f"Tasa de rechazo baja: {env_data.reverse_osmosis.rejection_rate}%",
                        "severity": "warning",
                    }
                )

            if env_data.nutrients.ec < crop_thresholds["ec"]["min"]:
                commands["nutrient_pump"] = {
                    "action": "increase_ec",
                    "target": crop_thresholds["ec"]["min"],
                }
                alerts.append(
                    {
                        "type": "low_ec",
                        "message": f"EC baja en nutrientes: {env_data.nutrients.ec} mS/cm",
                        "severity": "warning",
                    }
                )
            elif env_data.nutrients.ec > crop_thresholds["ec"]["max"]:
                commands["nutrient_pump"] = {
                    "action": "decrease_ec",
                    "target": crop_thresholds["ec"]["max"],
                }
                alerts.append(
                    {
                        "type": "high_ec",
                        "message": f"EC alta en nutrientes: {env_data.nutrients.ec} mS/cm",
                        "severity": "warning",
                    }
                )

            if env_data.nutrients.ph < crop_thresholds["ph"]["min"]:
                commands["ph_adjust"] = {
                    "action": "increase_ph",
                    "target": crop_thresholds["ph"]["min"],
                }
                alerts.append(
                    {
                        "type": "low_ph",
                        "message": f"pH bajo: {env_data.nutrients.ph}",
                        "severity": "warning",
                    }
                )
            elif env_data.nutrients.ph > crop_thresholds["ph"]["max"]:
                commands["ph_adjust"] = {
                    "action": "decrease_ph",
                    "target": crop_thresholds["ph"]["max"],
                }
                alerts.append(
                    {
                        "type": "high_ph",
                        "message": f"pH alto: {env_data.nutrients.ph}",
                        "severity": "warning",
                    }
                )

            if env_data.uv_light.status == "fault":
                alerts.append(
                    {
                        "type": "uv_fault",
                        "message": "Fallo en el sistema de luz UV",
                        "severity": "critical",
                    }
                )

            tx_hash = ""
            if self.gaiachain:
                payload = {
                    "tray_id": env_data.tray_id,
                    "crop_type": env_data.crop_type,
                    "data": env_data.model_dump() if hasattr(env_data, "model_dump") else env_data.dict(),
                    "commands": commands,
                    "alerts": alerts,
                    "timestamp": env_data.timestamp.isoformat(),
                }
                tx_hash = self.gaiachain.log_environmental_data(payload)

            return {
                "status": "success",
                "commands": commands,
                "alerts": alerts,
                "gaiachain_tx": tx_hash,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.exception("Error al procesar datos ambientales: %s", e)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def get_crop_thresholds(self, crop_type: str) -> Dict[str, Any]:
        """Obtiene los umbrales para un tipo de cultivo."""
        return self.thresholds.get(crop_type, self.thresholds["microgreens"])
