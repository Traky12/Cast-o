from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

THC_ROUTER_PATH = ROOT / "backend" / "routers" / "thc.py"
spec = importlib.util.spec_from_file_location("backend.routers.thc_integration", THC_ROUTER_PATH)
assert spec and spec.loader
thc_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = thc_module
spec.loader.exec_module(thc_module)


def _build_trained_estimator():
    est = thc_module.THCEstimator()
    X = np.random.RandomState(123).rand(32, 157).astype(np.float32)
    y = (np.random.RandomState(321).rand(32).astype(np.float32) * 20.0) + 1.0
    est.train_pls_1c(X, y)
    return est


def test_thc_estimate_flow():
    app = FastAPI()
    app.include_router(thc_module.router, prefix="/thc")
    thc_module._EST = _build_trained_estimator()
    client = TestClient(app)

    response = client.post(
        "/thc/estimate",
        json={
            "batch_id": "test-batch-001",
            "plant_id": "test_plant_001",
            "spectrum": [0.1] * 157,
            "zone_id": "test_zone",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "PENDING_VALIDATION"
    assert data["batch_id"] == "test-batch-001"
    assert "gaiachain_tx" in data
