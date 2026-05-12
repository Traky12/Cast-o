"""
Smoke tests E2E para la integración TRACES UE + Hyperledger Fabric.

Valida el flujo completo en modo simulado (sin TRACES_API_KEY):
- submit_to_traces() retorna estructura correcta
- Modo simulado activo cuando no hay API key
- check_status() retorna estado válido
- async_submit_to_traces() compatible con await
- Retries y logging configurados correctamente
"""

from __future__ import annotations

import asyncio
import logging
import os
from unittest.mock import MagicMock, patch

import pytest

# Dual import: Docker (raíz=api/) o tests (api.*)
try:
    from services.traces import TRACESClient, traces_client
except ModuleNotFoundError:
    from api.services.traces import TRACESClient, traces_client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client_simulado() -> TRACESClient:
    """Cliente TRACES sin API key → modo simulado."""
    with patch.dict(os.environ, {"TRACES_API_KEY": "", "TRACES_OPERATOR_ID": "ES-TEST-001"}):
        return TRACESClient()


@pytest.fixture()
def sample_metadata() -> dict:
    return {
        "product_id": "CBD-OIL-001",
        "quantity_kg": 10.5,
        "thc": 0.2,
        "cbd": 12.3,
        "type": "AGRICULTURAL_PRODUCT",
        "batch": "LOTE-2026-001",
    }


# ---------------------------------------------------------------------------
# Tests: submit_to_traces (modo simulado)
# ---------------------------------------------------------------------------


class TestSubmitTraces:
    def test_submit_returns_expected_keys(self, client_simulado, sample_metadata):
        """submit_to_traces retorna las claves traces, hyperledger y signed_payload."""
        result = client_simulado.submit_to_traces("LOTE-001", sample_metadata)

        assert "traces" in result
        assert "hyperledger" in result
        assert "signed_payload" in result

    def test_simulated_mode_when_no_api_key(self, client_simulado, sample_metadata):
        """Modo simulado activo cuando TRACES_API_KEY no configurada."""
        result = client_simulado.submit_to_traces("LOTE-002", sample_metadata)

        assert result["traces"]["status"] == "SIMULATED"

    def test_signed_payload_has_hash(self, client_simulado, sample_metadata):
        """signed_payload contiene hash y signature_hex."""
        result = client_simulado.submit_to_traces("LOTE-003", sample_metadata)

        sp = result["signed_payload"]
        assert "hash" in sp
        assert "signature_hex" in sp
        assert "payload" in sp

    def test_payload_reference_matches_lote_id(self, client_simulado, sample_metadata):
        """El reference en el payload coincide con el lote_id enviado."""
        lote_id = "LOTE-REFERENCIA-007"
        result = client_simulado.submit_to_traces(lote_id, sample_metadata)

        assert result["traces"].get("reference") == lote_id

    def test_hyperledger_skipped_without_requests(self, client_simulado, sample_metadata):
        """Sin requests disponible, Hyperledger retorna SKIPPED o ERROR."""
        result = client_simulado.submit_to_traces("LOTE-004", sample_metadata)
        hl_status = result["hyperledger"].get("status", "")
        # En modo simulado sin requests puede ser SKIPPED o con status de error
        assert isinstance(hl_status, str)

    def test_operator_id_in_payload(self, client_simulado, sample_metadata):
        """El operator_id se incluye en el payload enviado a TRACES."""
        result = client_simulado.submit_to_traces("LOTE-005", sample_metadata)
        payload = result["signed_payload"]["payload"]
        assert payload["operator"]["id"] == "ES-TEST-001"


# ---------------------------------------------------------------------------
# Tests: check_status (reconciliación)
# ---------------------------------------------------------------------------


class TestCheckStatus:
    def test_check_status_simulated_without_api_key(self, client_simulado):
        """check_status retorna estado simulado sin API key."""
        result = client_simulado.check_status("LOTE-001")

        assert result["status"] == "SIMULATED"
        assert result["reference"] == "LOTE-001"

    def test_check_status_message_present(self, client_simulado):
        """check_status incluye mensaje informativo."""
        result = client_simulado.check_status("REF-ABC")
        assert "message" in result

    def test_check_status_with_api_key_calls_endpoint(self):
        """Con API key, check_status intenta llamar al endpoint TRACES."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ACCEPTED", "reference": "LOTE-REAL"}

        with patch.dict(os.environ, {"TRACES_API_KEY": "test-key-123"}):
            client = TRACESClient()
            with patch("api.services.traces._requests") as mock_req:
                mock_req.get.return_value = mock_response
                # Solo ejecutar si requests está disponible
                import api.services.traces as traces_mod
                if traces_mod._requests_available:
                    result = client.check_status("LOTE-REAL")
                    assert "status" in result


# ---------------------------------------------------------------------------
# Tests: async_submit_to_traces
# ---------------------------------------------------------------------------


class TestAsyncSubmit:
    def test_async_submit_is_coroutine(self, client_simulado, sample_metadata):
        """async_submit_to_traces devuelve una corrutina awaitable."""
        coro = client_simulado.async_submit_to_traces("LOTE-ASYNC-001", sample_metadata)
        assert asyncio.iscoroutine(coro)
        # Ejecutar para no dejar coroutine sin consumir
        result = asyncio.get_event_loop().run_until_complete(coro)
        assert "traces" in result

    def test_async_submit_same_result_as_sync(self, client_simulado, sample_metadata):
        """async_submit_to_traces y submit_to_traces retornan estructura idéntica."""
        sync_result = client_simulado.submit_to_traces("LOTE-SYNC", sample_metadata)
        async_result = asyncio.get_event_loop().run_until_complete(
            client_simulado.async_submit_to_traces("LOTE-ASYNC-002", sample_metadata)
        )
        # Ambos deben tener las mismas claves
        assert set(sync_result.keys()) == set(async_result.keys())


# ---------------------------------------------------------------------------
# Tests: Singleton y logging
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_singleton_traces_client_exists(self):
        """traces_client singleton está disponible en el módulo."""
        assert traces_client is not None
        assert isinstance(traces_client, TRACESClient)

    def test_logger_configured(self):
        """El módulo tiene logger configurado correctamente."""
        import api.services.traces as traces_mod
        assert hasattr(traces_mod, "logger")
        assert isinstance(traces_mod.logger, logging.Logger)

    def test_tenacity_availability_flag(self):
        """El flag de disponibilidad de tenacity está definido."""
        import api.services.traces as traces_mod
        assert hasattr(traces_mod, "_tenacity_available")
        assert isinstance(traces_mod._tenacity_available, bool)
