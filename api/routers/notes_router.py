from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.security.rbac import require_roles
from services.ai.semantic_memory import get_semantic_memory_service


router = APIRouter(prefix="/api/v1/notes", tags=["notes"])
semantic_memory = get_semantic_memory_service()


class NoteInput(BaseModel):
    id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    path: str = Field(..., min_length=1)


@router.post(
    "/extract",
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "usuario", "comercial", "alumno", "data_scientist"))],
)
async def extract_notes(notes: list[NoteInput]) -> dict[str, Any]:
    processed: list[dict[str, Any]] = []
    for note in notes:
        queued = semantic_memory.queue_note(
            note_id=note.id,
            content=note.content,
            metadata=note.metadata,
            path=note.path,
        )
        processed.append(
            {
                "id": queued["id"],
                "hash": queued["hash"],
                "status": "queued",
                "path": queued["path"],
            }
        )

    return {"count": len(processed), "notes": processed}