# tests/test_sandbox_manager.py — Pruebas de SandboxManager (sin cliente K8s real)

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_sandbox_manager_without_k8s_returns_simulated():
    """Sin cliente Kubernetes, create_sandbox devuelve resultado simulado."""
    from backend.ai.sandbox_manager import SandboxManager

    sm = SandboxManager(kubernetes_client=None)
    result = sm.create_sandbox("node-123", {"evidence_hash": "abc"})
    assert result["status"] == "created"
    assert "sandbox-" in result["sandbox_name"]
    assert "node-123" in result["sandbox_name"]
    assert result["original_node"] == "node-123"
    assert result.get("simulated") is True


def test_sandbox_manager_namespace():
    """SandboxManager usa namespace sandbox-environment."""
    from backend.ai.sandbox_manager import SandboxManager

    sm = SandboxManager(kubernetes_client=None)
    assert sm.sandbox_namespace == "sandbox-environment"


def test_federated_defense_quarantine_uses_sandbox():
    """FederatedDefenseSystem._quarantine_node usa SandboxManager cuando está disponible."""
    from backend.security.end_to_end_encryption import EndToEndEncryption
    from backend.compliance.immutable_traceability import ImmutableTraceability
    from backend.ai.secure_federated_learning import SecureFederatedLearningCoordinator
    from backend.ai.federated_defense import FederatedDefenseSystem
    import asyncio

    enc = EndToEndEncryption()
    trace = ImmutableTraceability(enc)
    coord = SecureFederatedLearningCoordinator(enc, trace)
    defense = FederatedDefenseSystem(enc, trace, coord)
    assert defense.sandbox_manager is not None
    evidence = {"node_id": "test-node", "evidence_hash": "h1"}
    result = asyncio.run(defense._quarantine_node(evidence))
    assert result["action"] == "quarantine"
    assert result["status"] == "success"
    assert result.get("sandbox") or result.get("details")
