from __future__ import annotations

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.main import app
from api.routers.claude_router import router as claude_router
from api.routers.mistral_router import router as mistral_router


def _auth_header(secret: str, role: str = "admin_general") -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": "secure-defaults-user",
            "roles": [role],
        },
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_traces_submit_disabled_by_default_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "secure-defaults-secret")
    monkeypatch.delenv("ENABLE_TRACES_SUBMIT", raising=False)

    client = TestClient(app)
    response = client.post(
        "/api/v1/traces/submit",
        json={"lote_id": "lote-secure-default", "metadata": {}},
        headers=_auth_header("secure-defaults-secret"),
    )

    assert response.status_code == 503


def test_claude_integration_disabled_by_default_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "secure-defaults-secret")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")
    monkeypatch.delenv("ENABLE_CLAUDE_INTEGRATION", raising=False)

    app_local = FastAPI()
    app_local.include_router(claude_router)
    client = TestClient(app_local)

    response = client.post(
        "/api/v1/claude/generate",
        json={"prompt": "Describe un riego eficiente."},
        headers=_auth_header("secure-defaults-secret"),
    )

    assert response.status_code == 503


def test_mistral_integration_disabled_by_default_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("JWT_SECRET", "secure-defaults-secret")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key")
    monkeypatch.delenv("ENABLE_MISTRAL_INTEGRATION", raising=False)

    app_local = FastAPI()
    app_local.include_router(mistral_router)
    client = TestClient(app_local)

    response = client.post(
        "/api/v1/mistral/analyze",
        json={"text": "Analiza humedad y temperatura."},
        headers=_auth_header("secure-defaults-secret"),
    )

    assert response.status_code == 503


def test_environment_alias_triggers_production_guards(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "secure-defaults-secret")
    monkeypatch.delenv("ENABLE_TRACES_SUBMIT", raising=False)

    client = TestClient(app)
    response = client.post(
        "/api/v1/traces/submit",
        json={"lote_id": "lote-env-alias", "metadata": {}},
        headers=_auth_header("secure-defaults-secret"),
    )

    assert response.status_code == 503
