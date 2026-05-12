# -*- coding: utf-8 -*-
"""Endpoint FastAPI para ejecutar el grafo LangGraph CASTÚO (Mistral + sellado + hooks HTTP)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/langgraph/castuo", tags=["LangGraph CASTÚO"])


class LangGraphRunBody(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


async def _run_langgraph_body(body: LangGraphRunBody) -> dict[str, Any]:
    try:
        from backend.integrations.langgraph_castuo.graph import run_castuo_langgraph
    except ImportError as e:
        raise HTTPException(
            status_code=501,
            detail="LangGraph no instalado. pip install -r backend/requirements.txt (langgraph, langchain-core).",
        ) from e
    return await run_castuo_langgraph(body.payload)


@router.post("/run")
async def run_langgraph(body: LangGraphRunBody) -> dict[str, Any]:
    return await _run_langgraph_body(body)


@router.post("/execute-graph")
async def execute_graph_alias(body: LangGraphRunBody) -> dict[str, Any]:
    """Alias compatible con proxies DNS tipo grafo.dominio (mismo cuerpo que /run)."""
    return await _run_langgraph_body(body)


@router.get("/health")
async def langgraph_health() -> dict[str, Any]:
    try:
        from backend.integrations.langgraph_castuo.graph import get_compiled_graph

        get_compiled_graph()
        return {"ok": True, "engine": "langgraph"}
    except ImportError:
        return {"ok": False, "engine": "missing_deps"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}
