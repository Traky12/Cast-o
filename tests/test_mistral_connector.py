"""Tests for Mistral AI Connector."""
import pytest
import os
from typing import Any
from unittest.mock import patch

from castuo_graph.ai.mistral_connector import MistralConnector


@pytest.fixture
def mistral_key() -> str:
    return "test-mistral-api-key"


@pytest.fixture
def connector(mistral_key: str) -> MistralConnector:
    return MistralConnector(api_key=mistral_key)


@pytest.fixture
def sample_agricultural_data() -> dict[str, Any]:
    return {
        "humidity": 70,
        "temperature": 25,
        "soil_ph": 6.5,
        "crop": "tomate",
        "location": "Campo Sur",
        "timestamp": "2026-04-01T10:30:00Z"
    }


class TestMistralConnector:
    """Test suite for MistralConnector class."""

    def test_init_with_api_key(self, mistral_key: str) -> None:
        """Test connector initialization with API key."""
        connector = MistralConnector(api_key=mistral_key)
        assert connector.api_key == mistral_key
        assert connector.base_url == "https://api.mistral.ai/v1/chat"

    def test_analyze_agricultural_data_structure(
        self,
        connector: MistralConnector,
        sample_agricultural_data: dict[str, Any],
    ) -> None:
        """Test that analyze_agricultural_data returns expected structure."""
        with patch('requests.post') as mock_post:
            mock_response = {
                "id": "model-12345",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "Análisis: Condiciones óptimas para tomate"
                        }
                    }
                ]
            }
            mock_post.return_value.json.return_value = mock_response

            result = connector.analyze_agricultural_data(sample_agricultural_data)
            
            assert "choices" in result
            assert result["choices"][0]["message"]["content"] is not None
            assert "Análisis" in result["choices"][0]["message"]["content"]

    def test_analyze_agricultural_data_calls_correct_endpoint(
        self,
        connector: MistralConnector,
        sample_agricultural_data: dict[str, Any],
    ) -> None:
        """Test that the correct API endpoint is called."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"choices": []}

            connector.analyze_agricultural_data(sample_agricultural_data)

            # Verify the correct URL was called
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://api.mistral.ai/v1/chat"

    def test_analyze_agricultural_data_includes_auth_header(
        self,
        connector: MistralConnector,
        sample_agricultural_data: dict[str, Any],
        mistral_key: str,
    ) -> None:
        """Test that Authorization header is included."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"choices": []}

            connector.analyze_agricultural_data(sample_agricultural_data)

            # Verify Authorization header
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == f"Bearer {mistral_key}"

    def test_analyze_agricultural_data_prompt_includes_all_fields(
        self,
        connector: MistralConnector,
        sample_agricultural_data: dict[str, Any],
    ) -> None:
        """Test that prompt includes all agricultural data."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"choices": []}

            connector.analyze_agricultural_data(sample_agricultural_data)

            # Get the payload
            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            prompt = payload["messages"][0]["content"]

            # Verify all critical fields are in the prompt
            assert "70" in prompt  # humidity
            assert "25" in prompt  # temperature
            assert "6.5" in prompt  # soil_ph
            assert "tomate" in prompt  # crop

    def test_analyze_agricultural_data_model_selection(
        self,
        connector: MistralConnector,
        sample_agricultural_data: dict[str, Any],
    ) -> None:
        """Test that correct Mistral model is selected."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"choices": []}

            connector.analyze_agricultural_data(sample_agricultural_data)

            call_args = mock_post.call_args
            payload = call_args[1]["json"]
            assert payload["model"] in ["mistral-small", "mistral-tiny", "mistral-medium"]

    @patch.dict(os.environ, {"MISTRAL_API_KEY": "env-key"})
    def test_init_from_environment_variable(self) -> None:
        """Test that connector can read API key from environment."""
        api_key = os.getenv("MISTRAL_API_KEY")
        assert api_key is not None
        connector = MistralConnector(api_key=api_key)
        assert connector.api_key == "env-key"

    def test_analyze_agricultural_data_handles_api_error(
        self,
        connector: MistralConnector,
        sample_agricultural_data: dict[str, Any],
    ) -> None:
        """Test error handling for API failures."""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("API connection failed")

            with pytest.raises(Exception):
                connector.analyze_agricultural_data(sample_agricultural_data)

    def test_analyze_agricultural_data_missing_crop_field(
        self,
        connector: MistralConnector,
    ) -> None:
        """Test handling of missing optional crop field."""
        data_without_crop = {
            "humidity": 70,
            "temperature": 25,
            "soil_ph": 6.5
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"choices": []}

            connector.analyze_agricultural_data(data_without_crop)
            
            call_args = mock_post.call_args
            prompt = call_args[1]["json"]["messages"][0]["content"]
            assert "desconocido" in prompt or "unknown" in prompt.lower()
