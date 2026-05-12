# -*- coding: utf-8 -*-
"""Workspace Sabionda: listado paginado de agentes (JSON) y rejilla de nodos (367 demo)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

_root = Path(__file__).resolve().parents[2]
_AGENTS_FILE = _root / "backend" / "data" / "sabionda_workspace_agents.json"
_TOTAL_DEMO_NODES = 367

router = APIRouter(prefix="/workspace", tags=["Sabionda Workspace"])


def _load_agents() -> list[dict[str, Any]]:
    if not _AGENTS_FILE.is_file():
        return []
    return json.loads(_AGENTS_FILE.read_text(encoding="utf-8"))


def _node_slice(page: int, per_page: int) -> tuple[list[dict[str, Any]], int]:
    page = max(1, page)
    per_page = min(max(1, per_page), 100)
    start_idx = (page - 1) * per_page
    items: list[dict[str, Any]] = []
    for j in range(per_page):
        i = start_idx + j + 1
        if i > _TOTAL_DEMO_NODES:
            break
        items.append(
            {
                "id": f"Nodo-{i:03d}",
                "location": "Extremadura",
                "security_status": "demo",
                "yield_pct": round(94.0 + (i % 9) * 0.4, 1),
            }
        )
    return items, _TOTAL_DEMO_NODES


@router.get("/agents")
async def workspace_agents_paginated(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    agents = _load_agents()
    total = len(agents)
    start = (max(1, page) - 1) * per_page
    chunk = agents[start : start + per_page]
    return {
        "data": chunk,
        "total": total,
        "page": page,
        "per_page": per_page,
        "kind": "agents",
    }


@router.get("/nodes")
async def workspace_nodes_paginated(
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
) -> dict[str, Any]:
    items, total = _node_slice(page, per_page)
    return {
        "data": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "kind": "nodes",
        "note": "Datos sintéticos para maquetación; sustituir por inventario real.",
    }


@router.get("/items")
async def workspace_items(
    kind: Literal["agents", "nodes"] = Query("agents"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    if kind == "nodes":
        items, total = _node_slice(page, per_page)
        return {"data": items, "total": total, "page": page, "per_page": per_page, "kind": "nodes"}
    agents = _load_agents()
    total = len(agents)
    start = (page - 1) * per_page
    return {
        "data": agents[start : start + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "kind": "agents",
    }


@router.websocket("/ws/agents")
async def workspace_agents_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            await websocket.send_json(
                {
                    "echo": raw,
                    "hint": "Sustituir por bus a métricas reales o SSE existente /agents/dashboard/stream",
                }
            )
    except WebSocketDisconnect:
        return
