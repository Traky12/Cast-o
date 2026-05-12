#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CASTÚO-SYSTEM™ — Entrenamiento del modelo de detección de anomalías (anti-hacking v1.0).
Isolation Forest sobre métricas: cpu_usage, memory_usage, network_traffic, login_attempts.
Salida: models/anomaly_detection.pkl + models/anomaly_metrics.json
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def train_model(
    contamination: float = 0.01,
    n_estimators: int = 100,
    csv_path: str | None = None,
) -> None:
    if HAS_PANDAS and csv_path and os.path.isfile(csv_path):
        data = pd.read_csv(csv_path)
        X = data[["cpu_usage", "memory_usage", "network_traffic", "login_attempts"]].values
    else:
        # Datos de ejemplo para arranque sin CSV
        np.random.seed(42)
        X = np.random.rand(200, 4) * 0.8 + 0.1  # valores típicos 0.1–0.9

    clf = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
    )
    clf.fit(X)

    model_path = MODEL_DIR / "anomaly_detection.pkl"
    import joblib
    joblib.dump(clf, model_path)

    metrics = {
        "training_date": datetime.utcnow().isoformat(),
        "contamination": contamination,
        "features": ["cpu_usage", "memory_usage", "network_traffic", "login_attempts"],
        "sample_size": len(X),
    }
    with open(MODEL_DIR / "anomaly_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"Modelo guardado en {model_path}; métricas en {MODEL_DIR / 'anomaly_metrics.json'}")


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    train_model(csv_path=csv_path)
