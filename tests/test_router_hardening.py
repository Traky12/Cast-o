from __future__ import annotations

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.claude_router import router as claude_router
from api.routers.dsar import router as dsar_router
from api.routers.gdpr import router as gdpr_router
from api.routers.mistral_router import router as mistral_router


def _auth_header(secret: str, role: str = "admin_general") -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "router-hardening-user",
            "roles": [role],
        },
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(claude_router)
    app.include_router(mistral_router)
    app.include_router(dsar_router)
    app.include_router(gdpr_router)
    return TestClient(app)


def test_dsar_requires_auth_in_production(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "router-hardening-secret")

    response = client.post(
        "/api/v1/dsar/request",
        json={
            "user_id": "user-001",
            "request_type": "access",
            "data_category": "logs",
        },
    )

    assert response.status_code == 401


def test_claude_requires_privileged_role_in_production(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "router-hardening-secret")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")

    response = client.post(
        "/api/v1/claude/generate",
        json={"prompt": "hola"},
        headers=_auth_header("router-hardening-secret", role="usuario"),
    )

    assert response.status_code == 403


def test_mistral_requires_auth_in_production(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "router-hardening-secret")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key")

    response = client.post(
        "/api/v1/mistral/analyze",
        json={"text": "analiza esto"},
    )

    assert response.status_code == 401


def test_gdpr_requires_auth_in_production(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "router-hardening-secret")

    response = client.post("/api/v1/gdpr/delete", params={"user_id": "u-001"})

    assert response.status_code == 401