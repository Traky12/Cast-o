"""AGRI-SENSE-CORE: contratos de ultra-precisión, filtrado de sensores y constantes fail-safe."""
from __future__ import annotations

from .constants import (
    FAIL_SAFE_NPK_VALVE_CLOSED_ON_OZONE_FAULT,
    GEOTHERMAL_SETPOINT_DEVIATION_C,
    MIN_SAMPLES_BEFORE_ACTUATION_NPK,
)
from .schemas import (
    UltraPrecisionFloat,
    UltraPrecisionSchema,
    ValueWithPrecision,
)
from .quantum_optimizer import CastuoQuantumOptimizer, QuantumOptimizationResult, optimize_bionergy_allocation
from .sensor_filters import NPKFilter, SensorFilterState

__all__ = [
    "FAIL_SAFE_NPK_VALVE_CLOSED_ON_OZONE_FAULT",
    "GEOTHERMAL_SETPOINT_DEVIATION_C",
    "MIN_SAMPLES_BEFORE_ACTUATION_NPK",
    "NPKFilter",
    "SensorFilterState",
    "UltraPrecisionFloat",
    "UltraPrecisionSchema",
    "ValueWithPrecision",
    "CastuoQuantumOptimizer",
    "QuantumOptimizationResult",
    "optimize_bionergy_allocation",
]
