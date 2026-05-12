from __future__ import annotations

import hashlib
import json
from typing import Any


class GaiaChainClient:
    """Cliente GaiaChain con fallback local para entornos sin nodo real."""

    def log_ethical_action(self, action_type: str, action_data: dict[str, Any]) -> dict[str, str]:
        canonical = json.dumps({"action_type": action_type, "action_data": action_data}, sort_keys=True)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return {"hash": f"gaiachain-sim-{digest[:24]}"}
