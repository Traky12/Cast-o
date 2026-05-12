# backend/compliance/traceability.py — Trazabilidad end-to-end (GaiaChain + IPFS opcional)

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_IPFS_AVAILABLE = False
try:
    import ipfshttpclient
    _IPFS_AVAILABLE = True
except ImportError:
    ipfshttpclient = None


class EndToEndTraceability:
    """Registro de eventos en IPFS (opcional) y GaiaChain."""

    def __init__(self, ipfs_host: str | None = None) -> None:
        self.ipfs_host = ipfs_host or os.getenv("IPFS_GATEWAY", "/dns/ipfs.infura.io/tcp/5001/https")
        self._client = None
        if _IPFS_AVAILABLE and ipfshttpclient:
            try:
                self._client = ipfshttpclient.connect(self.ipfs_host)
            except Exception as e:
                logger.debug("IPFS no disponible: %s", e)
        self.logger = logging.getLogger(__name__)

    def register_event(self, event: Dict[str, Any]) -> str:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        ipfs_hash = ""
        if self._client:
            try:
                res = self._client.add_json(event)
                ipfs_hash = str(res)
            except Exception as e:
                self.logger.debug("IPFS add_json: %s", e)
        gaiachain_record = {
            "ipfs_hash": ipfs_hash,
            "event_type": event.get("type", "event"),
            "timestamp": event["timestamp"],
            "normative_references": event.get("normative_references", []),
        }
        script = os.path.join(
            os.path.dirname(__file__), "..", "scripts", "register_gaiachain_event.py"
        )
        if os.path.isfile(script):
            try:
                subprocess.run(
                    [
                        os.environ.get("PYTHON", "python"),
                        script,
                        "--event_type", "traceability",
                        "--details", json.dumps(gaiachain_record),
                        "--norms", ",".join(gaiachain_record["normative_references"]) or "ISO_27001:A.18.1.4",
                    ],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
            except Exception as e:
                self.logger.debug("GaiaChain traceability: %s", e)
        return ipfs_hash or gaiachain_record["timestamp"]
