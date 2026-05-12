"""Contratos Pydantic V2: cada valor con tolerance y confidence_score (ultra-precisión)."""
from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


def _clamp_confidence(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


class ValueWithPrecision(BaseModel):
    """Un valor numérico con rango de tolerancia y puntuación de confianza."""

    value: float
    tolerance_plus: float = Field(ge=0, default=0.0, description="Tolerancia por encima del valor nominal")
    tolerance_minus: float = Field(ge=0, default=0.0, description="Tolerancia por debajo del valor nominal")
    confidence_score: float = Field(
        ge=0,
        le=1,
        default=1.0,
        description="0=sin confianza, 1=totalmente fiable; acciones solo si > umbral",
    )

    model_config = ConfigDict(frozen=True)

    @property
    def band_low(self) -> float:
        return self.value - self.tolerance_minus

    @property
    def band_high(self) -> float:
        return self.value + self.tolerance_plus

    def is_within_band(self, other: float) -> bool:
        return self.band_low <= other <= self.band_high

    def is_actionable(self, min_confidence: float = 0.85) -> bool:
        return self.confidence_score >= min_confidence


UltraPrecisionFloat = Annotated[
    float,
    Field(description="Valor con banda de tolerancia implícita; ver UltraPrecisionSchema para detalle"),
]


class UltraPrecisionSchema(BaseModel):
    """Esquema maestro para telemetría de alta precisión: pH, temperatura, flujo, NPK.

    Cada magnitud incluye tolerance y confidence_score para no actuar sobre un solo dato errático.
    """

    model_config = ConfigDict(extra="allow")

    ph: ValueWithPrecision | None = Field(
        default=None,
        description="pH con banda y confianza; crítico para Ozono+Nitrato",
    )
    temperature_c: ValueWithPrecision | None = Field(default=None, description="Temperatura agua/suelo °C")
    flow_m3_h: ValueWithPrecision | None = Field(default=None, description="Flujo riego m³/h")
    conductivity_ms_cm: ValueWithPrecision | None = Field(
        default=None,
        description="CE; condiciona permeabilidad membranas RO",
    )
    nitrate_ppm: ValueWithPrecision | None = Field(default=None, description="N filtrado (Kalman/EWMA)")
    potassium_ppm: ValueWithPrecision | None = Field(default=None, description="K filtrado")
    ozone_ppm: ValueWithPrecision | None = Field(default=None, description="O3; fallo sensor → fail-safe NPK")
    ground_temp_10m_c: ValueWithPrecision | None = Field(default=None, description="T suelo 10 m geotermia")
    pressure_bar: ValueWithPrecision | None = Field(default=None, description="Presión riego/RO bar")
    irradiance_wm2: ValueWithPrecision | None = Field(default=None, description="Radiación UNE 216701")

    def get_ph_actionable(self, min_confidence: float = 0.85) -> bool:
        return self.ph is not None and self.ph.is_actionable(min_confidence)

    def get_npk_actionable(self, min_confidence: float = 0.85) -> bool:
        n = self.nitrate_ppm is not None and self.nitrate_ppm.is_actionable(min_confidence)
        k = self.potassium_ppm is not None and self.potassium_ppm.is_actionable(min_confidence)
        return n and k

    def ozone_sensor_ok(self, min_confidence: float = 0.7) -> bool:
        """Si False, activar fail-safe: cerrar válvula NPK."""
        return self.ozone_ppm is not None and self.ozone_ppm.confidence_score >= min_confidence
