from __future__ import annotations

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.holo_soberano import router as holo_router


def _auth_header(secret: str, role: str = "admin_general") -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "holo-test-user",
            "roles": [role],
        },
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _client() -> TestClient:
    app_local = FastAPI()
    app_local.include_router(holo_router)
    return TestClient(app_local)


def test_render_hologram_succeeds_without_holopy_runtime() -> None:
    client = _client()

    response = client.post(
        "/api/v1/holo/render",
        json={
            "farm_id": "farm-caceres-01",
            "prototype_id": 1,
            "scene": "nutrient_overlay",
            "sensor_data": {"ph": 6.1, "ec": 1.8, "temp_agua": 21.4},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["farm_id"] == "farm-caceres-01"
    assert payload["sovereignty"]["region"] == "EU"
    assert payload["engine"]["name"] == "holopy"


def test_register_tracking_and_haptics_updates_session_state() -> None:
    client = _client()

    tracking_resp = client.post(
        "/api/v1/holo/tracking/frame",
        json={
            "farm_id": "farm-badajoz-02",
            "device_id": "ultra-01",
            "hand_present": True,
            "gesture": "pinch",
            "confidence": 0.92,
            "position": {"x": 0.1, "y": 0.2, "z": 0.3},
        },
    )
    assert tracking_resp.status_code == 200

    haptics_resp = client.post(
        "/api/v1/holo/haptics/pulse",
        json={
            "farm_id": "farm-badajoz-02",
            "device_id": "ultra-haptics-01",
            "intensity": 0.7,
            "frequency_hz": 220.0,
            "duration_ms": 120,
            "pattern": "short_confirm",
        },
    )
    assert haptics_resp.status_code == 200

    status_resp = client.get("/api/v1/holo/session/farm-badajoz-02")
    assert status_resp.status_code == 200
    payload = status_resp.json()
    assert payload["tracking"]["frames_total"] >= 1
    assert payload["haptics"]["commands_total"] >= 1


def test_holopy_disabled_by_default_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "holo-secure-defaults")
    monkeypatch.delenv("ENABLE_HOLOPY_INTEGRATION", raising=False)

    client = _client()
    response = client.post(
        "/api/v1/holo/render",
        json={
            "farm_id": "farm-secure-01",
            "prototype_id": 1,
            "scene": "nutrient_overlay",
            "sensor_data": {"ph": 6.0},
        },
        headers=_auth_header("holo-secure-defaults"),
    )

    assert response.status_code == 503


def test_ultraleap_disabled_by_default_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "holo-secure-defaults")
    monkeypatch.delenv("ENABLE_ULTRALEAP_INTEGRATION", raising=False)

    client = _client()
    response = client.post(
        "/api/v1/holo/tracking/frame",
        json={
            "farm_id": "farm-secure-02",
            "device_id": "ultra-guard",
            "hand_present": True,
            "gesture": "open_hand",
            "confidence": 0.82,
        },
        headers=_auth_header("holo-secure-defaults"),
    )

    assert response.status_code == 503


def test_sabionda_context_exposes_actionable_holo_metrics() -> None:
    client = _client()
    farm_id = "farm-sabionda-context"

    client.post(
        "/api/v1/holo/render",
        json={
            "farm_id": farm_id,
            "prototype_id": 1,
            "scene": "nutrient_overlay",
            "sensor_data": {"ph": 6.2, "ec": 1.7},
        },
    )
    client.post(
        "/api/v1/holo/tracking/frame",
        json={
            "farm_id": farm_id,
            "device_id": "ultra-ctx",
            "hand_present": True,
            "gesture": "pinch",
            "confidence": 0.91,
        },
    )
    client.post(
        "/api/v1/holo/haptics/pulse",
        json={
            "farm_id": farm_id,
            "device_id": "haptic-ctx",
            "intensity": 0.6,
            "frequency_hz": 210,
            "duration_ms": 90,
            "pattern": "confirm",
        },
    )

    response = client.get(f"/api/v1/holo/sabionda/{farm_id}/context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["farm_id"] == farm_id
    assert payload["severity"] in {"info", "warning", "critical", "emergency"}
    assert "recommended_action" in payload
    assert "metrics" in payload


def test_sabionda_escalation_from_holo_metrics() -> None:
    client = _client()
    farm_id = "farm-sabionda-escalate"

    # Estado incompleto para forzar al menos warning.
    client.post(
        "/api/v1/holo/tracking/frame",
        json={
            "farm_id": farm_id,
            "device_id": "ultra-risk",
            "hand_present": False,
            "gesture": "unknown",
            "confidence": 0.2,
        },
    )

    response = client.post(f"/api/v1/holo/sabionda/{farm_id}/escalate")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "escalated"
    assert payload["farm_id"] == farm_id
    assert payload["decision"]
