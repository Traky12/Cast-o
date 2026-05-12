# backend/ai/model_quality.py — Métricas de calidad para agregación ponderada (EU AI Act)

from __future__ import annotations

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False


class ModelQualityMetrics:
    """Score de calidad (0–1) para ponderar modelos en agregación."""

    @staticmethod
    def calculate_quality_score(model: Dict) -> float:
        """
        Combina confianza reportada y baja varianza de pesos.
        Peso: 60% confianza, 40% (1 - min(varianza, 1)).
        """
        confidence = float(model.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
        if not _NUMPY or np is None:
            return confidence
        try:
            var_sum = 0.0
            total = 0
            for w in (model.get("weights") or {}).values():
                arr = np.array(w, dtype=float)
                var_sum += float(np.var(arr))
                total += arr.size
            weight_var = var_sum / total if total > 0 else 0.0
            var_score = 1.0 - min(weight_var, 1.0)
            return 0.6 * confidence + 0.4 * max(0.0, var_score)
        except Exception:
            return confidence

    @staticmethod
    def quality_weights(models: List[Dict]) -> List[float]:
        """Devuelve pesos normalizados por calidad para usar en promedio ponderado."""
        if not models:
            return []
        scores = [ModelQualityMetrics.calculate_quality_score(m) for m in models]
        total = sum(scores)
        if total <= 0:
            return [1.0 / len(models)] * len(models)
        return [s / total for s in scores]
