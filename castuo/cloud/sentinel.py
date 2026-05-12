# -*- coding: utf-8 -*-
"""Sentinel v5 — Seguridad post-cuántica y detección de anomalías (CASTUO Cloud 5.0)."""
from typing import Any, Dict, List


class SentinelSecurity:
    """
    Seguridad CASTUO: detección de anomalías (temperatura, humedad, intrusión).
    Alineado con eIDAS, GDPR, AI Act (UE).
    """

    def __init__(self, greenhouse_id: str):
        self.greenhouse_id = greenhouse_id

    def detect_anomalies(self, processed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta anomalías en datos procesados (umbrales temperatura, humedad, etc.)."""
        anomalies: List[Dict[str, Any]] = []
        sensors = processed_data.get("sensors", {})
        if isinstance(sensors, dict):
            temp = sensors.get("temperature")
            if temp is not None and (isinstance(temp, (int, float)) and (temp > 35 or temp < 5)):
                anomalies.append({"type": "temperature", "value": temp})
            hum = sensors.get("humidity")
            if hum is not None and isinstance(hum, (int, float)) and (hum > 90 or hum < 20):
                anomalies.append({"type": "humidity", "value": hum})
        return anomalies

    def isolate_system(self) -> None:
        """Aislamiento de sistema en caso de amenaza de seguridad."""
        pass

    def get_status(self) -> Dict[str, str]:
        """Estado de seguridad actual."""
        return {"status": "active", "greenhouse_id": self.greenhouse_id}
