"""Puerta TRL-6 de integración del monorepo (pytest); no certifica TRL de campo ni de silicio."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.trl6

os.environ.setdefault("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
os.environ.setdefault("TRL_LEVEL", "TRL-6-staging")


def test_trl6_terpene_profiles_integration_label():
    from agrotech.terpene_profiles import TERPENE_PROFILES

    for name, prof in TERPENE_PROFILES.items():
        assert prof.get("trl") == "TRL-6-staging-gate", name
        assert "TRL-6" in prof["description"]


def test_trl6_infer_traceability_block():
    from backend.integrations.robotics.neuromorphic_edge import _hydro_traceability_block

    t = _hydro_traceability_block("mirceno")
    assert t["processing_purpose"] == "agronomic_research_TRL6"
    assert t["trl"] == "TRL-6-staging"
    assert "validation_checks" in t
    assert t["tier_disclosure"]["neuromorphic_simulation"] == "TRL-4-lab-sim"
    assert t["tier_disclosure"]["integration_gate"] == "TRL-6-staging"
    assert t["model_tier"] == "TRL-6-staging"
    assert t["model_implementation_note"] == "SNN TRL-4 (NeuromorphicEdge v2.0)"
    assert "deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md" in t["governance_doc_paths"]


def test_trl6_infer_endpoint_traceability():
    from fastapi.testclient import TestClient

    from backend.integrations.robotics.lab_stub_app import app

    c = TestClient(app)
    token = os.environ["CASTUO_ROBOTICS_LAB_BEARER_TOKEN"]
    r = c.post(
        "/api/robotics/lab/neuromorphic/hydroponics/infer",
        json={"humedad": 50, "ph": 6.0, "ec": 1.2, "luz_umol": 900, "target_terpene": "mirceno"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    tr = r.json()["inference"]["traceability"]
    assert tr["processing_purpose"] == "agronomic_research_TRL6"
    assert tr["tier_disclosure"]["integration_gate"] == "TRL-6-staging"


def test_trl6_traceability_without_trl6_env(monkeypatch):
    monkeypatch.setenv("TRL_LEVEL", "TRL-4-only")
    from backend.integrations.robotics.neuromorphic_edge import _hydro_traceability_block

    t = _hydro_traceability_block(None)
    assert t["processing_purpose"] == "agronomic_research"
    assert t["model_tier"] == "research_grade"
    assert t["tier_disclosure"]["integration_gate"] == "not-applicable"


def test_trl6_playbook_lists_agrotech_ethics():
    from backend.models.system_admin_playbook import GOVERNANCE_DOCUMENTATION

    paths = {d["ruta"] for d in GOVERNANCE_DOCUMENTATION}
    assert "agrotech/ETHICS_TRACEABILITY.md" in paths
    assert "docs/deploy/PRONTUARIO-AGROTECH-TLS.md" in paths
    assert "deploy/CHECKLIST-TRL7-INDUSTRIAL-LIVE.md" in paths
