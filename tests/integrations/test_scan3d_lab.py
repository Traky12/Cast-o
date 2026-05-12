import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.trl6

os.environ.setdefault("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")


@pytest.fixture()
def client():
    from backend.integrations.robotics.lab_stub_app import app

    return TestClient(app)


def test_scan3d_json(client):
    tok = os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
    r = client.post(
        "/api/robotics/lab/scan3d/scan",
        json={"filename": "hydro_v1.ply", "points": 125_000, "format": "pointcloud"},
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["result"]["mesh_points"] == 125_000
    assert "chain_seal" in data
    assert 5 <= data["result"]["volume_cm3"] <= 150


def test_scan3d_print_job(client):
    tok = os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
    r = client.post(
        "/api/robotics/lab/scan3d/print",
        json={
            "scan_id": "scan_20260322",
            "printer_model": "fdm_lab",
            "infill": 25,
            "layer_height": 0.2,
            "material": "PLA+",
            "volume_cm3": 42.0,
            "apply_neuro_hints": True,
        },
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "gcode-ready"
    assert data["chain_seal"]
    assert data["neuro_hints"]["infill"] in (15, 30)
    assert data.get("chain_registration") == "none"


def test_scan3d_upload_small(client):
    tok = os.environ.get("CASTUO_ROBOTICS_LAB_BEARER_TOKEN", "test-bearer-secret")
    r = client.post(
        "/api/robotics/lab/scan3d/scan/upload",
        content=b"fakeply" * 500,
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": "application/octet-stream",
            "Content-Disposition": 'attachment; filename="t.ply"',
        },
    )
    assert r.status_code == 200
    assert r.json()["result"]["mesh_points"] >= 1000
