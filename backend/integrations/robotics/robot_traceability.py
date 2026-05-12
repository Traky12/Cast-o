from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def build_robot_evolution_audit_payload(
    token_id: int,
    robot_id: str,
    state_or_checkpoint: Dict[str, Any],
    *,
    action: str = "robot_evolution_checkpoint",
    status: str = "registered",
) -> Dict[str, Any]:
    """
    Payload compatible con register_event_in_chain / POST /api/audit/register-event.
    Solo digest y metadatos mínimos: reduce superficie RGPD y coste de gas en detalles JSON.
    """
    canonical = json.dumps(
        {
            "robot_id": robot_id,
            "best_individual": state_or_checkpoint.get("best_individual"),
            "fitness": state_or_checkpoint.get("fitness"),
            "generations": state_or_checkpoint.get("generations"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "tokenId": int(token_id),
        "action": action,
        "status": status,
        "details": {
            "digest": f"sha256:{digest}",
            "robot_id": robot_id,
            "generations": state_or_checkpoint.get("generations"),
            "fitness": state_or_checkpoint.get("fitness"),
        },
        "compliance": {
            "module": "backend.integrations.robotics",
            "trace_policy": "minimize_payload",
        },
    }
