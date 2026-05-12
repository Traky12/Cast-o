from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from services.blockchain.evidence_register import LocalEvidenceBackend


class GraphChangeLogger:
    def __init__(self, network: str = "gaia_testnet") -> None:
        self.network = network
        self.backend = LocalEvidenceBackend(network=network)

    def log_change(self, change_type: str, data: dict[str, Any], actor: str) -> dict[str, Any]:
        serialized = json.dumps(data, sort_keys=True, ensure_ascii=False)
        data_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        payload = {
            "change_type": change_type,
            "data_hash": data_hash,
            "data": data,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        evidence = self.backend.create(payload)
        return {
            "txid": evidence["txid"],
            "timestamp": evidence["timestamp"],
            "data_hash": data_hash,
            "network": self.network,
        }