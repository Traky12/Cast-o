# -*- coding: utf-8 -*-
"""
Integración CASTUA con CASTUO Cloud 5.0.
Sincronización sensores, Sentinel (anomalías), energía, GaiaChain.
Todo en sistemas españoles/UE.
"""
from datetime import datetime
from typing import Any, Dict

import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from castuo.cloud import EdgeNode, SentinelSecurity, EnergyManager
except ImportError:
    EdgeNode = None  # type: ignore
    SentinelSecurity = None  # type: ignore
    EnergyManager = None  # type: ignore

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


class CastuaCloudIntegration:
    """
    Integración invernadero CASTUA con CASTUO Cloud 5.0.
    Edge, Sentinel (seguridad post-cuántica), energía, trazabilidad GaiaChain.
    """

    def __init__(self, greenhouse_id: str):
        self.greenhouse_id = greenhouse_id
        self.edge_node = EdgeNode(greenhouse_id) if EdgeNode else None
        self.security = SentinelSecurity(greenhouse_id) if SentinelSecurity else None
        self.energy = EnergyManager(greenhouse_id) if EnergyManager else None
        self.blockchain = GaiaChainClient() if GaiaChainClient else None

    def sync_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza datos de sensores con Cloud: edge, Sentinel, GaiaChain."""
        processed_data = self.edge_node.process_data(sensor_data) if self.edge_node else {"sensors": sensor_data, "timestamp": datetime.now().isoformat()}

        anomalies = []
        if self.security:
            anomalies = self.security.detect_anomalies(processed_data)
        if anomalies:
            self._handle_anomalies(anomalies)

        if self.blockchain:
            data_for_blockchain = {
                "greenhouse_id": self.greenhouse_id,
                "timestamp": processed_data.get("timestamp"),
                "sensors": processed_data.get("sensors", {}),
                "energy": self.energy.get_status() if self.energy else {},
                "security_status": "clean" if not anomalies else "anomaly_detected",
            }
            self.blockchain.log_sensor_data(data_for_blockchain)

        return processed_data

    def _handle_anomalies(self, anomalies: list) -> None:
        """Gestiona anomalías: acciones edge y registro en GaiaChain."""
        for anomaly in anomalies:
            if self.edge_node:
                if anomaly.get("type") == "temperature":
                    self.edge_node.trigger_action("cooling")
                elif anomaly.get("type") == "humidity":
                    self.edge_node.trigger_action("humidifier")
            if self.security and anomaly.get("type") == "security":
                self.security.isolate_system()
            if self.blockchain:
                self.blockchain.log_anomaly({
                    "greenhouse_id": self.greenhouse_id,
                    "anomaly": anomaly,
                    "action_taken": f"Triggered {anomaly.get('type', '')} response",
                    "timestamp": datetime.now().isoformat(),
                })

    def get_energy_status(self) -> Dict[str, Any]:
        """Estado energético (agrovoltaica, batería, consumo)."""
        return self.energy.get_status() if self.energy else {}

    def optimize_energy_use(self) -> None:
        """Optimiza uso: red si batería baja, venta de excedentes."""
        if not self.energy:
            return
        current = self.energy.get_status()
        if current.get("battery_level", 100) < 20:
            self.energy.switch_to_grid()
        elif current.get("solar_generation", 0) > current.get("consumption", 0) * 1.2:
            excess = current["solar_generation"] - current["consumption"]
            self.energy.sell_excess(excess)
        if self.blockchain:
            self.blockchain.log_energy_optimization({
                "greenhouse_id": self.greenhouse_id,
                "action": "energy_optimization",
                "status": current,
                "timestamp": datetime.now().isoformat(),
            })

    def get_security_status(self) -> Dict[str, Any]:
        """Estado de seguridad Sentinel."""
        return self.security.get_status() if self.security else {}
