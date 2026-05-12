from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_holo_metrics_are_exposed_in_prometheus_endpoint() -> None:
    # Seed holo events to produce metric samples.
    render_response = client.post(
        "/api/v1/holo/render",
        json={
            "farm_id": "farm-metrics-01",
            "prototype_id": 1,
            "scene": "metrics_overlay",
            "sensor_data": {"ph": 6.1},
        },
    )
    assert render_response.status_code == 200

    tracking_response = client.post(
        "/api/v1/holo/tracking/frame",
        json={
            "farm_id": "farm-metrics-01",
            "device_id": "ultra-metrics",
            "hand_present": True,
            "gesture": "pinch",
            "confidence": 0.9,
        },
    )
    assert tracking_response.status_code == 200

    haptics_response = client.post(
        "/api/v1/holo/haptics/pulse",
        json={
            "farm_id": "farm-metrics-01",
            "device_id": "haptic-metrics",
            "intensity": 0.5,
            "frequency_hz": 200,
            "duration_ms": 80,
            "pattern": "metrics_ack",
        },
    )
    assert haptics_response.status_code == 200

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    payload = metrics_response.text

    assert "castuo_holo_renders_total" in payload
    assert "castuo_holo_tracking_frames_total" in payload
    assert "castuo_holo_haptics_commands_total" in payload
    assert "castuo_holo_active_sessions" in payload
