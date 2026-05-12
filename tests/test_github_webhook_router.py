"""Tests para el router de webhook de GitHub con validación HMAC-SHA256."""
from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient


# ─── helpers ─────────────────────────────────────────────────────────────────

def _sign(body: bytes, secret: str) -> str:
    """Genera cabecera X-Hub-Signature-256 válida."""
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


SECRET = "webhook-test-secret"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", SECRET)

    from fastapi import FastAPI
    from api.routers.github_webhook import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ─── tests ────────────────────────────────────────────────────────────────────

class TestGithubWebhookEndpoint:
    """POST /api/v1/github/webhook"""

    def test_valid_push_event_returns_200(self, client: TestClient) -> None:
        """Push con firma correcta devuelve 200 y status ok."""
        payload = json.dumps(
            {"ref": "refs/heads/main", "repository": {"full_name": "org/goldfish"}}
        ).encode()
        resp = client.post(
            "/api/v1/github/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": _sign(payload, SECRET),
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_pull_request_event_returns_200(self, client: TestClient) -> None:
        """Evento pull_request con firma válida se acepta."""
        payload = json.dumps(
            {"action": "opened", "pull_request": {"number": 42, "title": "feat: test"}}
        ).encode()
        resp = client.post(
            "/api/v1/github/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": _sign(payload, SECRET),
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200

    def test_invalid_signature_returns_401(self, client: TestClient) -> None:
        """Firma incorrecta → 401 Unauthorized."""
        payload = b'{"event": "push"}'
        resp = client.post(
            "/api/v1/github/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": "sha256=invalida",
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401

    def test_missing_signature_returns_401(self, client: TestClient) -> None:
        """Sin cabecera de firma → 401."""
        payload = b'{"event": "push"}'
        resp = client.post(
            "/api/v1/github/webhook",
            content=payload,
            headers={
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401

    def test_unknown_event_ignored_gracefully(self, client: TestClient) -> None:
        """Eventos desconocidos se aceptan sin crash (retorna status ignored o ok)."""
        payload = json.dumps({"foo": "bar"}).encode()
        resp = client.post(
            "/api/v1/github/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": _sign(payload, SECRET),
                "X-GitHub-Event": "deployment",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] in ("ok", "ignored")

    def test_replayed_body_mismatch_returns_401(self, client: TestClient) -> None:
        """Firma calculada sobre body diferente al real → 401 (replay attack)."""
        real_payload = b'{"ref": "main"}'
        fake_sig = _sign(b'{"ref": "injected"}', SECRET)
        resp = client.post(
            "/api/v1/github/webhook",
            content=real_payload,
            headers={
                "X-Hub-Signature-256": fake_sig,
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401

    def test_oversized_payload_returns_413(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Payload excesivo se rechaza para mitigar abuso/DoS."""
        monkeypatch.setenv("GITHUB_WEBHOOK_MAX_BYTES", "32")
        payload = json.dumps({"big": "x" * 256}).encode()
        resp = client.post(
            "/api/v1/github/webhook",
            content=payload,
            headers={
                "X-Hub-Signature-256": _sign(payload, SECRET),
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 413
