from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


class SupportsEvidenceBackend(Protocol):
    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass
class LocalEvidenceBackend:
    """Fallback backend when OpenEvidence SDK is not configured."""

    network: str = "gaia_testnet"

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return {
            "txid": f"local-{digest[:16]}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


class EvidenceRegistrar:
    def __init__(self, backend: SupportsEvidenceBackend | None = None, network: str = "gaia_testnet") -> None:
        self.network = network
        self.backend: SupportsEvidenceBackend = backend or LocalEvidenceBackend(network=network)

    def compute_asset_hash(self, asset_path: str) -> str:
        file_path = Path(asset_path)
        digest = hashlib.sha256()
        with file_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def register_asset(self, asset_path: str, metadata: dict[str, Any]) -> dict[str, Any]:
        file_hash = self.compute_asset_hash(asset_path)
        payload = {
            "hash": file_hash,
            "asset": asset_path,
            "metadata": metadata,
            "network": self.network,
            "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        evidence = self.backend.create(payload)
        return {
            "txid": evidence.get("txid", ""),
            "timestamp": evidence.get("timestamp", payload["recorded_at"]),
            "metadata": metadata,
            "hash": file_hash,
            "asset": asset_path,
            "network": self.network,
        }
