from __future__ import annotations

from typing import Any


class ActivityPubServer:
    def __init__(self) -> None:
        self._impl = None
        try:
            from activitypub import ActivityPub  # type: ignore

            self._impl = ActivityPub()
        except Exception:
            self._impl = None

    def broadcast_educational_resource(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self._impl is not None and hasattr(self._impl, "broadcast"):
            result = self._impl.broadcast(payload)
            return {
                "status": "published",
                "mode": "activitypub",
                "result": result,
            }

        return {
            "status": "published",
            "mode": "simulated",
            "audience": payload.get("audience", "5-12"),
            "topic": payload.get("topic", "general"),
        }