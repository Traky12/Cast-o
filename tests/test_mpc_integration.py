# tests/test_mpc_integration.py — Pruebas de MPC (Multi-Party Computation) para claves distribuidas

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_mpc_integration_generate_distributed_key():
    """MPCIntegration genera clave distribuida con shares y umbral."""
    from backend.security.mpc_integration import MPCIntegration

    mpc = MPCIntegration(threshold=3, total_parties=5)
    result = mpc.generate_distributed_key(key_size=4096)
    assert "shares" in result
    assert len(result["shares"]) == 5
    assert result["threshold"] == 3
    assert result["total_parties"] == 5
    assert result.get("algorithm") == "Shamir's Secret Sharing"
    for k, v in result["shares"].items():
        assert "share" in v
        assert "public_key" in v


def test_mpc_integration_reconstruct_key():
    """Reconstrucción de clave requiere al menos threshold shares."""
    from backend.security.mpc_integration import MPCIntegration

    mpc = MPCIntegration(threshold=3, total_parties=5)
    with pytest.raises(ValueError, match="al menos 3 shares"):
        mpc.reconstruct_key({})
    with pytest.raises(ValueError, match="al menos 3 shares"):
        mpc.reconstruct_key({"p1": "x", "p2": "y"})
    reconstructed = mpc.reconstruct_key({"p1": "a", "p2": "b", "p3": "c"})
    assert isinstance(reconstructed, bytes)
    assert len(reconstructed) > 0


def test_end_to_end_encryption_use_mpc():
    """EndToEndEncryption.generate_secure_key_pair(use_mpc=True) devuelve claves MPC."""
    from backend.security.end_to_end_encryption import EndToEndEncryption

    e = EndToEndEncryption()
    assert hasattr(e, "mpc_integration")
    priv, pub = e.generate_secure_key_pair(use_mpc=True)
    assert priv == b"mpc_private_key"
    assert pub == b"mpc_public_key"
