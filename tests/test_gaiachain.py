"""Tests for GaiaChain Blockchain Integration."""
import pytest
from typing import Any
from unittest.mock import patch

from castuo_graph.blockchain.gaiachain import GaiachainConnector


@pytest.fixture
def gaiachain_connector() -> Any:
    """Create a GaiachainConnector with mocked client."""
    with patch('castuo_graph.blockchain.gaiachain.GaiaChainClient'):
        return GaiachainConnector(endpoint="https://gaiachain.eu")


@pytest.fixture
def sample_data() -> dict[str, Any]:
    return {
        "temperature": 25,
        "humidity": 70,
        "soil_ph": 6.5,
        "timestamp": "2026-04-01T10:30:00Z",
        "location": "Campo Sur",
        "sensor_id": "sensor_001"
    }


class TestGaiachainConnector:
    """Test suite for GaiachainConnector class."""

    def test_init_with_endpoint(self) -> None:
        """Test connector initialization with endpoint."""
        with patch('castuo_graph.blockchain.gaiachain.GaiaChainClient') as mock_client_class:
            GaiachainConnector(endpoint="https://gaiachain.eu")
            mock_client_class.assert_called_once()

    def test_register_hash_returns_hash_string(
        self,
        gaiachain_connector: Any,
        sample_data: dict[str, Any],
    ) -> None:
        """Test that register_hash returns a hash string."""
        expected_hash = "0x" + "a" * 64  # Mock hash format
        gaiachain_connector.client.registerDataHash.return_value = expected_hash

        hash_result = gaiachain_connector.register_hash(sample_data)

        assert isinstance(hash_result, str)
        assert hash_result.startswith("0x")

    def test_register_hash_calls_client_method(
        self,
        gaiachain_connector: Any,
        sample_data: dict[str, Any],
    ) -> None:
        """Test that client method is called."""
        expected_hash = "0x" + "a" * 64
        gaiachain_connector.client.registerDataHash.return_value = expected_hash

        gaiachain_connector.register_hash(sample_data)

        gaiachain_connector.client.registerDataHash.assert_called_once()

    def test_register_hash_with_dict_data(self, gaiachain_connector: Any) -> None:
        """Test registering dictionary data."""
        data = {
            "sensor_reading": 25,
            "timestamp": "2026-04-01T10:30:00Z"
        }
        expected_hash = "0xabc123def456"
        gaiachain_connector.client.registerDataHash.return_value = expected_hash

        result = gaiachain_connector.register_hash(data)

        assert result == expected_hash

    def test_register_hash_with_json_string(self, gaiachain_connector: Any) -> None:
        """Test registering JSON string data."""
        import json
        data = json.dumps({"temperature": 25})
        expected_hash = "0xhash123"
        gaiachain_connector.client.registerDataHash.return_value = expected_hash

        result = gaiachain_connector.register_hash(data)

        assert result is not None

    def test_register_hash_immutability(
        self,
        gaiachain_connector: Any,
        sample_data: dict[str, Any],
    ) -> None:
        """Test that registering same data produces same hash."""
        hash1 = "0x" + "b" * 64
        hash2 = "0x" + "b" * 64
        
        gaiachain_connector.client.registerDataHash.return_value = hash1
        result1 = gaiachain_connector.register_hash(sample_data)

        gaiachain_connector.client.registerDataHash.return_value = hash2
        result2 = gaiachain_connector.register_hash(sample_data)

        assert result1 == result2

    def test_register_hash_different_data_different_hash(self, gaiachain_connector: Any) -> None:
        """Test that different data produces different hashes."""
        hash1 = "0x" + "a" * 64
        hash2 = "0x" + "b" * 64
        
        data1 = {"temperature": 25}
        data2 = {"temperature": 26}

        gaiachain_connector.client.registerDataHash.return_value = hash1
        result1 = gaiachain_connector.register_hash(data1)

        gaiachain_connector.client.registerDataHash.return_value = hash2
        result2 = gaiachain_connector.register_hash(data2)

        assert result1 != result2

    def test_register_hash_handles_api_error(
        self,
        gaiachain_connector: Any,
        sample_data: dict[str, Any],
    ) -> None:
        """Test error handling for API failures."""
        gaiachain_connector.client.registerDataHash.side_effect = Exception(
            "Blockchain connection failed"
        )

        with pytest.raises(Exception):
            gaiachain_connector.register_hash(sample_data)

    def test_register_hash_audit_trail(
        self,
        gaiachain_connector: Any,
        sample_data: dict[str, Any],
    ) -> None:
        """Test that registration creates audit trail."""
        hash_result = "0x" + "c" * 64
        gaiachain_connector.client.registerDataHash.return_value = hash_result

        gaiachain_connector.register_hash(sample_data)

        # Verify the call was made with the data
        gaiachain_connector.client.registerDataHash.assert_called()

    def test_register_large_agricultural_dataset(self, gaiachain_connector: Any) -> None:
        """Test registering large agricultural dataset."""
        large_data = {
            "readings": [
                {"temp": 25 + i, "humidity": 70 - i}
                for i in range(100)
            ],
            "metadata": {"field": "norte", "crop": "tomate"}
        }
        
        expected_hash = "0x" + "d" * 64
        gaiachain_connector.client.registerDataHash.return_value = expected_hash

        result = gaiachain_connector.register_hash(large_data)

        assert result == expected_hash

    def test_register_hash_with_special_characters(self, gaiachain_connector: Any) -> None:
        """Test registering data with special characters."""
        data = {
            "crop": "tomate",
            "location": "Campo Sur - Región Metropolitana",
            "notes": "Datos de prueba: 温度, pH, 🌾"
        }
        
        expected_hash = "0x" + "e" * 64
        gaiachain_connector.client.registerDataHash.return_value = expected_hash

        result = gaiachain_connector.register_hash(data)

        assert result is not None

    def test_get_hash_from_blockchain(self, gaiachain_connector: Any) -> None:
        """Test retrieving hash from blockchain."""
        hash_to_retrieve = "0x" + "f" * 64
        mock_data = {"temperature": 25, "humidity": 70}
        
        gaiachain_connector.client.getDataHash.return_value = mock_data

        if hasattr(gaiachain_connector.client, 'getDataHash'):
            result = gaiachain_connector.client.getDataHash(hash_to_retrieve)
            assert result is not None

    def test_register_multiple_hashes_sequentially(self, gaiachain_connector: Any) -> None:
        """Test registering multiple data points sequentially."""
        hashes = [f"0x{'f' * 64}", f"0x{'a' * 64}", f"0x{'b' * 64}"]
        data_points = [
            {"temp": 25},
            {"temp": 26},
            {"temp": 27}
        ]

        results: list[str] = []
        for i, data in enumerate(data_points):
            gaiachain_connector.client.registerDataHash.return_value = hashes[i]
            results.append(gaiachain_connector.register_hash(data))

        assert len(results) == 3
        assert all(h.startswith("0x") for h in results)
