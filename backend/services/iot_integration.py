# -*- coding: utf-8 -*-
"""Integración IoT para microgreens (sensores, análisis ambiental)."""
from __future__ import annotations

import random
from datetime import datetime
from typing import Any, Dict, List

from backend.models.microgreens_specific import MicrogreenBatch, MicrogreenVariety


class MicrogreenIoTService:
    """Servicio para integrar datos de IoT en lotes de microgreens."""

    def get_environmental_data(self, batch_id: str) -> Dict[str, Any]:
        """Simula datos de sensores IoT para un lote de microgreens."""
        return {
            "temperature": round(random.uniform(18, 24), 1),
            "humidity": round(random.uniform(60, 75), 1),
            "ph": round(random.uniform(5.5, 6.5), 1),
            "ec": round(random.uniform(1.0, 1.5), 2),
            "light_intensity": round(random.uniform(10000, 20000), 0),
            "co2": round(random.uniform(400, 800), 0),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def analyze_environment(
        self,
        batch: MicrogreenBatch,
        variety: MicrogreenVariety | Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analiza los datos ambientales y sugiere ajustes."""
        if not batch.environmental_data:
            return {"status": "no_data", "suggestions": []}

        suggestions: List[str] = []
        env = batch.environmental_data

        if isinstance(variety, MicrogreenVariety):
            ideal_ph = variety.ideal_ph
            ideal_temp = variety.ideal_temperature
            ideal_hum = variety.ideal_humidity
            ideal_ec = variety.ideal_ec
        else:
            ideal_ph = variety.get("ideal_ph", 6.0)
            ideal_temp = tuple(variety.get("ideal_temperature", (18, 22)))
            ideal_hum = tuple(variety.get("ideal_humidity", (60, 70)))
            ideal_ec = variety.get("ideal_ec", 1.2)

        ph = env.get("ph")
        if ph is not None and ph < ideal_ph - 0.3:
            suggestions.append(
                f"Aumentar pH a {ideal_ph} (actual: {ph}). Usar solución alcalina."
            )
        elif ph is not None and ph > ideal_ph + 0.3:
            suggestions.append(
                f"Reducir pH a {ideal_ph} (actual: {ph}). Usar solución ácida."
            )

        temp = env.get("temperature")
        if temp is not None and temp < ideal_temp[0]:
            suggestions.append(
                f"Aumentar temperatura a {ideal_temp}°C (actual: {temp}°C)."
            )
        elif temp is not None and temp > ideal_temp[1]:
            suggestions.append(
                f"Reducir temperatura a {ideal_temp}°C (actual: {temp}°C)."
            )

        hum = env.get("humidity")
        if hum is not None and hum < ideal_hum[0]:
            suggestions.append(
                f"Aumentar humedad a {ideal_hum}% (actual: {hum}%)."
            )
        elif hum is not None and hum > ideal_hum[1]:
            suggestions.append(f"Reducir humedad a {ideal_hum}% (actual: {hum}%).")

        ec = env.get("ec")
        if ec is not None and ec < ideal_ec - 0.2:
            suggestions.append(
                f"Aumentar EC a {ideal_ec} (actual: {ec}). Añadir nutrientes."
            )
        elif ec is not None and ec > ideal_ec + 0.2:
            suggestions.append(
                f"Reducir EC a {ideal_ec} (actual: {ec}). Diluir solución nutritiva."
            )

        co2 = env.get("co2")
        if co2 is not None and co2 < 600:
            suggestions.append(f"Aumentar CO2 a 600-800 ppm (actual: {co2} ppm).")
        elif co2 is not None and co2 > 1000:
            suggestions.append(
                f"Reducir CO2 a 600-800 ppm (actual: {co2} ppm). Ventilar."
            )

        status = "optimal" if not suggestions else "needs_adjustment"
        return {"status": status, "suggestions": suggestions}
