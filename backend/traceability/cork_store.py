"""Almacén en memoria ordenado por tiempo; sustituir por QuestDB/PostgreSQL en despliegue."""
from __future__ import annotations

import threading
from collections.abc import Sequence
from uuid import UUID

from backend.traceability.cork_models import CorkExtractionEventCreate, CorkExtractionEventStored

_lock = threading.Lock()
_events: list[CorkExtractionEventStored] = []


def append_event(payload: CorkExtractionEventCreate) -> CorkExtractionEventStored:
    row = CorkExtractionEventStored(**payload.model_dump(by_alias=True))
    with _lock:
        _events.append(row)
    return row


def list_events(limit: int = 500) -> Sequence[CorkExtractionEventStored]:
    with _lock:
        return tuple(_events[-limit:])


def by_tree(tree_uuid: UUID) -> list[CorkExtractionEventStored]:
    with _lock:
        return [e for e in _events if e.tree_uuid == tree_uuid]


def count_events() -> int:
    with _lock:
        return len(_events)
