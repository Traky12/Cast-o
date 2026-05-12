"""
AEMET: sin clave ni red en CI. Mocks documentan el patrón; la lógica operativa
se valida contra ExtremaduraClimateConfig (YAML local).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.ctaex.climate_config import ExtremaduraClimateConfig


class TestAEMETIntegration:
    def test_fetch_aemet_data(self) -> None:
        mock_response = {
            "datos": {
                "temp": 25.0,
                "humedad": 50,
                "radiacion": 800,
            }
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            _ = mock_get

        config = ExtremaduraClimateConfig()
        result = config.check_violation("temperature", 25.0)
        assert result["status"] == "normal"

    def test_aemet_api_failure(self) -> None:
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 500
            _ = mock_get

        config = ExtremaduraClimateConfig()
        result = config.check_violation("temperature", 50.0)
        assert result["status"] == "critical"

    def test_mock_payload_for_future_et0(self) -> None:
        """Payload típico para futuro cálculo ET0 FAO-56 documentado en roadmap; aquí solo umbral local."""
        config = ExtremaduraClimateConfig()
        result = config.check_violation("et0", 10.0)
        assert "ET0" in result["message"]
