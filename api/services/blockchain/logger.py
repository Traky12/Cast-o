from __future__ import annotations

from typing import Any

try:
    from services.blockchain.gaiachain_client import GaiaChainClient
except ModuleNotFoundError:  # pragma: no cover
    from api.services.blockchain.gaiachain_client import GaiaChainClient


class GaiaChainLogger:
    def __init__(self) -> None:
        self.client = None
        try:
            self.client = GaiaChainClient()  # type: ignore[call-arg]
        except Exception:
            self.client = None

    def log_content(self, payload: dict[str, Any]) -> str:
        if self.client is not None and hasattr(self.client, "log_ethical_action"):
            try:
                result = self.client.log_ethical_action(
                    action_type="educational_validation",
                    action_data=payload,
                )
                if isinstance(result, dict) and result.get("hash"):
                    return str(result["hash"])
                return str(result)
            except Exception:
                pass

        fallback_hash = payload.get("content_hash", "unknown")
        return f"gaiachain-sim-{fallback_hash[:16]}"