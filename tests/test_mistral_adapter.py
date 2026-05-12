# tests/test_mistral_adapter.py — Tests unitarios Mistral-CASTÚO Adapter
"""
Ejecutar desde raíz del repo: pytest tests/test_mistral_adapter.py -v
Requiere: pip install pytest requests pandas pyarrow cryptography
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Raíz del proyecto para imports
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Importar tras path (api como paquete o módulo según ejecución)
try:
    from api.mistral_castuo_adapter import (
        APIKeyManager,
        MistralAdapter,
        MistralAPIClient,
        MistralDataManager,
    )
except ImportError:
    sys.path.insert(0, str(ROOT / "api"))
    from mistral_castuo_adapter import (
        APIKeyManager,
        MistralAdapter,
        MistralAPIClient,
        MistralDataManager,
    )


# --- APIKeyManager ---


@patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key-123"}, clear=False)
def test_api_key_manager_plain_key():
    """APIKeyManager devuelve la key en claro si MISTRAL_API_KEY está definida."""
    manager = APIKeyManager(region="ES")
    key = manager.get_valid_key()
    assert key == "test-key-123"


def test_api_key_manager_missing_key():
    """APIKeyManager lanza ValueError si no hay key en env."""
    with patch.dict("os.environ", {}, clear=True):
        # Asegurar que no hay MISTRAL_*
        for k in list(os.environ.keys()):
            if "MISTRAL" in k:
                os.environ.pop(k, None)
    with patch.dict("os.environ", {"MISTRAL_ENCRYPTION_KEY_ES": "x"}, clear=False):
        try:
            orig = os.environ.get("MISTRAL_API_KEY"), os.environ.get("ENCRYPTED_MISTRAL_API_KEY")
            os.environ.pop("MISTRAL_API_KEY", None)
            os.environ.pop("ENCRYPTED_MISTRAL_API_KEY", None)
            manager = APIKeyManager(region="ES")
            with pytest.raises(ValueError, match="Falta ENCRYPTED_MISTRAL_API_KEY o MISTRAL_API_KEY"):
                manager.get_valid_key()
        finally:
            if orig[0] is not None:
                os.environ["MISTRAL_API_KEY"] = orig[0]
            if orig[1] is not None:
                os.environ["ENCRYPTED_MISTRAL_API_KEY"] = orig[1]


# --- MistralDataManager: extensión y PII ---


def test_load_dataset_extension_validation():
    """load_dataset rechaza extensiones no soportadas."""
    pytest.importorskip("pandas")
    manager = MistralDataManager(region="ES")
    with pytest.raises(ValueError, match="Extensión no soportada"):
        manager.load_dataset("/fake/path/data.txt")


def test_load_dataset_pii_columns_dropped(tmp_path):
    """Con drop_pii_columns=True se eliminan columnas PII."""
    pytest.importorskip("pandas")
    import pandas as pd

    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({
        "cultivo": ["maíz", "trigo"],
        "dni": ["12345678A", "87654321B"],
        "nombre": ["Ana", "Luis"],
        "humedad": [0.6, 0.5],
    })
    df.to_csv(csv_path, index=False)

    manager = MistralDataManager(region="ES")
    out = manager.load_dataset(str(csv_path), drop_pii_columns=True)
    assert "dni" not in out.columns
    assert "nombre" not in out.columns
    assert "cultivo" in out.columns
    assert "humedad" in out.columns


# --- MistralAPIClient: errores HTTP ---


def test_client_401_raises_value_error():
    """Cliente lanza ValueError con mensaje claro en 401."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.raise_for_status = MagicMock()

    with patch.object(MistralAPIClient, "_wait_rate_limit"):
        client = MistralAPIClient(api_key="fake", region="ES")
        client.session.post = MagicMock(return_value=mock_response)

        with pytest.raises(ValueError, match="API key inválida"):
            client.query(model="mistral-tiny", prompt="test")


def test_client_429_raises_value_error():
    """Cliente lanza ValueError en 429 (rate limit)."""
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "30"}

    with patch.object(MistralAPIClient, "_wait_rate_limit"):
        client = MistralAPIClient(api_key="fake", region="ES")
        client.session.post = MagicMock(return_value=mock_response)

        with pytest.raises(ValueError, match="Rate limit"):
            client.query(model="mistral-tiny", prompt="test")


def test_client_success_returns_json():
    """Cliente devuelve JSON de la API en 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hola"}, "index": 0}],
        "usage": {"total_tokens": 10},
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(MistralAPIClient, "_wait_rate_limit"):
        client = MistralAPIClient(api_key="fake", region="ES")
        client.session.post = MagicMock(return_value=mock_response)
        # No llamar _log_to_gaiachain para no depender de hashlib
        with patch.object(client, "_log_to_gaiachain"):
            result = client.query(model="mistral-tiny", prompt="test")
    assert result["choices"][0]["message"]["content"] == "Hola"


# --- MistralAdapter (facade) ---


@patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}, clear=False)
def test_adapter_query_success():
    """MistralAdapter.query devuelve resultado cuando la API responde OK."""
    adapter = MistralAdapter(region="ES")
    fake_response = {
        "choices": [{"message": {"content": "Análisis de rendimiento."}, "index": 0}],
        "usage": {"total_tokens": 20},
    }
    with patch.object(adapter._key_manager, "get_valid_key", return_value="fake-key"):
        with patch.object(MistralAPIClient, "query", return_value=fake_response):
            result = adapter.query(dataset_path=None, query="análisis rendimiento")
    assert result["choices"][0]["message"]["content"] == "Análisis de rendimiento."


@patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}, clear=False)
def test_adapter_health_equivalent():
    """MistralAdapter se puede instanciar (equivalente a /mistral/health OK)."""
    adapter = MistralAdapter(region="ES")
    assert adapter.region in ("ES", "EU", "GLOBAL")
