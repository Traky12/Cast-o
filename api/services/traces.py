"""
Cliente TRACES (UE) + Hyperledger Fabric para trazabilidad oficial de lotes.

Usa eidas_signer para firmar los payloads antes de enviarlos.
Cuando TRACES_API_KEY no está configurada opera en modo simulado.

Mejoras v3.1.2:
- Retries con tenacity (3 intentos, backoff exponencial 2-10s)
- Logging estructurado (reemplaza print)
- check_status() para reconciliación
- async_submit_to_traces() wrapper asíncrono
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

_requests: Any | None = None
_requests_available = False
try:
    import requests as _requests

    _requests_available = True
except ImportError:  # pragma: no cover
    pass

# Tenacity para retries
_tenacity_available = False
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )
    _tenacity_available = True
except ImportError:  # pragma: no cover
    pass

try:
    from services.eidas import eidas_signer
except ModuleNotFoundError:  # pragma: no cover
    from api.services.eidas import eidas_signer


def _retry_decorator():
    """Devuelve decorador de retry si tenacity está disponible, si no identity."""
    if _tenacity_available:
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
    # Sin tenacity: decorador identidad
    def _identity(fn):  # pragma: no cover
        return fn
    return _identity  # pragma: no cover


class TRACESClient:
    """Cliente para el sistema TRACES de la UE + Hyperledger Fabric."""

    def __init__(self) -> None:
        self.api_url = os.getenv(
            "TRACES_API_URL",
            "https://webgate.ec.europa.eu/traces/api",
        )
        self.api_key = os.getenv("TRACES_API_KEY", "")
        self.hyperledger_url = os.getenv(
            "HYPERLEDGER_URL",
            "http://hyperledger.castuo-system.cloud:7050",
        )
        self.hyperledger_channel = os.getenv(
            "HYPERLEDGER_CHANNEL", "castuo-channel"
        )
        self.hyperledger_cc = os.getenv(
            "HYPERLEDGER_CHAINCODE", "traces-cc"
        )
        self.operator_id = os.getenv("TRACES_OPERATOR_ID", "ES-CASTUO-001")

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def submit_to_traces(self, lote_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Envía datos a TRACES UE y los registra en Hyperledger.

        Retorna un dict con claves 'traces', 'hyperledger' y 'signed_payload'.
        """
        traces_payload = self._build_traces_payload(lote_id, metadata)

        # Firmar con eIDAS
        signed = eidas_signer.sign_payload(traces_payload)
        payload_hash = signed["hash"]
        signature_hex = signed["signature_hex"]

        # Enviar a TRACES (real o simulado)
        traces_response = self._send_to_traces(
            traces_payload, signature_hex, payload_hash
        )

        # Registrar en Hyperledger
        hyperledger_tx = self._register_in_hyperledger(
            lote_id, payload_hash, traces_response
        )

        return {
            "traces": traces_response,
            "hyperledger": hyperledger_tx,
            "signed_payload": {
                "payload": traces_payload,
                "signature_hex": signature_hex,
                "hash": payload_hash,
                "mode": signed.get("mode", "simulated"),
            },
        }

    async def async_submit_to_traces(
        self, lote_id: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Wrapper asíncrono sobre submit_to_traces para uso futuro en async context.

        Ejecuta la lógica síncrona directamente; el wrapper facilita
        migración incremental a asyncio sin romper la API existente.
        """
        return self.submit_to_traces(lote_id, metadata)

    def check_status(self, reference: str) -> dict[str, Any]:
        """Consulta el estado de una sumisión TRACES por referencia (reconciliación).

        En modo simulado retorna estado simulado.
        Con API key activa consulta el endpoint real de TRACES.
        """
        if not self.api_key:
            logger.debug("check_status: modo simulado para reference=%s", reference)
            return {
                "status": "SIMULATED",
                "reference": reference,
                "message": "TRACES_API_KEY no configurada. Consulta simulada.",
            }

        if not _requests_available or _requests is None:  # pragma: no cover
            return {"status": "ERROR", "reference": reference, "error": "requests no instalado"}

        try:
            response = _requests.get(
                f"{self.api_url}/submissions/{reference}",
                headers={"X-API-KEY": self.api_key},
                timeout=10,
            )
            data = response.json()
            if response.status_code != 200:
                logger.warning(
                    "check_status TRACES retornó %s para reference=%s: %s",
                    response.status_code, reference, data,
                )
            return data
        except Exception as exc:  # pragma: no cover
            logger.error("check_status error conectando a TRACES: %s", exc)
            return {"status": "ERROR", "reference": reference, "error": str(exc)}

    # ------------------------------------------------------------------
    # Implementaciones internas
    # ------------------------------------------------------------------

    def _build_traces_payload(self, lote_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "reference": lote_id,
            "type": metadata.get("type", "AGRICULTURAL_PRODUCT"),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "operator": {
                "id": self.operator_id,
                "name": "CASTÚO-SYSTEM™",
            },
            "products": [
                {
                    "id": metadata.get("product_id", "DEFAULT"),
                    "quantity": metadata.get("quantity_kg", 0),
                    "thc": metadata.get("thc", 0),
                    "cbd": metadata.get("cbd", 0),
                }
            ],
            "metadata": metadata,
        }

    def _send_to_traces(
        self, payload: dict[str, Any], signature_hex: str, payload_hash: str
    ) -> dict[str, Any]:
        """Envía el payload firmado a TRACES. Simulado si no hay API key.

        Con tenacity: 3 reintentos, backoff exponencial 2-10s.
        """
        if not self.api_key:
            return {
                "status": "SIMULATED",
                "message": "TRACES_API_KEY no configurada. Modo simulado.",
                "reference": payload.get("reference"),
                "hash": payload_hash,
            }

        if not _requests_available or _requests is None:  # pragma: no cover
            return {"status": "ERROR", "error": "requests no instalado"}

        @_retry_decorator()
        def _do_send() -> dict[str, Any]:
            response = _requests.post(  # type: ignore[union-attr]
                f"{self.api_url}/submissions",
                json={
                    "payload": payload,
                    "signature": signature_hex,
                    "hash": payload_hash,
                },
                headers={"X-API-KEY": self.api_key},
                timeout=10,
            )
            data = response.json()
            if response.status_code != 200:
                logger.warning(
                    "TRACES retornó %s: %s", response.status_code, data
                )
            return data

        try:
            return _do_send()
        except Exception as exc:  # pragma: no cover
            logger.error("Error conectando a TRACES tras reintentos: %s", exc)
            return {"status": "ERROR", "error": str(exc)}

    def _register_in_hyperledger(
        self,
        lote_id: str,
        payload_hash: str,
        traces_response: dict[str, Any],
    ) -> dict[str, Any]:
        """Registra el hash de trazabilidad en Hyperledger Fabric.

        Con tenacity: 3 reintentos, backoff exponencial 2-10s.
        """
        if not _requests_available or _requests is None:  # pragma: no cover
            return {"status": "SKIPPED", "reason": "requests no instalado"}

        @_retry_decorator()
        def _do_register() -> dict[str, Any]:
            response = _requests.post(  # type: ignore[union-attr]
                f"{self.hyperledger_url}/channels/{self.hyperledger_channel}"
                f"/chaincodes/{self.hyperledger_cc}",
                json={
                    "fcn": "registerTrace",
                    "args": [lote_id, payload_hash, json.dumps(traces_response)],
                },
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "Hyperledger %s: %s", response.status_code, response.text
            )
            return {"status": "ERROR", "error": response.text}

        try:
            return _do_register()
        except Exception as exc:  # pragma: no cover
            logger.error("Error conectando a Hyperledger tras reintentos: %s", exc)
            return {"status": "ERROR", "error": str(exc)}


# Singleton
traces_client = TRACESClient()
