# backend/ai/outlier_detection.py — Detección de outliers con DBSCAN (FL seguro)

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

_SKLEARN = False
try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    _SKLEARN = True
except ImportError:
    DBSCAN = None
    StandardScaler = None


class AdvancedOutlierDetector:
    """
    Detecta outliers en pesos de modelos con DBSCAN.
    Si sklearn no está disponible, fallback a Z-score con NumPy.
    """

    def __init__(self, eps: float = 0.5, min_samples: int = 2, zscore_threshold: float = 3.0) -> None:
        self.eps = eps
        self.min_samples = min_samples
        self.zscore_threshold = zscore_threshold
        self.scaler = StandardScaler() if _SKLEARN and StandardScaler else None
        self.logger = logging.getLogger(__name__)

    def detect_outliers(self, models: List[Dict]) -> List[bool]:
        """
        Devuelve lista de booleanos: True = outlier.
        Por modelo se considera outlier si alguna de sus contribuciones es outlier.
        """
        if not models or not _NUMPY or np is None:
            return [False] * len(models)
        # Aplanar pesos por modelo: una fila por modelo
        rows = []
        for m in models:
            vec = []
            for layer_weights in (m.get("weights") or {}).values():
                if isinstance(layer_weights, (list, tuple)):
                    vec.extend(layer_weights)
                else:
                    vec.extend(list(layer_weights))
            rows.append(vec)
        if not rows:
            return [False] * len(models)
        X = np.array(rows, dtype=float)
        n_models = X.shape[0]
        if n_models < 2:
            return [False] * n_models
        outlier_flags = [False] * n_models
        if _SKLEARN and DBSCAN is not None and self.scaler is not None:
            try:
                X_scaled = self.scaler.fit_transform(X)
                clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(X_scaled)
                for i, label in enumerate(clustering.labels_):
                    if label == -1:
                        outlier_flags[i] = True
            except Exception as e:
                self.logger.debug("DBSCAN fallido, usando Z-score: %s", e)
                outlier_flags = self._zscore_outliers(X)
        else:
            outlier_flags = self._zscore_outliers(X)
        return outlier_flags

    def _zscore_outliers(self, X: "np.ndarray") -> List[bool]:
        """Marca como outlier las filas con algún valor con Z-score > threshold."""
        mean = np.mean(X, axis=0)
        std = np.std(X, axis=0)
        std[std == 0] = 1
        z = np.abs((X - mean) / std)
        max_z_per_row = np.max(z, axis=1)
        return [float(m) > self.zscore_threshold for m in max_z_per_row]

    def filter_valid_models(self, models: List[Dict]) -> List[Dict]:
        """Devuelve solo modelos que no son outliers."""
        flags = self.detect_outliers(models)
        return [m for m, out in zip(models, flags) if not out]
