from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.dsar import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_dsar_access_request_returns_queued() -> None:
    response = client.post(
        "/api/v1/dsar/request",
        json={
            "user_id": "user-001",
            "request_type": "access",
            "data_category": "logs",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["request_type"] == "access"


def test_dsar_delete_request_returns_processing() -> None:
    response = client.post(
        "/api/v1/dsar/request",
        json={
            "user_id": "user-002",
            "request_type": "delete",
            "data_category": "sensors",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["data_category"] == "sensors"


def test_dsar_invalid_request_type_returns_422() -> None:
    response = client.post(
        "/api/v1/dsar/request",
        json={
            "user_id": "user-003",
            "request_type": "erase-all",
            "data_category": "blockchain",
        },
    )
    assert response.status_code == 422
