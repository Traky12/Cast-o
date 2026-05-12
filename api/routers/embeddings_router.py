from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.security.rbac import require_roles
from services.ai.semantic_memory import get_semantic_memory_service
from services.blockchain.graph_change_logger import GraphChangeLogger


router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])
semantic_memory = get_semantic_memory_service()
graph_logger = GraphChangeLogger()


class EmbeddingRequest(BaseModel):
    id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    path: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class EmbeddingSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


@router.post(
    "/generate",
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "data_scientist", "devops"))],
)
async def generate_embedding(request: EmbeddingRequest) -> dict[str, Any]:
    note = semantic_memory.upsert_note(
        note_id=request.id,
        content=request.content,
        metadata=request.metadata,
        path=request.path,
    )
    semantic_memory.enrich_graph(note.note_id, limit=min(request.limit, 3))
    similar_notes = semantic_memory.search_similar_by_note(note.note_id, limit=request.limit)
    trace = graph_logger.log_change(
        "embedding_generated",
        {
            "note_id": note.note_id,
            "content_hash": note.content_hash,
            "similar_count": len(similar_notes),
        },
        actor="embedding_service",
    )

    return {
        "note_id": note.note_id,
        "embedding_dim": len(note.embedding),
        "vector_backend": semantic_memory.active_backend,
        "model": semantic_memory.model_name,
        "similar_notes": similar_notes,
        "blockchain_txid": trace["txid"],
    }


@router.post(
    "/search",
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "usuario", "auditor", "comercial", "alumno", "data_scientist"))],
)
async def search_embeddings(request: EmbeddingSearchRequest) -> dict[str, Any]:
    return {
        "query": request.query,
        "matches": semantic_memory.search_similar_by_text(request.query, limit=request.limit),
    }