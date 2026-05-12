#!/usr/bin/env python3
"""
Vector de baja dimensión a partir del resumen raster (banda 1). Slotes reservados para NDVI / humedad
cuando exista fuente multispectral o sensores; no rellenar con valores sintéticos en producción.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

Json = Dict[str, Any]


def summary_to_feature_vector(summary: Json) -> np.ndarray:
    if "error" in summary:
        raise ValueError(str(summary["error"]))
    h, w = summary["shape"]
    area = float(summary.get("area_m2_approx") or 0.0)
    return np.array(
        [
            float(summary["mean"]),
            float(summary["std"]),
            float(summary["min"]),
            float(summary["max"]),
            float(np.log1p(max(area, 0.0))),
            float(h) / 1000.0,
            float(w) / 1000.0,
            0.0,
        ],
        dtype=np.float32,
    )


def federated_feature_bundle(summary: Json) -> Json:
    """Metadatos para alertas y pipelines; campos ausentes explícitos hasta integrar capas extra."""
    vec = summary_to_feature_vector(summary)
    return {
        "vector_dim": int(vec.shape[0]),
        "raster_band1": {
            "mean": summary.get("mean"),
            "std": summary.get("std"),
            "min": summary.get("min"),
            "max": summary.get("max"),
        },
        "ndvi": None,
        "soil_moisture": None,
    }
