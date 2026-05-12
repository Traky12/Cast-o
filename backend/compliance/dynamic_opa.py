# backend/compliance/dynamic_opa.py — Validación dinámica OPA por tipo de acción (EU AI Act Art.13)

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from backend.compliance.opa_client import OPAClient

logger = logging.getLogger(__name__)

_POLICY_MAP = {
    "deployment": "castuo/compliance",
    "self_healing": "castuo/compliance",
    "model_update": "castuo/compliance",
    "key_rotation": "castuo/compliance",
    "data_access": "castuo/compliance",
    "command": "castuo/compliance",
}

_NORMATIVE_MAP: Dict[str, List[str]] = {
    "deployment": ["ISO_27001:A.12.5.1", "NIS2:Art.23"],
    "self_healing": ["ISO_27001:A.16.1.1", "GDPR:Art.32"],
    "model_update": ["EU_AI_Act:Anexo_IV", "ISO_27001:A.10.1.1"],
    "key_rotation": ["ISO_27001:A.10.1.1", "GDPR:Art.32"],
    "data_access": ["GDPR:Art.15", "GDPR:Art.20"],
    "command": ["ISO_27001:A.18.1.4"],
}


class DynamicOPAValidator:
    """Valida acciones con OPA y añade metadatos de cumplimiento."""

    def __init__(self, opa_url: str | None = None) -> None:
        self.opa_client = OPAClient(opa_url=opa_url)
        self.logger = logging.getLogger(__name__)

    async def validate_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        action_type = action.get("type", "command")
        input_data = {
            "action": action,
            "context": context,
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": context.get("agent_name", "unknown"),
            },
        }
        policy = _POLICY_MAP.get(action_type, "castuo/compliance")
        result = await asyncio.to_thread(
            self.opa_client.evaluate_and_register,
            input_data,
            policy,
        )
        result["metadata"] = {
            "policy": policy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "normative_references": _NORMATIVE_MAP.get(action_type, ["ISO_27001:A.18.1.4"]),
        }
        return result
