from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("DEMO_TRL101_DATA_DIR", str(tmp_path / "trl101"))
    from backend.demo_trl101.router import router as gemelo_router

    app = FastAPI()
    app.include_router(gemelo_router, prefix="/agents/gemelo")
    return TestClient(app)


def test_ingest_rejects_empty_sensor(client: TestClient) -> None:
    r = client.post("/agents/gemelo/ingest", json={"agent_type": "agrovoltaico", "sensor_data": {}})
    assert r.status_code == 400


def test_ingest_success_and_artifacts(client: TestClient) -> None:
    r = client.post(
        "/agents/gemelo/ingest",
        json={
            "agent_type": "agrovoltaico",
            "sensor_data": {"temperature": 22.0, "humidity": 55, "co2": 400},
            "generate_invoice": True,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "success"
    assert data["gemelo_id"].startswith("gemelo-")
    gid = data["gemelo_id"]
    assert data.get("certificate_html_url")

    h = client.get(f"/agents/gemelo/artifacts/certificate/{gid}.html")
    assert h.status_code == 200


def test_dashboard(client: TestClient) -> None:
    r = client.get("/agents/gemelo/dashboard")
    assert r.status_code == 200
    assert "ingest" in r.text.lower()
