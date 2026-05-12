# backend/maya_segura/maya_torus.py
# Topología honeycomb 7x7 + torus. GREGORIO J JIMÉNEZ BODES.

from __future__ import annotations

from typing import Any, Dict, List, Tuple

GRID_ROWS = 7
GRID_COLS = 7
TOTAL_NODES = GRID_ROWS * GRID_COLS


def torus_neighbors(row: int, col: int) -> List[Tuple[int, int]]:
    """Vecinos en torus (wrap-around)."""
    out: List[Tuple[int, int]] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r = (row + dr) % GRID_ROWS
            c = (col + dc) % GRID_COLS
            out.append((r, c))
    return out


def torus_path_to_edges(path: str) -> List[Tuple[int, int, int, int]]:
    """Convierte path '0,0→1,0→2,1→3,2' en lista de aristas (r1,c1,r2,c2)."""
    edges: List[Tuple[int, int, int, int]] = []
    parts = path.replace(" ", "").split("→")
    for i in range(len(parts) - 1):
        a = parts[i].split(",")
        b = parts[i + 1].split(",")
        if len(a) == 2 and len(b) == 2:
            r1, c1 = int(a[0]), int(a[1])
            r2, c2 = int(b[0]), int(b[1])
            edges.append((r1, c1, r2, c2))
    return edges


def node_id(row: int, col: int) -> int:
    return row * GRID_COLS + col


def get_torus_topology() -> Dict[str, Any]:
    """Topología 7x7 para dashboard."""
    nodes = []
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            nodes.append({"id": node_id(r, c), "row": r, "col": c, "status": "OK"})
    return {"grid": "7x7", "nodes": nodes, "total": TOTAL_NODES}
