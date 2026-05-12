# -*- coding: utf-8 -*-
"""Modelos Pydantic para producción: control ambiental, microgreens, tratamiento de agua."""
from .environment_control import (
    OzoneSensorData,
    ReverseOsmosisData,
    UVLightData,
    NutrientSolutionData,
    EnvironmentalControlData,
)
from .microgreens import MicrogreenVariety, MicrogreenBatch
from .water_treatment import WaterQualityData, ROSystemData, WaterTreatmentLog

__all__ = [
    "OzoneSensorData",
    "ReverseOsmosisData",
    "UVLightData",
    "NutrientSolutionData",
    "EnvironmentalControlData",
    "MicrogreenVariety",
    "MicrogreenBatch",
    "WaterQualityData",
    "ROSystemData",
    "WaterTreatmentLog",
]
