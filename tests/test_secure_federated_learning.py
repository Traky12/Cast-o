# tests/test_secure_federated_learning.py — Pruebas de integración para FL seguro y estructura cifrada

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    np = None
    _NUMPY = False


def test_secure_federated_learning_flow():
    """Flujo completo: cifrado, trazabilidad, agregación y descifrado."""
    from backend.security.end_to_end_encryption import EndToEndEncryption
    from backend.compliance.immutable_traceability import ImmutableTraceability
    from backend.ai.secure_federated_learning import SecureFederatedLearningCoordinator

    encryption = EndToEndEncryption()
    traceability = ImmutableTraceability(encryption)
    coordinator = SecureFederatedLearningCoordinator(encryption, traceability)

    _, peer_public_key = encryption.generate_key_pair()
    coordinator.node_public_keys["peer1"] = peer_public_key

    if not _NUMPY or np is None:
        test_model = {
            "weights": {"layer_0": [0.1] * 10, "layer_1": [0.2] * 5},
            "confidence": 0.95,
        }
    else:
        test_model = {
            "weights": {
                "layer_0": np.random.randn(100, 50).astype(np.float32),
                "layer_1": np.random.randn(50, 20).astype(np.float32),
            },
            "confidence": 0.95,
        }

    result = asyncio.run(coordinator.secure_coordinate_round(test_model, "test_round_123"))

    assert isinstance(result, dict)
    assert "weights" in result
    assert "layer_0" in result["weights"]
    if _NUMPY and hasattr(result["weights"]["layer_0"], "shape"):
        assert result["weights"]["layer_0"].shape == (100, 50)
    else:
        assert isinstance(result["weights"]["layer_0"], (list, type(test_model["weights"]["layer_0"])))

    if coordinator.traceability and coordinator.traceability.current_chain:
        assert coordinator.traceability.current_chain[0]["event"]["type"] == "fl_round_start"


def test_encrypted_model_structure():
    """Comprueba la estructura de salida de encrypt_model_weights."""
    from backend.security.end_to_end_encryption import EndToEndEncryption

    encryption = EndToEndEncryption()
    private_key, public_key = encryption.generate_key_pair()

    if not _NUMPY or np is None:
        test_weights = {"layer_0": [0.1, 0.2, 0.3], "layer_1": [0.4, 0.5]}
    else:
        test_weights = {
            "layer_0": np.random.randn(10, 5).astype(np.float32),
            "layer_1": np.random.randn(5, 2).astype(np.float32),
        }

    encrypted = encryption.encrypt_model_weights(test_weights, public_key)

    assert "encrypted_weights" in encrypted
    assert "encryption_metadata" in encrypted
    assert encrypted["encryption_metadata"]["algorithm"] in (
        "RSA4096_AES256_GCM_Kyber1024",
        "RSA4096_AES256_GCM",
    )

    for layer_name, layer in encrypted["encrypted_weights"].items():
        assert "original_shape" in layer
        assert "dtype" in layer
        assert "ciphertext" in layer
        assert "encrypted_key" in layer
        assert "iv" in layer
        assert "tag" in layer
        if layer_name in test_weights and hasattr(test_weights[layer_name], "shape"):
            assert layer["original_shape"] == list(test_weights[layer_name].shape)
        elif layer_name in test_weights:
            assert isinstance(layer["original_shape"], list)

    decrypted = encryption.decrypt_model_weights(encrypted, private_key)
    assert set(decrypted.keys()) == set(test_weights.keys())


def test_secure_coordinator_requires_encryption():
    """El coordinador exige encryption."""
    from backend.ai.secure_federated_learning import SecureFederatedLearningCoordinator

    with pytest.raises(ValueError, match="encryption"):
        SecureFederatedLearningCoordinator(None)


def test_traceability_block_structure():
    """Comprueba las claves del bloque de trazabilidad."""
    from backend.security.end_to_end_encryption import EndToEndEncryption
    from backend.compliance.immutable_traceability import ImmutableTraceability

    encryption = EndToEndEncryption()
    traceability = ImmutableTraceability(encryption)
    traceability.register_event({"type": "test", "data": "value"}, ["data"])

    assert len(traceability.current_chain) == 1
    block = traceability.current_chain[0]
    assert set(block.keys()) == {"previous_hash", "timestamp", "event_hash", "event", "signature"}
