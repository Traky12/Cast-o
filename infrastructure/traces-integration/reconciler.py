from __future__ import annotations

from typing import Any


def reconcile_trace_status(local_event: dict[str, Any], remote_event: dict[str, Any]) -> dict[str, Any]:
    local_hash = local_event.get("digest")
    remote_hash = remote_event.get("digest")
    matched = bool(local_hash and remote_hash and local_hash == remote_hash)
    return {
        "matched": matched,
        "local_digest": local_hash,
        "remote_digest": remote_hash,
        "status": "reconciled" if matched else "mismatch",
    }
