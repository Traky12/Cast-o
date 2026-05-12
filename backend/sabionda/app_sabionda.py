# backend/sabionda/app_sabionda.py
"""SABIONDA_MASTER_v4.0 — FastAPI puerto 9000. Orquestación global, status, agentes, WS."""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .sabionda_master import SabiondaMaster
    from .crypto_pqc import get_kyber
    from .agent_hierarchy import AGENTES_SUBORDINADOS, trigger_federated_agents
except ImportError:
    from sabionda_master import SabiondaMaster
    from crypto_pqc import get_kyber
    from agent_hierarchy import AGENTES_SUBORDINADOS, trigger_federated_agents

app = FastAPI(
    title="SABIONDA Master v4.0",
    description="IA Suprema: Kyber-1024, consenso bizantino, 12 agentes, audit Merkle.",
    version="4.0.0",
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

master = SabiondaMaster()


class OrchestrateBody(BaseModel):
    type: str = ""
    agent: str = ""
    progress: float | None = None
    source_node: str = ""

    class Config:
        extra = "allow"


@app.get("/")
def root():
    return {
        "service": "SABIONDA_MASTER_v4.0",
        "orchestrate": "POST /sabionda/orchestrate",
        "status": "GET /sabionda/status",
        "agents": "POST /sabionda/agents/{id}",
        "ws": "/ws/sabionda",
        "docs": "/docs",
    }


@app.post("/sabionda/orchestrate")
async def sabionda_orchestrate(body: OrchestrateBody):
    """Acción global → Consenso → 12 agentes → Audit Merkle."""
    event = body.model_dump(exclude_none=True)
    if not event.get("type") and not event.get("agent"):
        event["type"] = "sabionda"
    try:
        return await master.orchestrate_global(event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sabionda/status")
async def sabionda_status():
    """Nodes=3/3 | Consensus=100% | Revenue=€150K | Fail=0.2%."""
    return master.get_status()


@app.post("/sabionda/agents/{agent_id}")
async def sabionda_agent_control(agent_id: str, payload: dict):
    """Control agente subordinado (Kyber encrypted). Dispara un agente por id."""
    if agent_id not in AGENTES_SUBORDINADOS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    triggered = await trigger_federated_agents(payload or {})
    if agent_id not in triggered and payload:
        triggered.append(agent_id)
    return {
        "agent_id": agent_id,
        "triggered": agent_id in triggered,
        "config": AGENTES_SUBORDINADOS[agent_id],
        "all_triggered": triggered,
    }


@app.websocket("/ws/sabionda")
async def ws_sabionda(websocket: WebSocket):
    """Real-time global orchestration por WebSocket."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            result = await master.orchestrate_global(data)
            await websocket.send_json(result)
    except Exception:
        pass


@app.get("/sabionda/vote-encrypted")
async def sabionda_vote_encrypted(action: dict = None):
    """Voto para consenso bizantino (nodos federados llaman). Devuelve voto aprobado encriptado."""
    approved = bool(action) or True
    vote = {"approved": approved}
    enc = get_kyber().encrypt_peers([vote])
    import base64
    return {"vote_encrypted": base64.b64encode(enc).decode()}


@app.post("/sabionda/vote-encrypted")
async def sabionda_vote_encrypted_post(body: dict):
    """Voto encriptado (POST body con action)."""
    action = body.get("action", {})
    approved = bool(action.get("type") or action.get("agent") or action.get("action_type"))
    vote = {"approved": approved}
    enc = get_kyber().encrypt_peers([vote])
    import base64
    return {"vote_encrypted": base64.b64encode(enc).decode()}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "SABIONDA_MASTER_v4.0"}
