from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security.rbac import require_roles
from services.ai.semantic_memory import get_semantic_memory_service
from services.blockchain.graph_change_logger import GraphChangeLogger


router = APIRouter(tags=["graph"])
semantic_memory = get_semantic_memory_service()
graph_logger = GraphChangeLogger()


class GraphUpdateRequest(BaseModel):
    note_id: str = Field(..., min_length=1)
    limit: int = Field(default=3, ge=1, le=20)


@router.get(
    "/api/v1/graph",
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "usuario", "auditor", "comercial", "alumno", "data_scientist"))],
)
async def get_graph() -> dict[str, Any]:
    return semantic_memory.build_graph_projection(xr=False)


@router.get(
    "/api/v1/graph/xr",
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "usuario", "auditor", "comercial", "alumno", "data_scientist"))],
)
async def get_graph_xr() -> dict[str, Any]:
    return semantic_memory.build_graph_projection(xr=True)


@router.post(
    "/api/v1/neo4j/update",
    dependencies=[Depends(require_roles("admin_general", "administrador", "tecnico", "devops", "data_scientist"))],
)
async def update_graph(request: GraphUpdateRequest) -> dict[str, Any]:
    if request.note_id not in semantic_memory.notes:
        raise HTTPException(status_code=404, detail="Note not found in semantic memory")

    edges = semantic_memory.enrich_graph(request.note_id, limit=request.limit)
    trace = graph_logger.log_change(
        "graph_update",
        {
            "note_id": request.note_id,
            "relationships_added": len(edges),
            "source": "semantic_memory",
        },
        actor="system",
    )
    return {
        "status": "updated",
        "note_id": request.note_id,
        "relationships_added": len(edges),
        "blockchain_txid": trace["txid"],
    }