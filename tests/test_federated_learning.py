# tests/test_federated_learning.py
import pytest
from unittest.mock import MagicMock


def test_validate_model_integrity():
    from backend.ai.federated_learning import FederatedLearningCoordinator
    import hashlib
    import json

    coord = FederatedLearningCoordinator()
    data = {"weights": {"layer1": [0.1, 0.2]}, "confidence": 0.9}
    data_for_hash = {k: v for k, v in data.items()}
    h = hashlib.sha3_512(json.dumps(data_for_hash, sort_keys=True).encode()).hexdigest()
    if hasattr(hashlib, "blake3"):
        h = hashlib.blake3(json.dumps(data_for_hash, sort_keys=True).encode()).hexdigest()
    data["hash"] = h
    assert coord._validate_model_integrity(data) is True
    data["hash"] = "wrong"
    assert coord._validate_model_integrity(data) is False


def test_aggregate_models_valid():
    from backend.ai.federated_learning import FederatedLearningCoordinator
    import hashlib
    import json

    coord = FederatedLearningCoordinator()
    def add_hash(m):
        d = {k: v for k, v in m.items() if k != "hash"}
        m["hash"] = hashlib.sha3_512(json.dumps(d, sort_keys=True).encode()).hexdigest()
        if hasattr(hashlib, "blake3"):
            m["hash"] = hashlib.blake3(json.dumps(d, sort_keys=True).encode()).hexdigest()
        return m
    m1 = add_hash({"weights": {"layer1": [0.1, 0.2]}, "confidence": 0.9})
    m2 = add_hash({"weights": {"layer1": [0.11, 0.21]}, "confidence": 0.85})
    result = coord._aggregate_models([{"model1": m1}, {"model1": m2}])
    assert result is not None
    assert "model1" in result
    assert "aggregation_metadata" in result["model1"]
    assert "hash" in result["model1"]


def test_weighted_average():
    from backend.ai.federated_learning import FederatedLearningCoordinator

    coord = FederatedLearningCoordinator()
    models = [
        {"weights": {"layer1": [0.1, 0.2]}, "confidence": 0.9},
        {"weights": {"layer1": [0.15, 0.25]}, "confidence": 0.8},
    ]
    agg = coord._weighted_average_models(models)
    assert "weights" in agg
    assert 0.1 <= agg["weights"]["layer1"][0] <= 0.15
    assert 0.2 <= agg["weights"]["layer1"][1] <= 0.25
    assert "hash" in agg
    assert "aggregation_metadata" in agg


def _add_hash(m):
    import hashlib
    import json
    d = {k: v for k, v in m.items() if k != "hash"}
    h = hashlib.sha3_512(json.dumps(d, sort_keys=True).encode()).hexdigest()
    if hasattr(hashlib, "blake3"):
        h = hashlib.blake3(json.dumps(d, sort_keys=True).encode()).hexdigest()
    m["hash"] = h
    return m


def test_outlier_detection_high_zscore():
    """Modelo con outlier (Z-score > 3) debe rechazar agregación."""
    from backend.ai.federated_learning import FederatedLearningCoordinator

    coord = FederatedLearningCoordinator()
    normals = [_add_hash({"weights": {"layer1": [0.1 + i * 0.01, 0.2 + i * 0.01]}}) for i in range(10)]
    m_outlier = _add_hash({"weights": {"layer1": [1000.0, 2000.0]}})
    all_models = [{"model1": m} for m in normals] + [{"model1": m_outlier}]
    result = coord._aggregate_models(all_models)
    assert result is None


def test_valid_models_aggregation():
    """Modelos válidos sin outliers se agregan correctamente."""
    from backend.ai.federated_learning import FederatedLearningCoordinator

    coord = FederatedLearningCoordinator()
    m1 = _add_hash({"weights": {"layer1": [0.1, 0.2]}, "confidence": 0.9})
    m2 = _add_hash({"weights": {"layer1": [0.15, 0.25]}, "confidence": 0.8})
    result = coord._aggregate_models([{"model1": m1}, {"model1": m2}])
    assert result is not None
    assert "model1" in result
    assert "aggregation_metadata" in result["model1"]
