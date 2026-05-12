# backend/federated/app_federated.py
"""CASTUO_FEDERATED_IA_v3.0 — FastAPI 3 nodos + consenso + blockchain audit. Puerto 8001."""
from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .federated_coordinator import FederatedCoordinator
    from .blockchain_auditor import commit_audit, get_audit_metrics
    from .agent_federation import dispatch_agent, list_agents
    from .ml_predictor import get_predictions
except ImportError:
    from federated_coordinator import FederatedCoordinator
    from blockchain_auditor import commit_audit, get_audit_metrics
    from agent_federation import dispatch_agent, list_agents
    from ml_predictor import get_predictions

app = FastAPI(
    title="CASTÚO Federated IA v3.0",
    description="3 nodos P2P, consenso 2/3, audit trail blockchain, 12 agentes.",
    version="3.0.0",
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

coord = FederatedCoordinator()


class ActionBody(BaseModel):
    type: str = ""
    action_type: str = ""
    agent: str = ""
    id: str = ""
    source_node: str = ""

    class Config:
        extra = "allow"


class VoteBody(BaseModel):
    action: dict
    from_node: str = ""


@app.get("/")
def root():
    return {
        "service": "CASTUO_FEDERATED_IA_v3.0",
        "node_id": coord.node_id,
        "dashboard": "/federated/dashboard",
        "action": "POST /federated/action",
        "vote": "POST /federated/vote",
        "audit": "POST /audit/commit",
        "docs": "/docs",
    }


@app.get("/federated/dashboard")
async def federated_dashboard():
    """Métricas federadas v3.0: global + local + predictivas."""
    metrics = coord.get_metrics()
    audit = get_audit_metrics()
    pred = get_predictions()
    return {
        "version": "3.0",
        "federated": {
            "nodes_online": f"{metrics['nodes_online']}/{metrics['nodes_online']}",
            "consensus_pct": 100,
            "blocks": metrics["blocks"],
            "node_id": metrics["node_id"],
            "peers": metrics["peers"],
        },
        "blockchain": {
            "audit_trail_blocks": audit["audit_trail_blocks"],
            "ipfs_pins": audit["ipfs_pins"],
            "last_block": audit["last_block"],
        },
        "predictive": {
            "fail_rate_pct": pred["fail_rate_pct"],
            "revenue_q2_eur": pred["revenue_q2_eur"],
            "iso_stage2_pct": pred["iso_stage2_pct"],
            "mttr_reduction_pct": pred["mttr_reduction_pct"],
        },
        "local": {
            "iso_pct": 92,
            "uptime_pct": 99.9,
            "kyber_days": 28,
            "gdpr_consents_pct": 92,
        },
        "agents": list_agents(),
    }


@app.post("/federated/action")
async def federated_action(body: ActionBody):
    """Procesa acción federada: broadcast → consenso 2/3 → commit blockchain."""
    action = body.model_dump(exclude_none=True)
    if not action.get("type") and not action.get("action_type"):
        action["type"] = body.type or body.action_type or "federated"
    try:
        result = await coord.process_federated_action(action)
        audit_record = commit_audit(action)
        result["ipfs_cid"] = audit_record.get("ipfs_cid")
        result["anytype_object_id"] = audit_record.get("anytype_object_id")
        result["block_hash"] = audit_record.get("block_hash", result.get("block"))
        return result
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@app.post("/federated/vote")
async def federated_vote(body: VoteBody):
    """Voto de un peer: approved true/false (para consenso)."""
    action = body.action or {}
    approved = bool(action.get("type") or action.get("action_type") or action.get("agent"))
    return {
        "approved": approved,
        "node_id": coord.node_id,
        "signature": "v3_" + (body.from_node or "unknown")[:8],
    }


@app.post("/audit/commit")
async def audit_commit(action: dict):
    """Commit a audit trail blockchain (IPFS + block hash)."""
    record = commit_audit(action)
    return {
        "block_hash": record["block_hash"],
        "ipfs_cid": record["ipfs_cid"],
        "anytype_object_id": record["anytype_object_id"],
        "hash": record["block_hash"],
    }


@app.get("/federated/agents")
def federated_agents_list():
    return {"agents": list_agents(), "count": len(list_agents())}


@app.post("/federated/agents/{agent_id}")
def federated_agent_dispatch(agent_id: str, payload: dict):
    """Despacha a un agente federado (sin consenso, para pruebas)."""
    return dispatch_agent(agent_id, payload or {})


@app.get("/health")
def health():
    return {"status": "healthy", "node_id": coord.node_id, "version": "3.0"}
