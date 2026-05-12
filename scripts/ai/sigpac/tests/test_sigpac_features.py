from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "sigpac"))
import sigpac_features  # noqa: E402


def test_summary_to_feature_vector() -> None:
    summary = {
        "mean": 1.0,
        "std": 0.1,
        "min": 0.5,
        "max": 1.5,
        "shape": [10, 20],
        "area_m2_approx": 100.0,
    }
    v = sigpac_features.summary_to_feature_vector(summary)
    assert v.shape == (8,)
    assert v[0] == pytest.approx(1.0)


def test_summary_error_raises() -> None:
    with pytest.raises(ValueError):
        sigpac_features.summary_to_feature_vector({"error": "x"})


def test_federated_bundle_nulls() -> None:
    summary = {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "shape": [1, 1],
        "area_m2_approx": 0.0,
    }
    b = sigpac_features.federated_feature_bundle(summary)
    assert b["ndvi"] is None
    assert b["soil_moisture"] is None
    assert b["vector_dim"] == 8
