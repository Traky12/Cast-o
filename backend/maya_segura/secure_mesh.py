# backend/maya_segura/secure_mesh.py
# P2P torus encrypted — mesh seguro 7x7.

from __future__ import annotations

from typing import Any, Dict, List

try:
    from .maya_torus import torus_path_to_edges, TOTAL_NODES
    from .multi_crypto_engine import encrypt_multi
except ImportError:
    from maya_torus import torus_path_to_edges, TOTAL_NODES
    from multi_crypto_engine import encrypt_multi


def broadcast_along_path(data: Dict[str, Any], torus_path: str) -> Dict[str, Any]:
    """Broadcast encriptado a lo largo del path torus."""
    edges = torus_path_to_edges(torus_path or "0,0→1,0→2,1→3,2")
    payload = encrypt_multi(data)
    return {
        "encrypted": payload.hex(),
        "path_edges": len(edges),
        "nodes_traversed": len(edges) + 1,
        "status": "OK",
    }
