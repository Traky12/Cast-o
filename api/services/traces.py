"""
Cliente TRACES (UE) + Hyperledger Fabric para trazabilidad oficial de lotes.

Usa eidas_signer para firmar los payloads antes de enviarlos.
Cuando TRACES_API_KEY no está configurada opera en modo simulado.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

_requests: Any | None = None
_requests_available = False
try:
    import requests as _requests

    _requests_available = True
except ImportError:  # pragma: no cover
    pass

try:
    from services.eidas import eidas_signer
except ModuleNotFoundError:  # pragma: no cover
    from api.services.eidas import eidas_signer


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
        """Envía el payload firmado a TRACES. Simulado si no hay API key."""
        if not self.api_key:
            return {
                "status": "SIMULATED",
                "message": "TRACES_API_KEY no configurada. Modo simulado.",
                "reference": payload.get("reference"),
                "hash": payload_hash,
            }

        if not _requests_available or _requests is None:  # pragma: no cover
            return {"status": "ERROR", "error": "requests no instalado"}

        try:
            response = _requests.post(
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
                print(f"⚠️ TRACES retornó {response.status_code}: {data}")
            return data
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error conectando a TRACES: {exc}")
            return {"status": "ERROR", "error": str(exc)}

    def _register_in_hyperledger(
        self,
        lote_id: str,
        payload_hash: str,
        traces_response: dict[str, Any],
    ) -> dict[str, Any]:
        """Registra el hash de trazabilidad en Hyperledger Fabric."""
        if not _requests_available or _requests is None:  # pragma: no cover
            return {"status": "SKIPPED", "reason": "requests no instalado"}

        try:
            response = _requests.post(
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
            print(f"⚠️ Hyperledger {response.status_code}: {response.text}")
            return {"status": "ERROR", "error": response.text}
        except Exception as exc:  # pragma: no cover
            print(f"❌ Error conectando a Hyperledger: {exc}")
            return {"status": "ERROR", "error": str(exc)}


# Singleton
traces_client = TRACESClient()
