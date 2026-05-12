from __future__ import annotations

import jwt
from fastapi.testclient import TestClient

from api.main import app


def _auth_header(secret: str, role: str = "admin_general") -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "hardening-test-user",
            "roles": [role],
        },
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_claude_tools_requires_auth_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    client = TestClient(app)

    response = client.get("/api/v1/claude/tools")

    assert response.status_code == 401


def test_claude_tools_requires_privileged_role_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    client = TestClient(app)

    response = client.get(
        "/api/v1/claude/tools",
        headers=_auth_header("test-jwt-secret", role="usuario"),
    )

    assert response.status_code == 403


def test_gdpr_delete_rejects_invalid_bearer_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")

    client = TestClient(app)
    response = client.delete(
        "/api/v1/admin/gdpr/users/tenantA",
        headers={"Authorization": "Bearer invalid"},
    )

    assert response.status_code == 401


def test_traces_submit_requires_auth_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    client = TestClient(app)

    response = client.post(
        "/api/v1/traces/submit",
        json={"lote_id": "lote-001", "metadata": {}},
    )

    assert response.status_code == 401


def test_traces_submit_requires_privileged_role_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    client = TestClient(app)

    response = client.post(
        "/api/v1/traces/submit",
        json={"lote_id": "lote-001", "metadata": {}},
        headers=_auth_header("test-jwt-secret", role="usuario"),
    )

    assert response.status_code == 403


def test_ai_predict_requires_auth_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/predict",
        json={"data": {"temperature": 24.0, "humidity": 62.0}},
    )

    assert response.status_code == 401


def test_ai_predict_requires_privileged_role_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    client = TestClient(app)

    response = client.post(
        "/api/v1/ai/predict",
        json={"data": {"temperature": 24.0, "humidity": 62.0}},
        headers=_auth_header("test-jwt-secret", role="usuario"),
    )

    assert response.status_code == 403


def test_traces_submit_disabled_by_policy_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    monkeypatch.delenv("ENABLE_TRACES_SUBMIT", raising=False)
    client = TestClient(app)

    response = client.post(
        "/api/v1/traces/submit",
        json={"lote_id": "lote-002", "metadata": {}},
        headers=_auth_header("test-jwt-secret", role="admin_general"),
    )

    assert response.status_code == 503