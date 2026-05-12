# backend/sabionda/byzantine_consensus.py
"""Consenso bizantino: 3 nodos, votos encriptados Kyber-1024, umbral 2/3."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from .crypto_pqc import kyber1024_decrypt, get_kyber
except ImportError:
    from crypto_pqc import kyber1024_decrypt, get_kyber

CONSENSUS_THRESHOLD = float(os.getenv("CONSENSUS_THRESHOLD", "0.66"))
PEER_URLS = [
    os.getenv("SABIONDA_PEER1", "http://node1-castuo:8001"),
    os.getenv("SABIONDA_PEER2", "http://node2-castuo:8001"),
    os.getenv("SABIONDA_PEER3", "http://node3-castuo:8001"),
]


class ByzantineFaultTolerance:
    """Tolerancia a fallos bizantinos: N nodos, consenso >= threshold."""

    def __init__(self, threshold: float | None = None):
        self.threshold = threshold if threshold is not None else CONSENSUS_THRESHOLD
        self._nodes = [u for u in PEER_URLS if u]

    async def request_encrypted_vote(self, node_url: str, action: dict) -> bytes | None:
        """Solicita voto encriptado a un nodo. Fallback: /federated/vote (v3) si no hay /sabionda/vote-encrypted."""
        try:
            import base64
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{node_url.rstrip('/')}/sabionda/vote-encrypted",
                    json={"action": action},
                )
                if r.status_code == 200:
                    data = r.json()
                    enc = data.get("vote_encrypted")
                    if isinstance(enc, str):
                        return base64.b64decode(enc)
                    return enc
                if r.status_code == 404:
                    r2 = await client.post(f"{node_url.rstrip('/')}/federated/vote", json={"action": action, "from_node": "sabionda"})
                    if r2.status_code == 200 and r2.json().get("approved"):
                        return b"SIM:" + base64.b64encode(b'[{"approved":true}]')
        except Exception as e:
            logger.debug("request_encrypted_vote %s: %s", node_url, e)
        return None

    async def achieve_consensus(self, action: dict, nodes: List[str] | None = None) -> Dict[str, Any]:
        """
        Obtiene votos (opcionalmente encriptados), desencripta, cuenta approved.
        consensus_ok = (approved_count / total) >= threshold.
        """
        nodes = nodes or self._nodes
        if not nodes:
            return {"consensus": True, "approved": 1, "total": 1, "pct": 100.0}

        votes_encrypted: List[bytes | None] = []
        for node in nodes:
            v = await self.request_encrypted_vote(node, action)
            votes_encrypted.append(v)

        votes: List[Dict[str, Any]] = []
        for v in votes_encrypted:
            if v is None:
                votes.append({"approved": False})
                continue
            try:
                dec = kyber1024_decrypt(v)
                if isinstance(dec, dict):
                    votes.append(dec)
                elif isinstance(dec, list) and dec:
                    votes.append(dec[0] if isinstance(dec[0], dict) else {"approved": True})
                else:
                    votes.append({"approved": True})
            except Exception:
                votes.append({"approved": False})

        approved = sum(1 for v in votes if v.get("approved"))
        total = len(votes)
        pct = (approved / total * 100) if total else 0
        consensus = (approved / total) >= self.threshold if total else True

        return {
            "consensus": consensus,
            "approved": approved,
            "total": total,
            "pct": round(pct, 1),
            "votes": votes,
        }
