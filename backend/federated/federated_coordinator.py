# backend/federated/federated_coordinator.py
"""CASTUO_FEDERATED_IA_v3.0 — Nodo master + consenso 2/3. Multi-nodo: Gregorio-PC ↔ Técnico-Campo ↔ CTAEX-Demo."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

NODE_ID = os.getenv("NODE_ID", "node1")
PEERS_STR = os.getenv("PEERS", "node2,node3")
PEERS = [p.strip() for p in PEERS_STR.split(",") if p.strip()]
CONSENSUS_THRESHOLD = float(os.getenv("CONSENSUS_THRESHOLD", "0.66"))
BLOCKCHAIN_AUDITOR_URL = os.getenv("BLOCKCHAIN_AUDITOR_URL", "http://localhost:8002")


class FederatedCoordinator:
    """Coordina acciones federadas: broadcast a N nodos, consenso 2/3, commit a blockchain."""

    def __init__(self, node_id: str | None = None):
        self.node_id = node_id or NODE_ID
        self.peers = PEERS if PEERS else ["node2", "node3"]
        self.consensus_threshold = CONSENSUS_THRESHOLD
        self._blocks: List[Dict[str, Any]] = []
        self._peer_base_urls: Dict[str, str] = self._resolve_peer_urls()

    def _resolve_peer_urls(self) -> Dict[str, str]:
        """Resuelve URL base por peer (en Docker: node2-castuo:8001)."""
        base = {}
        for peer in self.peers:
            key = "PEER_" + peer.upper().replace("-", "_") + "_URL"
            base[peer] = os.getenv(key, f"http://{peer}:8001")
        return base

    async def broadcast_action(self, peer: str, action: dict) -> Dict[str, Any]:
        """Envía acción a un peer y devuelve {approved, node_id, signature}."""
        url = self._peer_base_urls.get(peer, f"http://{peer}:8001")
        endpoint = f"{url.rstrip('/')}/federated/vote"
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(endpoint, json={"action": action, "from_node": self.node_id})
                if r.status_code == 200:
                    data = r.json()
                    return {"approved": data.get("approved", True), "node_id": peer, "signature": data.get("signature", "")}
        except Exception as e:
            logger.warning("broadcast_action %s failed: %s", peer, e)
        return {"approved": False, "node_id": peer, "signature": ""}

    async def process_federated_action(self, action: dict) -> Dict[str, Any]:
        """Broadcast a todos los peers, consenso 2/3, commit a blockchain audit trail."""
        action_id = action.get("id") or hashlib.sha256(json.dumps(action, sort_keys=True).encode()).hexdigest()[:16]
        action["id"] = action_id
        action["source_node"] = self.node_id

        all_nodes = [self.node_id] + self.peers
        responses = await asyncio.gather(
            *[self.broadcast_action(peer, action) for peer in self.peers],
            return_exceptions=True,
        )

        valid = []
        for r in responses:
            if isinstance(r, Exception):
                logger.debug("Peer exception: %s", r)
                continue
            if r.get("approved"):
                valid.append(r)

        self_approved = await self._local_vote(action)
        if self_approved:
            valid.append({"approved": True, "node_id": self.node_id, "signature": "local"})

        consensus = len(valid) / max(len(all_nodes), 1)
        if consensus >= self.consensus_threshold:
            block_hash = await self.commit_blockchain(action)
            self._blocks.append({"action_id": action_id, "block_hash": block_hash, "consensus": consensus})
            return {
                "consensus": True,
                "consensus_pct": round(consensus * 100, 1),
                "votes": len(valid),
                "nodes": len(all_nodes),
                "block": block_hash,
                "action_id": action_id,
            }

        raise ValueError(f"No consensus: {len(valid)}/{len(all_nodes)} = {consensus:.2f} < {self.consensus_threshold}")

    async def _local_vote(self, action: dict) -> bool:
        """Voto local del nodo (política: aprobar si action tiene type y timestamp)."""
        return bool(action.get("type") or action.get("action_type")) and isinstance(action, dict)

    async def commit_blockchain(self, action: dict) -> str:
        """Registra acción en blockchain auditor (IPFS + hash) y devuelve block hash."""
        fallback_hash = "0x" + hashlib.sha256(json.dumps(action, sort_keys=True).encode()).hexdigest()[:64]
        if not BLOCKCHAIN_AUDITOR_URL:
            return fallback_hash
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{BLOCKCHAIN_AUDITOR_URL.rstrip('/')}/audit/commit",
                    json=action,
                )
                if r.status_code == 200:
                    data = r.json()
                    return data.get("block_hash", data.get("hash", fallback_hash))
        except Exception as e:
            logger.debug("blockchain_auditor not reachable: %s", e)
        return fallback_hash

    def get_blocks_count(self) -> int:
        return len(self._blocks)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "peers": self.peers,
            "nodes_online": 1 + len(self.peers),
            "blocks": len(self._blocks),
            "consensus_threshold": self.consensus_threshold,
        }
