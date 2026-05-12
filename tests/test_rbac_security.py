from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.blockchain_router import router as blockchain_router
from api.routers.embeddings_router import router as embeddings_router


JWT_SECRET = "test-rbac-secret"


def _token(roles: list[str]) -> str:
    payload = {
        "sub": "pytest-rbac",
        "roles": roles,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _auth_header(roles: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {_token(roles)}"}


def test_blockchain_endpoint_requires_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)

    app = FastAPI()
    app.include_router(blockchain_router)
    client = TestClient(app)

    response = client.post(
        "/api/v1/blockchain/log",
        json={"event_type": "security_test", "data": {}, "actor": "pytest"},
    )

    assert response.status_code == 401


def test_blockchain_endpoint_forbids_low_privilege_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)

    app = FastAPI()
    app.include_router(blockchain_router)
    client = TestClient(app)

    response = client.post(
        "/api/v1/blockchain/log",
        headers=_auth_header(["alumno"]),
        json={"event_type": "security_test", "data": {}, "actor": "pytest"},
    )

    assert response.status_code == 403


def test_blockchain_encrypts_sensitive_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)

    captured_payload: dict[str, Any] = {}

    def _capture(payload: dict[str, Any]) -> str:
        captured_payload.update(payload)
        return "0xtesttxid"

    app = FastAPI()
    app.include_router(blockchain_router)
    client = TestClient(app)

    with patch("castuo_graph.blockchain.gaiachain.GaiachainConnector.register_hash", side_effect=_capture):
        response = client.post(
            "/api/v1/blockchain/log",
            headers=_auth_header(["admin_general"]),
            json={
                "event_type": "sensitive_event",
                "actor": "pytest",
                "data": {
                    "nif": "12345678Z",
                    "comentario": "ok",
                },
                "sensitive_fields": ["nif"],
            },
        )

    assert response.status_code == 200
    assert captured_payload["data"]["nif"].startswith("enc:v1:")
    assert captured_payload["data"]["comentario"] == "ok"


def test_embeddings_generate_forbids_comercial_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET", JWT_SECRET)

    app = FastAPI()
    app.include_router(embeddings_router)
    client = TestClient(app)

    response = client.post(
        "/api/v1/embeddings/generate",
        headers=_auth_header(["comercial"]),
        json={
            "id": "nota-rbac",
            "content": "Texto para embeddings",
            "metadata": {"source": "pytest"},
            "path": "Vault/nota-rbac.md",
        },
    )

    assert response.status_code == 403
