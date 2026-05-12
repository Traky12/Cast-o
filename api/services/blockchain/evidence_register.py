from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from services.blockchain.logger import GaiaChainLogger
except ModuleNotFoundError:  # pragma: no cover
    from api.services.blockchain.logger import GaiaChainLogger


class LocalEvidenceBackend:
    """Backend local para pruebas y entornos sin GaiaChain."""

    def __init__(self, network: str = "gaia_testnet") -> None:
        self.network = network

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        return {
            "txid": f"local-{digest[:16]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class EvidenceRegistrar:
    """Registro de evidencias con fallback local si GaiaChain no esta disponible."""

    def __init__(self, backend: Any | None = None) -> None:
        self.logger = GaiaChainLogger()
        self.backend = backend

    def compute_asset_hash(self, asset_path: str) -> str:
        return hashlib.sha256(Path(asset_path).read_bytes()).hexdigest()

    def register_asset(
        self,
        payload: dict[str, Any] | None = None,
        *,
        asset_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        content = dict(payload or {})
        metadata_payload = dict(metadata or {})
        if asset_path:
            content["asset"] = asset_path

        content["metadata"] = metadata_payload
        evidence_hash: str | None = None
        if asset_path:
            evidence_hash = self.compute_asset_hash(asset_path)
            content["hash"] = evidence_hash

        backend = self.backend
        if backend is None:
            backend = LocalEvidenceBackend()

        if hasattr(backend, "create"):
            result = backend.create(content)
            txid = str(result.get("txid", ""))
            timestamp = str(result.get("timestamp", datetime.now(timezone.utc).isoformat()))
        else:
            txid = self.logger.log_content(content)
            timestamp = datetime.now(timezone.utc).isoformat()

        response = {
            "txid": txid,
            "network": "gaia_testnet",
            "timestamp": timestamp,
        }
        if asset_path:
            response["asset"] = asset_path
        if metadata is not None:
            response["metadata"] = metadata_payload
        if evidence_hash:
            response["hash"] = evidence_hash
        return response
