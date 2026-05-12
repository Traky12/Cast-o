from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.thc_estimator import THCEstimator


def _train_estimator() -> THCEstimator:
    est = THCEstimator()
    X = np.random.RandomState(42).rand(64, 157).astype(np.float32)
    y = (np.random.RandomState(7).rand(64).astype(np.float32) * 20.0) + 1.0
    est.train_pls_1c(X, y)
    return est


def test_estimator_initialization():
    est = THCEstimator()
    assert est.weights is None
    assert est.mean_x is None
    assert est.mean_y is None


def test_train_and_predict_shapes():
    est = _train_estimator()
    sample = np.random.RandomState(1).rand(1, 157).astype(np.float32)
    pred = est.predict(sample)
    assert pred.shape == (1,)


def test_estimate_and_register_works_with_stub_chain():
    est = _train_estimator()
    spectrum = [0.1] * 157
    result = asyncio.run(
        est.estimate_and_register(
            plant_id="PLANT-001",
            zone_id="ZONE-A",
            spectrum=spectrum,
            batch_id="BATCH-001",
        )
    )
    assert result["status"] == "PENDING_VALIDATION"
    assert result["batch_id"] == "BATCH-001"
    assert len(result["spectrum_hash"]) == 64
