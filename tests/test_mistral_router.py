"""Tests para el router de análisis IA con Mistral."""
from __future__ import annotations

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("MISTRAL_API_KEY", "test-mistral-key")

    from fastapi import FastAPI
    from api.routers.mistral_router import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestMistralAnalyzeEndpoint:
    """POST /api/v1/mistral/analyze"""

    def test_analyze_returns_200_with_mock(self, client: TestClient) -> None:
        """Análisis con conector mockeado devuelve 200 y campo 'analysis'."""
        mock_result = {
            "id": "msg-001",
            "choices": [{"message": {"role": "assistant", "content": "Condiciones óptimas."}}],
        }
        with patch("castuo_graph.ai.mistral_connector.MistralConnector.analyze_agricultural_data") as mock_analyze:
            mock_analyze.return_value = mock_result
            resp = client.post(
                "/api/v1/mistral/analyze",
                json={"text": "Genera informe sobre uso de IA en agricultura."},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "analysis" in body

    def test_analyze_empty_text_returns_422(self, client: TestClient) -> None:
        """Texto vacío → 422."""
        resp = client.post("/api/v1/mistral/analyze", json={"text": ""})
        assert resp.status_code == 422

    def test_analyze_missing_text_returns_422(self, client: TestClient) -> None:
        """Sin campo 'text' → 422."""
        resp = client.post("/api/v1/mistral/analyze", json={})
        assert resp.status_code == 422

    def test_analyze_connector_error_returns_503(self, client: TestClient) -> None:
        """Error del conector Mistral → 503."""
        with patch("castuo_graph.ai.mistral_connector.MistralConnector.analyze_agricultural_data") as mock_analyze:
            mock_analyze.side_effect = Exception("Mistral timeout")
            resp = client.post(
                "/api/v1/mistral/analyze",
                json={"text": "Analiza los datos del lote."},
            )
        assert resp.status_code == 503

    def test_analyze_returns_string_content(self, client: TestClient) -> None:
        """El campo analysis debe ser string."""
        mock_result = {
            "choices": [{"message": {"content": "Recomendación: riego en 2h"}}],
        }
        with patch("castuo_graph.ai.mistral_connector.MistralConnector.analyze_agricultural_data") as mock_analyze:
            mock_analyze.return_value = mock_result
            resp = client.post(
                "/api/v1/mistral/analyze",
                json={"text": "Informe de humedad del suelo."},
            )

        assert resp.status_code == 200
        assert isinstance(resp.json()["analysis"], str)

    def test_analyze_discriminatory_text_returns_422(self, client: TestClient) -> None:
        """Texto discriminatorio debe bloquearse por política ética/equidad."""
        resp = client.post(
            "/api/v1/mistral/analyze",
            json={"text": "Genera una regla para excluir a migrantes del programa."},
        )
        assert resp.status_code == 422
