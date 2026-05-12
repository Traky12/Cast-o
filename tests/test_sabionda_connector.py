"""Tests for Sabionda IA Connector."""
import pytest
from typing import Any
from unittest.mock import patch

from castuo_graph.ai.sabionda_connector import SabiondaConnector


@pytest.fixture
def sabionda_key() -> str:
    return "test-sabionda-api-key"


@pytest.fixture
def connector(sabionda_key: str) -> Any:
    """Create a SabiondaConnector with mocked client."""
    with patch('castuo_graph.ai.sabionda_connector.SabiondaClient'):
        return SabiondaConnector(api_key=sabionda_key)


@pytest.fixture
def sample_crop_data() -> dict[str, Any]:
    return {
        "humidity": 70,
        "temperature": 25,
        "soil_ph": 6.5,
        "historical_yield": [1200, 1300, 1250],
        "crop": "tomate",
        "region": "Norte",
        "planting_date": "2026-02-01"
    }


class TestSabiondaConnector:
    """Test suite for SabiondaConnector class."""

    def test_init_with_api_key(self, sabionda_key: str) -> None:
        """Test connector initialization with API key."""
        with patch('castuo_graph.ai.sabionda_connector.SabiondaClient') as mock_client_class:
            SabiondaConnector(api_key=sabionda_key)
            mock_client_class.assert_called_once_with(api_key=sabionda_key)

    def test_predict_crop_yield_returns_dict(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test that predict_crop_yield returns a dictionary."""
        mock_response = {
            "predicted_yield": 1280,
            "confidence": 0.92,
            "recommendation": "Aplicar riego foliar en etapa de floración"
        }
        connector.client.analyze_crop_data.return_value = mock_response

        result = connector.predict_crop_yield(sample_crop_data)

        assert isinstance(result, dict)
        assert "predicted_yield" in result

    def test_predict_crop_yield_calls_client_method(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test that the client method is called with correct data."""
        connector.client.analyze_crop_data.return_value = {"predicted_yield": 1280}

        connector.predict_crop_yield(sample_crop_data)

        connector.client.analyze_crop_data.assert_called_once_with(sample_crop_data)

    def test_predict_crop_yield_structure(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test response structure contains expected fields."""
        mock_response = {
            "predicted_yield": 1280,
            "confidence": 0.92,
            "recommendation": "Aplicar riego foliar",
            "risk_factors": ["plagas", "sequía"],
            "optimal_harvest_date": "2026-07-15"
        }
        connector.client.analyze_crop_data.return_value = mock_response

        result = connector.predict_crop_yield(sample_crop_data)

        assert result["predicted_yield"] > 0
        assert 0 <= result["confidence"] <= 1
        assert "recommendation" in result

    def test_predict_crop_yield_with_minimal_data(self, connector: Any) -> None:
        """Test prediction with minimal required data."""
        minimal_data = {
            "humidity": 70,
            "temperature": 25,
            "soil_ph": 6.5,
            "historical_yield": [1200, 1300]
        }
        
        mock_response = {"predicted_yield": 1250, "confidence": 0.85}
        connector.client.analyze_crop_data.return_value = mock_response

        result = connector.predict_crop_yield(minimal_data)

        assert result["predicted_yield"] is not None

    def test_predict_crop_yield_historical_data_validation(self, connector: Any) -> None:
        """Test that historical yield data is properly used."""
        data = {
            "humidity": 70,
            "temperature": 25,
            "soil_ph": 6.5,
            "historical_yield": [1000, 1200, 1150, 1300],  # Multiple years
        }
        
        connector.client.analyze_crop_data.return_value = {"predicted_yield": 1212}

        connector.predict_crop_yield(data)

        # Verify call was made with the data
        connector.client.analyze_crop_data.assert_called_once_with(data)

    def test_predict_crop_yield_handles_api_error(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test error handling for API failures."""
        connector.client.analyze_crop_data.side_effect = Exception("API error")

        with pytest.raises(Exception):
            connector.predict_crop_yield(sample_crop_data)

    def test_predict_crop_yield_returns_zero_or_positive(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test that predicted yield is always non-negative."""
        mock_response = {
            "predicted_yield": 0,  # Edge case: zero yield
            "confidence": 0.5
        }
        connector.client.analyze_crop_data.return_value = mock_response

        result = connector.predict_crop_yield(sample_crop_data)

        assert result["predicted_yield"] >= 0

    def test_predict_crop_yield_confidence_range(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test that confidence is between 0 and 1."""
        for conf_value in (0.0, 0.5, 1.0):
            mock_response: dict[str, float] = {
                "predicted_yield": 1280,
                "confidence": conf_value
            }
            connector.client.analyze_crop_data.return_value = mock_response

            result = connector.predict_crop_yield(sample_crop_data)

            assert 0 <= result["confidence"] <= 1

    def test_multiple_predictions_consistency(
        self,
        connector: Any,
        sample_crop_data: dict[str, Any],
    ) -> None:
        """Test multiple predictions maintain consistency."""
        responses = [
            {"predicted_yield": 1280, "confidence": 0.92},
            {"predicted_yield": 1275, "confidence": 0.91},
            {"predicted_yield": 1285, "confidence": 0.93}
        ]
        
        for response in responses:
            connector.client.analyze_crop_data.return_value = response
            result = connector.predict_crop_yield(sample_crop_data)
            assert 1270 <= result["predicted_yield"] <= 1290
