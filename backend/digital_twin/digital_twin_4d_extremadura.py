"""
Gemelo Digital 4D (scaffold) para el piloto Extremadura 2026.

Diseno del modulo:
- Entrada: lecturas de sensores (dict).
- Salida: thermal_data, structural_data, alerts y timestamp.
- Export 3D/4D: genera un dict de geometria + materiales para que un frontend
  (Three.js/Unity) lo pinte o lo transforme.

Nota:
El repo actual no incluye CFD OpenFOAM ni simulacion estructural CalculiX como
dependencias operativas. Este motor implementa un modelo simplificado
(escalares y reglas heuristicas) para que:
  - El flujo de integracion quede claro.
  - GaiaChain pueda notarizar versiones del modelo/estimaciones.
  - La integracion posterior con CFD/FEA se haga sin romper interfaces.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class ThermalModel:
    """
    Modelo termico simplificado:
    - terracota amortigua picos -> reduce delta ext-int en funcion de humedad y radiacion.
    - geotermia aporta estabilidad -> si la geotermia esta "activa" (entrada opcional).
    """

    target_min: float = 10.0
    target_max: float = 40.0

    def calculate(
        self,
        ext_temp: float,
        humidity: float,
        radiation: float = 0.0,
        geo_active: bool = True,
    ) -> Dict[str, Any]:
        # Efecto humedad: mas humedad tiende a amortiguar (heuristica).
        humidity_factor = (humidity / 100.0)  # 0..1

        # Efecto radiacion: mayor radiacion sube temp "efectiva" de la cubierta.
        radiation_factor = _clamp(radiation / 1000.0, 0.0, 1.5)

        # Terracota: reduce el impacto de ext_temp en el interior.
        # Cuanto mas humedad y menos radiacion, mayor amortiguacion.
        cooling_strength = 0.35 + 0.25 * humidity_factor - 0.15 * radiation_factor
        cooling_strength = _clamp(cooling_strength, 0.15, 0.75)

        base_interior = ext_temp - (ext_temp - 20.0) * cooling_strength

        # Geotermia somera: estabilidad extra (si aplica).
        if geo_active:
            # Estabiliza acercando a un "setpoint" de 18.0..22.0.
            geo_target = 19.5 + 0.5 * (1.0 - humidity_factor)
            base_interior = base_interior * 0.7 + geo_target * 0.3

        # Clamp fisico/operativo.
        temp_interior = _clamp(base_interior, self.target_min, self.target_max)
        cooling_source = "geotermia" if geo_active else "terracota"

        return {
            "temp_exterior": float(ext_temp),
            "temp_interior": float(temp_interior),
            "humidity_factor": float(humidity_factor),
            "radiation_factor": float(radiation_factor),
            "cooling_source": cooling_source,
        }


@dataclass
class StructuralModel:
    """
    Modelo estructural simplificado:
    - stress relativo en funcion de delta termico y un factor de viento si existe.
    """

    def calculate(
        self,
        temp_interior: float,
        ext_temp: float,
        wind_speed: float = 0.0,
    ) -> Dict[str, Any]:
        delta = abs(float(temp_interior) - float(ext_temp))
        wind_factor = _clamp(float(wind_speed) / 10.0, 0.0, 1.0)

        # Heuristica: delta mas wind -> mayor stress relativo.
        stress = _clamp((delta / 20.0) * (0.7 + 0.3 * wind_factor), 0.0, 1.0)
        deformation = stress * 0.01  # unitless placeholder

        return {
            "stress": float(stress),
            "deformation": float(deformation),
            "delta_temp": float(delta),
        }


@dataclass
class DigitalTwin4DExtremadura:
    thermal_model: ThermalModel = field(default_factory=ThermalModel)
    structural_model: StructuralModel = field(default_factory=StructuralModel)
    time_series: List[Dict[str, Any]] = field(default_factory=list)

    def update(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza gemelo con datos de sensores.

        Requisitos de entrada (keys):
        - temp_exterior (float)
        - humidity (float)
        Opcionales:
        - radiation (float)
        - wind_speed (float)
        - geo_active (bool)
        """
        ext_temp = float(sensor_data.get("temp_exterior", 0.0))
        humidity = float(sensor_data.get("humidity", 0.0))
        radiation = float(sensor_data.get("radiation", 0.0))
        wind_speed = float(sensor_data.get("wind_speed", 0.0))
        geo_active = bool(sensor_data.get("geo_active", True))

        thermal_result = self.thermal_model.calculate(
            ext_temp=ext_temp,
            humidity=humidity,
            radiation=radiation,
            geo_active=geo_active,
        )

        structural_result = self.structural_model.calculate(
            temp_interior=thermal_result["temp_interior"],
            ext_temp=thermal_result["temp_exterior"],
            wind_speed=wind_speed,
        )

        timestamp = datetime.now(timezone.utc).isoformat()

        # 4D: guarda historial
        record = {
            "timestamp": timestamp,
            "thermal": thermal_result,
            "structural": structural_result,
            "sensor_data": dict(sensor_data),
        }
        self.time_series.append(record)

        alerts: List[str] = []
        if float(thermal_result["temp_interior"]) > 26.0:
            alerts.append("ALERT: Temp interior > 26C")
        if float(structural_result["stress"]) > 0.8:
            alerts.append("ALERT: Stress estructural > 80%")

        status = "OK" if not alerts else "WARNING"

        return {
            "status": status,
            "thermal_data": thermal_result,
            "structural_data": structural_result,
            "alerts": alerts,
            "timestamp": timestamp,
        }

    def get_time_series(self, hours: int = 24) -> List[Dict[str, Any]]:
        # Scaffold simple: recorta ultimos N registros. En integracion real,
        # se filtra por tiempo.
        if not hours:
            return self.time_series
        # Asumiendo 1 update por hora en el scaffold.
        max_records = int(hours)
        if max_records <= 0:
            return self.time_series
        return self.time_series[-max_records:]

    def export_to_3d(self, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporta datos para modelado 3D/visualizacion.

        Devuelve:
        - geometry: terracota_modules, pv_panels, geotermia_pipes
        - materials: paleta coloreada segun stress
        - thermal_data / structural_data / sensor_data de la instantanea
        """
        if not self.time_series:
            raise ValueError("time_series vacio: ejecuta update() primero")

        record = self.time_series[-1]
        if timestamp:
            # Busca exacto; en integracion real usar tolerancia.
            for r in reversed(self.time_series):
                if r.get("timestamp") == timestamp:
                    record = r
                    break

        thermal = record["thermal"]
        structural = record["structural"]
        sensor = record["sensor_data"]
        stress = float(structural.get("stress", 0.0))
        pv_power_w = float(sensor.get("pv_power", sensor.get("pv_power_w", 0.0)))

        # Geometria parametricamente simple (placeholders del piloto).
        terracota_modules = {
            "type": "Box",
            "width": 0.8,
            "height": 0.1,
            "depth": 0.4,
            "position": [0.0, 0.05, 0.0],
            "color_scale": min(1.0, stress * 1.25),
        }
        pv_panels = {
            "type": "Box",
            "width": 1.6,
            "height": 0.02,
            "depth": 1.0,
            "position": [0.0, 2.5, 0.0],
            "rotation": [0.0, 0.0, -15.0],
            "color_scale": min(1.0, pv_power_w / 5000.0 if pv_power_w > 0 else 0.0),
        }
        geotermia_pipes = {
            "type": "Cylinder",
            "radius": 0.05,
            "length": 2.0,
            "position": [0.0, 0.0, -1.0],
        }

        materials = {
            "terracota": {"base_color": [0.7, 0.6, 0.5], "stress": stress},
            "pv_panels": {"base_color": [0.2, 0.2, pv_panels["color_scale"]], "metallic": 0.9},
            "geotermia_pipes": {"base_color": [1.0, 0.3, 0.3], "opacity": 0.7},
        }

        return {
            "geometry": {
                "terracota_modules": terracota_modules,
                "pv_panels": pv_panels,
                "geotermia_pipes": geotermia_pipes,
            },
            "materials": materials,
            "thermal_data": thermal,
            "structural_data": structural,
            "sensor_data": sensor,
            "timestamp": record["timestamp"],
        }


if __name__ == "__main__":
    # Ejemplo standalone del scaffold.
    twin = DigitalTwin4DExtremadura()
    out = twin.update(
        {
            "temp_exterior": 38,
            "humidity": 30,
            "radiation": 800,
            "pv_power": 3000,
            "wind_speed": 5,
            "geo_active": True,
        }
    )
    print("Estado del gemelo:", out["status"])
    print("Alerts:", out["alerts"])
    print("Export 3D:", twin.export_to_3d().keys())

