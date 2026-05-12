import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.trl6

os.environ["CASTUO_ROBOTICS_LAB_BEARER_TOKEN"] = "test-bearer-secret"


@pytest.fixture()
def client():
    from backend.integrations.robotics.lab_stub_app import app

    return TestClient(app)


def test_snapshot_ok_with_bearer(client):
    body = _minimal_body()
    r = client.post(
        "/api/robotics/lab/snapshot",
        json=body,
        headers={"Authorization": "Bearer test-bearer-secret"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "stub-registered"
    assert data["tx_id"] is None
    assert data["gaia_chain_digest"].startswith("sha256:")
    assert data["compliance"] is True
    assert data.get("chain_registration") == "none"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "robotics-lab-stub"
    assert data.get("chain_status") == "disabled"
    assert "neuromorphic_lab" in data


def _minimal_body():
    return {
        "parcel_id": "P1",
        "timestamp": "2026-03-22T00:00:00Z",
        "intervention_type": "riego_precision",
        "metrics_summary": {"volumen_ml": 1},
        "sigpac_compliant": True,
        "audit_event": "PEI001_REGISTERED",
    }
