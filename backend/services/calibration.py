# -*- coding: utf-8 -*-
"""Calibración de sensores IoT (Libelium) según estándares agrarios UE."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SensorCalibration(BaseModel):
    """Ajuste de rangos para cumplimiento con normativas agrarias UE."""

    sensor_id: str
    parameter: str  # "temperature", "humidity", "ph", "ec", "light"
    raw_value: float
    calibrated_value: Optional[float] = None
    tolerance: float = 0.05  # 5% tolerancia según ISO 17025

    def calibrate(self) -> "SensorCalibration":
        """Ajusta el valor del sensor según estándares UE."""
        if self.parameter == "temperature":
            # Rango UE para cultivos: 18°C–28°C (Reglamento (UE) 2018/848)
            if not (18 <= self.raw_value <= 28):
                raise ValueError(
                    f"Temperatura fuera de rango UE: {self.raw_value}°C (rango 18–28°C)"
                )
            self.calibrated_value = self.raw_value * 0.995  # Ajuste por derivas térmicas

        elif self.parameter == "ph":
            # Rango óptimo para cannabis: 5.8–6.5 (Norma UNE-EN 13655)
            if not (5.8 <= self.raw_value <= 6.5):
                raise ValueError(
                    f"pH fuera de rango: {self.raw_value} (rango 5.8–6.5)"
                )
            self.calibrated_value = self.raw_value + 0.02  # Compensación por electrodo

        elif self.parameter == "ec":
            # Conductividad eléctrica (mS/cm) para microgreens: 1.2–2.5
            if not (1.2 <= self.raw_value <= 2.5):
                raise ValueError(
                    f"EC fuera de rango: {self.raw_value} mS/cm (rango 1.2–2.5)"
                )
            self.calibrated_value = self.raw_value * 1.01  # Compensación por temperatura

        elif self.parameter == "humidity":
            # Humedad 40%–70% (Norma UNE 100021); sin ajuste (sensores precalibrados)
            if not (40 <= self.raw_value <= 70):
                raise ValueError(
                    f"Humedad fuera de rango UE: {self.raw_value}% (rango 40–70%)"
                )
            self.calibrated_value = self.raw_value

        elif self.parameter == "light":
            # Lux o µmol/m²/s; sin corrección específica UE
            self.calibrated_value = self.raw_value

        else:
            self.calibrated_value = self.raw_value
        return self
