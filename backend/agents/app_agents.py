# backend/agents/app_agents.py
"""FastAPI app CASTUO_IA_AGENTS_v2.0 — Anytype ↔ Agentes IA. Puerto 8001."""
from __future__ import annotations

import os

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

try:
    from .anytype_webhook import router as anytype_router, anytype_sync
except ImportError:
    from anytype_webhook import router as anytype_router, anytype_sync

app = FastAPI(
    title="CASTÚO IA Agents — Anytype ↔ FastAPI ↔ Agentes",
    description="Webhook Anytype JSON → AGENTE_AUDITOR, MONITOREO, VAULT, CAMPO. TRL8 + ISO 27001.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(anytype_router)


@app.get("/")
def root():
    return {
        "service": "CASTUO_IA_AGENTS_v2.0",
        "anytype_webhook": "/api/anytype",
        "anytype_webhook_alt": "/api/anytype/webhook",
        "metrics": "/api/anytype/metrics",
        "agents_metrics": "/api/agents/metrics",
        "ws": "/ws/anytype",
        "docs": "/docs",
    }


@app.websocket("/ws/anytype")
async def websocket_anytype(websocket: WebSocket):
    """WebSocket: recibe JSON objeto Anytype → procesa → devuelve result."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            result = await anytype_sync(data)
            await websocket.send_json(result)
    except Exception:
        pass


@app.get("/health")
def health():
    return {"status": "healthy", "agents": ["auditoria", "monitoreo", "vault", "campo"]}
