# -*- coding: utf-8 -*-
"""
Gestión hidropónica de cáñamo industrial en invernaderos agrovoltaicos.
Sistemas españoles/UE: sensores, riego, optimización luz, trazabilidad GaiaChain.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class AgrovoltaicSystem:
    """Sistema agrovoltaico (paneles semitransparentes, balance luz/energía)."""

    def __init__(self, greenhouse_id: str):
        self.greenhouse_id = greenhouse_id
        self.panel_angle = 30  # grados
        self.energy_generated = 0.0  # kWh
        self.energy_consumed = 0.0  # kWh

    def adjust_panels(self, adjustment: float) -> None:
        """Ajusta ángulo de paneles para equilibrio luz/energía (óptimo para cáñamo)."""
        self.panel_angle = max(10.0, min(60.0, self.panel_angle + adjustment))

    def get_consumption(self, tower_id: str) -> float:
        """Estimación consumo energético por torre (kWh)."""
        return 0.1 * 150  # 0.1 kWh por planta, 150 plantas por torre

    def update_energy(self, generated: float, consumed: float) -> float:
        """Actualiza métricas de energía. Retorna balance neto (kWh)."""
        self.energy_generated += generated
        self.energy_consumed += consumed
        return self.energy_generated - self.energy_consumed


class CannabisHydroponicSystem:
    """
    Sistema hidropónico de cáñamo industrial en invernadero agrovoltaico.
    Integración: sensores, torres, energía, blockchain GaiaChain (trazabilidad UE/España).
    """

    def __init__(self, greenhouse_id: str):
        self.greenhouse_id = greenhouse_id
        self.towers: List[Dict[str, Any]] = []
        self.sensors: Dict[str, List[Dict[str, Any]]] = {
            "temperature": [],
            "humidity": [],
            "ph": [],
            "ec": [],
            "light": [],
        }
        self.energy_system = AgrovoltaicSystem(greenhouse_id)
        self.blockchain = GaiaChainClient() if GaiaChainClient else None

    def add_tower(self, tower_id: str, plants: int = 150) -> None:
        """Añade torre hidropónica (plantas por torre)."""
        self.towers.append({
            "id": tower_id,
            "plants": plants,
            "stage": "vegetative",  # vegetative, flowering, harvest
            "nutrients": {"N": 0, "P": 0, "K": 0},
            "last_watering": datetime.now(),
            "yield_estimate": 0.0,  # kg biomasa
        })

    def update_sensor_data(self, sensor_type: str, value: float) -> None:
        """Actualiza dato de sensor y dispara acciones si supera umbrales."""
        self.sensors.setdefault(sensor_type, []).append({"timestamp": datetime.now(), "value": value})

        if sensor_type == "temperature" and value > 30:
            self._activate_cooling()
        elif sensor_type == "humidity" and value < 40:
            self._activate_humidifier()
        elif sensor_type == "ph" and (value < 5.5 or value > 6.5):
            self._adjust_ph()

    def _activate_cooling(self) -> None:
        """Activa refrigeración y registra en GaiaChain."""
        action = {
            "greenhouse_id": self.greenhouse_id,
            "action": "cooling_activated",
            "timestamp": datetime.now().isoformat(),
            "temperature": self.sensors["temperature"][-1]["value"] if self.sensors["temperature"] else 0,
        }
        if self.blockchain:
            self.blockchain.log_action(action)

    def _activate_humidifier(self) -> None:
        """Activa humidificador."""
        if self.blockchain:
            self.blockchain.log_action({
                "greenhouse_id": self.greenhouse_id,
                "action": "humidifier_activated",
                "timestamp": datetime.now().isoformat(),
            })

    def _adjust_ph(self) -> None:
        """Ajuste de pH (registro en blockchain)."""
        if self.blockchain:
            self.blockchain.log_action({
                "greenhouse_id": self.greenhouse_id,
                "action": "ph_adjustment",
                "timestamp": datetime.now().isoformat(),
            })

    def optimize_light(self) -> None:
        """Ajusta paneles agrovoltaicos para distribución óptima de luz (cáñamo ~15.000 lux)."""
        current_light = self.sensors["light"][-1]["value"] if self.sensors.get("light") else 0
        optimal_light = 15000  # lux para cannabis
        adjustment = (optimal_light - current_light) / 1000.0
        self.energy_system.adjust_panels(adjustment)
        if self.blockchain:
            self.blockchain.log_action({
                "greenhouse_id": self.greenhouse_id,
                "action": "light_optimization",
                "adjustment": adjustment,
                "timestamp": datetime.now().isoformat(),
            })

    def calculate_yield(self) -> float:
        """Estima producción (kg biomasa) según estado y condiciones."""
        total_yield = 0.0
        for tower in self.towers:
            base_yield = 0.5  # kg por planta
            if tower["stage"] == "flowering":
                base_yield = 0.7
            elif tower["stage"] == "harvest":
                base_yield = 0.9

            temp_factor = 1.0
            if self.sensors.get("temperature"):
                temp = self.sensors["temperature"][-1]["value"]
                temp_factor = max(0.5, min(1.2, 1.0 + (28 - temp) * 0.02))  # Óptimo 28 °C

            tower["yield_estimate"] = base_yield * tower["plants"] * temp_factor
            total_yield += tower["yield_estimate"]
        return total_yield

    def harvest(self, tower_id: str) -> Dict[str, Any]:
        """Cosecha una torre y registra en GaiaChain (trazabilidad RD 903/2025)."""
        tower = next((t for t in self.towers if t["id"] == tower_id), None)
        if not tower:
            raise ValueError(f"Torre {tower_id} no encontrada")
        yield_data = {
            "greenhouse_id": self.greenhouse_id,
            "tower_id": tower_id,
            "plants": tower["plants"],
            "yield_kg": tower["yield_estimate"],
            "stage": tower["stage"],
            "timestamp": datetime.now().isoformat(),
            "energy_used_kwh": self.energy_system.get_consumption(tower_id),
            "co2_saved_kg": tower["yield_estimate"] * 1.85,  # kg CO₂ evitados por kg biomasa
        }
        if self.blockchain:
            self.blockchain.register_harvest(yield_data)
        tower["stage"] = "vegetative"
        tower["yield_estimate"] = 0.0
        return yield_data
