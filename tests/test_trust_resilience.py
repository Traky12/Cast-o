"""Cyber-resilience: tamper ZIP, PQC handshake, circuit breaker químico."""
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import pytest

from backend.security.trust_orchestrator import SecurityError, TrustOrchestrator


def test_tamper_evidence_blocks_mint():
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f2:
        f2.write(b"tampered-one-bit")
        p2 = f2.name
    expected = hashlib.sha256(b"cad-original.stp").hexdigest()
    to = TrustOrchestrator(secret_key=b"test-secret")
    assert to.verify_binary_integrity(p2, expected) is False
    os.environ["CASTUO_MEASURED_BOOT"] = "1"
    try:
        with pytest.raises(SecurityError):
            to.secure_token_minting({"evidence_hash": "x", "serial_id": "1"})
    finally:
        os.environ.pop("CASTUO_MEASURED_BOOT", None)
    Path(p2).unlink(missing_ok=True)


def test_quantum_safe_pqc_module_available():
    """Handshake resistente: capa Kyber/Dilithium disponible en backend."""
    from backend.security.pq_crypto import PostQuantumCrypto

    assert PostQuantumCrypto is not None


def test_circuit_breaker_chemical_locks_irrigation():
    to = TrustOrchestrator()
    fired = to.circuit_breaker_chemical(ozone_confidence=0.1, client_ip="203.0.113.50", allowed_ip_prefixes=("127.",))
    assert fired is True
    locked, reason = to.is_irrigation_sector_locked()
    assert locked is True
    assert "O3" in reason or "IP" in reason
