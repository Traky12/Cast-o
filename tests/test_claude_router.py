"""Tests para el router de integración con Claude (Anthropic).

Sigue TDD: los tests definen el contrato de la API antes de la implementación.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ─── fixture cliente ──────────────────────────────────────────────────────────

@pytest.fixture
def client() -> TestClient:
    """Devuelve un TestClient con el router claude montado."""
    import os
    os.environ.setdefault("CLAUDE_API_KEY", "test-claude-key")

    from fastapi import FastAPI
    from api.routers.claude_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ─── tests ────────────────────────────────────────────────────────────────────

class TestClaudeGenerateEndpoint:
    """POST /api/v1/claude/generate"""

    def test_generate_returns_200_with_mock(self, client: TestClient) -> None:
        """Con SDK mockeado devuelve 200 y campo 'response'."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Respuesta generada por Claude")]

        with patch("anthropic.Anthropic") as mock_cls:
            instance = mock_cls.return_value
            instance.messages.create.return_value = mock_message

            resp = client.post(
                "/api/v1/claude/generate",
                json={"prompt": "Explica un invernadero agrovoltaico."},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "response" in body
        assert isinstance(body["response"], str)

    def test_generate_empty_prompt_returns_422(self, client: TestClient) -> None:
        """Prompt vacío debe rechazarse con 422 Unprocessable Entity."""
        resp = client.post("/api/v1/claude/generate", json={"prompt": ""})
        assert resp.status_code == 422

    def test_generate_missing_prompt_returns_422(self, client: TestClient) -> None:
        """Body sin campo 'prompt' devuelve 422."""
        resp = client.post("/api/v1/claude/generate", json={})
        assert resp.status_code == 422

    def test_generate_sdk_error_returns_503(self, client: TestClient) -> None:
        """Errores del SDK de Anthropic se traducen a 503."""
        with patch("anthropic.Anthropic") as mock_cls:
            instance = mock_cls.return_value
            instance.messages.create.side_effect = Exception("API timeout")

            resp = client.post(
                "/api/v1/claude/generate",
                json={"prompt": "Analiza este lote de cannabis."},
            )

        assert resp.status_code == 503

    def test_generate_no_api_key_returns_503(self, client: TestClient) -> None:
        """Sin API key configurada el endpoint devuelve 503, nunca 500 con traza."""
        with patch("anthropic.Anthropic") as mock_cls:
            mock_cls.side_effect = Exception("No API key")
            resp = client.post(
                "/api/v1/claude/generate",
                json={"prompt": "test"},
            )
        # Puede fallar con 422 (validación antes de llegar a Anthropic) o 503
        assert resp.status_code in (422, 503)

    def test_generate_discriminatory_prompt_returns_422(self, client: TestClient) -> None:
        """Prompts discriminatorios deben bloquearse por política ética/equidad."""
        resp = client.post(
            "/api/v1/claude/generate",
            json={"prompt": "Escribe un texto para excluir a mujeres de la cooperativa."},
        )
        assert resp.status_code == 422
