# -*- coding: utf-8 -*-
"""Agente especializado en agritech (microgreens, trazabilidad, IoT)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from backend.models.agent import AgentEthics, CustomAgent
from pydantic import Field


class AgritechAgent(CustomAgent):
    """Agente especializado en agritech (microgreens, trazabilidad, IoT)."""

    knowledge_areas: List[str] = Field(
        default_factory=lambda: [
            "hydroponics",
            "microgreens",
            "blockchain_traceability",
            "iot_sensors",
            "sustainable_agriculture",
        ]
    )
    ethics: AgentEthics = Field(
        default_factory=lambda: AgentEthics(sustainability=1.0, transparency=1.0)
    )

    def analyze_environment(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza datos ambientales y sugiere acciones."""
        temp = sensor_data.get("temperature", 0)
        humidity = sensor_data.get("humidity", 0)
        co2 = sensor_data.get("co2", 0)
        ph = sensor_data.get("ph", 0)
        ec = sensor_data.get("ec", 0)

        suggestions: List[str] = []
        if humidity > 0 and humidity < 60:
            suggestions.append("Aumentar humedad hacia 70%")
        elif humidity > 85:
            suggestions.append("Reducir humedad para evitar hongos")
        if co2 > 0 and co2 > 1000:
            suggestions.append("Reducir CO2 a ~800 ppm")
        if ph > 0 and (ph < 5.5 or ph > 6.5):
            suggestions.append("Ajustar pH a rango 5.8–6.2 para microgreens")
        if ec > 0 and ec < 1.0:
            suggestions.append("Verificar nivel de nutrientes (EC bajo)")

        return {
            "status": "optimal" if len(suggestions) == 0 else "adjust",
            "suggestions": suggestions or [
                "Condiciones dentro de rango; mantener monitoreo.",
            ],
            "sensor_summary": {
                "temperature": temp,
                "humidity": humidity,
                "co2": co2,
                "ph": ph,
                "ec": ec,
            },
        }

    def generate_certificate(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un certificado de trazabilidad para un lote."""
        batch_id = batch_data.get("id", batch_data.get("batch_id", "unknown"))
        return {
            "batch_id": batch_id,
            "certificate": {
                "standards": ["ISO_22000", "GlobalGAP", "CTAEX_TRL7"],
                "blockchain_tx": f"tx_{batch_id}_{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                "sustainability_score": 0.95,
            },
        }
