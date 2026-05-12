"""Filtro EWMA para N/K: no actuar con un solo dato errático (ruido de voltaje/interferencias)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .constants import MIN_SAMPLES_BEFORE_ACTUATION_NPK


@dataclass
class SensorFilterState:
    """Estado interno del filtro para un canal (N o K)."""

    value: float = 0.0
    variance_estimate: float = 0.0
    sample_count: int = 0
    alpha: float = 0.25


class NPKFilter:
    """Media móvil ponderada (EWMA) para Nitrato y Potasio; requiere N muestras antes de actuación."""

    def __init__(
        self,
        alpha: float = 0.25,
        min_samples: int = MIN_SAMPLES_BEFORE_ACTUATION_NPK,
    ) -> None:
        self.alpha = max(0.05, min(0.8, alpha))
        self.min_samples = max(1, min_samples)
        self._nitrate = SensorFilterState(alpha=self.alpha)
        self._potassium = SensorFilterState(alpha=self.alpha)

    def update_nitrate(self, raw_ppm: float) -> float:
        """Devuelve valor filtrado; no usar para actuación hasta sample_count >= min_samples."""
        s = self._nitrate
        if s.sample_count == 0:
            s.value = float(raw_ppm)
            s.variance_estimate = 0.0
        else:
            s.value = self.alpha * float(raw_ppm) + (1.0 - self.alpha) * s.value
            delta = raw_ppm - s.value
            s.variance_estimate = (1.0 - self.alpha) * s.variance_estimate + self.alpha * (delta * delta)
        s.sample_count += 1
        return round(s.value, 2)

    def update_potassium(self, raw_ppm: float) -> float:
        s = self._potassium
        if s.sample_count == 0:
            s.value = float(raw_ppm)
            s.variance_estimate = 0.0
        else:
            s.value = self.alpha * float(raw_ppm) + (1.0 - self.alpha) * s.value
            delta = raw_ppm - s.value
            s.variance_estimate = (1.0 - self.alpha) * s.variance_estimate + self.alpha * (delta * delta)
        s.sample_count += 1
        return round(s.value, 2)

    def nitrate_filtered(self) -> float:
        return self._nitrate.value

    def potassium_filtered(self) -> float:
        return self._potassium.value

    def is_ready_for_actuation(self) -> bool:
        """True solo cuando hay suficientes muestras para no depender de un solo dato."""
        return (
            self._nitrate.sample_count >= self.min_samples
            and self._potassium.sample_count >= self.min_samples
        )

    def nitrate_confidence(self) -> float:
        """Confianza aproximada: baja si varianza alta respecto al valor."""
        s = self._nitrate
        if s.sample_count < 2 or s.value == 0:
            return 0.5
        cv = (s.variance_estimate ** 0.5) / abs(s.value)
        return round(max(0.0, min(1.0, 1.0 - min(1.0, cv * 2))), 2)

    def potassium_confidence(self) -> float:
        s = self._potassium
        if s.sample_count < 2 or s.value == 0:
            return 0.5
        cv = (s.variance_estimate ** 0.5) / abs(s.value)
        return round(max(0.0, min(1.0, 1.0 - min(1.0, cv * 2))), 2)
