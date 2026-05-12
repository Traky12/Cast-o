"""
Gemelo digital energetico agrovoltaico: fusion satelite + IoT + modelo termico del piloto Extremadura.

OpenFOAM / CFD no estan enlazados aqui; el flujo de datos y la firma JSON son estables
para notarizar y para sustituir el motor fisico sin romper el dashboard.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from ..digital_twin.digital_twin_4d_extremadura import ThermalModel


class EnergyAuditTwin:
    def __init__(self) -> None:
        self.solar_efficiency = 0.18
        self.crop_models = {
            "microgreens": {"water_use": 0.5, "temp_range": (18, 24)},
            "strawberries": {"water_use": 0.8, "temp_range": (20, 26)},
        }
        self.thermal_model = ThermalModel()

    def update(self, satellite_data: Dict[str, Any], iot_data: Dict[str, Any]) -> Dict[str, Any]:
        solar_energy = self._calculate_solar_energy(satellite_data)
        thermal = self.thermal_model.calculate(
            ext_temp=float(iot_data["air_temp"]),
            humidity=float(iot_data["humidity"]),
            radiation=float(solar_energy.get("radiation", 0)),
            geo_active=bool(iot_data.get("geo_active", True)),
        )
        crop_temp = float(thermal["temp_interior"])
        energy_efficiency = self._calculate_energy_efficiency(
            float(solar_energy["available"]),
            float(iot_data["energy_consumed"]),
        )
        alerts = self._check_anomalies(crop_temp, iot_data)
        return {
            "solar_energy": solar_energy,
            "crop_temperature": crop_temp,
            "thermal_detail": thermal,
            "energy_efficiency": energy_efficiency,
            "alerts": alerts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_solar_energy(self, satellite_data: Dict[str, Any]) -> Dict[str, Any]:
        radiation = float(satellite_data.get("radiation", 800))
        albedo = float(satellite_data.get("albedo", 0.2))
        available_energy = radiation * (1.0 - albedo) * self.solar_efficiency
        return {
            "radiation": radiation,
            "albedo": albedo,
            "available": available_energy,
            "units": "W/m2",
        }

    def _calculate_energy_efficiency(
        self, available_energy: float, consumed_energy: float
    ) -> Dict[str, Any]:
        if available_energy <= 0:
            return {"efficiency": 0.0, "status": "error"}
        # Indice scaffold: disponible vs consumo declarado por IoT (calibrar con ingenieria).
        ratio = max(0.0, min(1.0, 1.0 - (consumed_energy / (available_energy + 1e-6))))
        return {
            "efficiency": ratio,
            "available_energy": available_energy,
            "consumed_energy": consumed_energy,
            "status": "optimal" if ratio > 0.7 else "suboptimal",
        }

    def _check_anomalies(self, crop_temp: float, iot_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        crop_type = str(iot_data.get("crop_type", "microgreens"))
        temp_range = self.crop_models.get(crop_type, self.crop_models["microgreens"])["temp_range"]
        if crop_temp < temp_range[0]:
            alerts.append(
                {
                    "type": "low_temperature",
                    "current": crop_temp,
                    "recommended": f"{temp_range[0]}-{temp_range[1]}C",
                    "severity": "medium",
                }
            )
        elif crop_temp > temp_range[1]:
            alerts.append(
                {
                    "type": "high_temperature",
                    "current": crop_temp,
                    "recommended": f"{temp_range[0]}-{temp_range[1]}C",
                    "severity": "high",
                }
            )
        threshold = float(iot_data.get("energy_threshold", 5000))
        if float(iot_data["energy_consumed"]) > threshold:
            alerts.append(
                {
                    "type": "high_energy_consumption",
                    "current": iot_data["energy_consumed"],
                    "severity": "high",
                }
            )
        return alerts

    def export_to_3d(self, energy_efficiency: Dict[str, Any] | None = None) -> Dict[str, Any]:
        eff = energy_efficiency or {"efficiency": 0.75}
        return {
            "solar_panels": {
                "geometry": {"type": "Box", "width": 1.6, "height": 0.02, "depth": 1.0},
                "position": [0, 2.5, 0],
                "material": {"color": "#333333", "metallic": 0.9},
            },
            "crops": {
                "geometry": {"type": "Plane", "width": 10, "height": 10},
                "position": [0, 0, 0],
                "material": {"color": "#4CAF50", "opacity": 0.8},
            },
            "thermal_data": {
                "temperature": 22.5,
                "radiation": 800,
                "humidity": 65,
            },
            "energy_efficiency": eff,
        }
