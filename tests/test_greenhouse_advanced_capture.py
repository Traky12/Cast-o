from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.greenhouse import router as greenhouse_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(greenhouse_router)
    return TestClient(app)


def test_register_holography_capture() -> None:
    client = _client()
    response = client.post(
        "/api/v1/greenhouse/1/holography/register",
        json={
            "device_id": "holo-p1-cam",
            "resolution": "4k",
            "point_density": 125000.0,
            "coverage_percent": 92.5,
            "operator_id": "ops-01",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["prototype_id"] == 1
    assert payload["registered"] is True
    assert payload["capture"]["coverage_percent"] == 92.5


def test_register_photogrammetry_scan() -> None:
    client = _client()
    response = client.post(
        "/api/v1/greenhouse/2/photogrammetry/register",
        json={
            "device_id": "photo-p2-rig",
            "images_count": 96,
            "overlap_percent": 78.0,
            "avg_reprojection_error": 0.42,
            "operator_id": "ops-02",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["prototype_id"] == 2
    assert payload["registered"] is True
    assert payload["capture"]["images_count"] == 96


def test_digital_twin_status_includes_3d_systems() -> None:
    client = _client()

    # Seed data for prototype 1
    client.post(
        "/api/v1/greenhouse/1/holography/register",
        json={
            "device_id": "holo-p1-cam",
            "resolution": "4k",
            "point_density": 120000.0,
            "coverage_percent": 90.0,
        },
    )
    client.post(
        "/api/v1/greenhouse/1/photogrammetry/register",
        json={
            "device_id": "photo-p1-rig",
            "images_count": 80,
            "overlap_percent": 75.0,
            "avg_reprojection_error": 0.5,
        },
    )

    response = client.get("/api/v1/greenhouse/1/digital-twin/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["prototype_id"] == 1
    assert payload["holography"]["captures_total"] >= 1
    assert payload["photogrammetry"]["captures_total"] >= 1
    assert payload["system_ready"] in {True, False}
