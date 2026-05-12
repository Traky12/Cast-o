# -*- coding: utf-8 -*-
"""
Router NFT — DynamicCropNFT growth updates desde IoT (3 cooperativas).
POST /nft/growth: actualiza growth stage en GaiaChain + IPFS.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/nft", tags=["NFT Dynamic Growth"])

# Último growth conocido por token (escalable 1-30 coops; 1-3 on-chain, 4+ en memoria hasta mint)
_nft_status: dict[int, dict] = {}
MAX_COOP_TOKEN = 30


class GrowthUpdate(BaseModel):
    token_id: int
    growth: float


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_update_script(token_id: int, growth_stage: int) -> tuple[str | None, str | None]:
    """Ejecuta update_dynamic_nft.py; devuelve (tx_hash_hex, ipfs_hash_placeholder)."""
    backend = _backend_root()
    script = backend / "scripts" / "update_dynamic_nft.py"
    if not script.is_file():
        return None, None
    growth_clamped = max(0, min(100, int(round(growth_stage))))
    try:
        out = subprocess.run(
            [sys.executable, str(script), str(token_id), str(growth_clamped)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(backend),
            env={**os.environ},
        )
        if out.returncode == 0 and out.stdout:
            tx_hash = out.stdout.strip()
            return tx_hash, "QmPlaceholderNoIPFS"
        return None, None
    except Exception:
        return None, None


@router.post("/growth")
async def update_nft_growth(request: GrowthUpdate):
    """Actualizar growth del Dynamic NFT desde IoT (escalable 1-30 coops; 1-3 on-chain, 4+ en memoria)."""
    token_id = request.token_id
    growth = request.growth
    if not (1 <= token_id <= MAX_COOP_TOKEN):
        raise HTTPException(status_code=400, detail=f"token_id debe ser 1-{MAX_COOP_TOKEN} (cooperativas)")
    if not (0 <= growth <= 100):
        raise HTTPException(status_code=400, detail="growth debe estar entre 0 y 100")

    now = datetime.utcnow().isoformat() + "Z"
    _nft_status[token_id] = {"growth": growth, "last_update": now}

    tx_hash, ipfs_hash = None, None
    if token_id <= 3:
        tx_hash, ipfs_hash = _run_update_script(token_id, growth)
        if tx_hash is None:
            raise HTTPException(
                status_code=503,
                detail="No se pudo actualizar on-chain (GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS, PRIVATE_KEY)",
            )
    return {
        "token_id": token_id,
        "growth": growth,
        "ipfs": ipfs_hash or "memory_only",
        "tx_hash": tx_hash or "memory_only",
        "last_update": now,
    }


@router.get("/status/{token_id}")
async def nft_status(token_id: int):
    """Estado de growth del Dynamic NFT (token 1-30 — cooperativas escalables)."""
    if not (1 <= token_id <= MAX_COOP_TOKEN):
        raise HTTPException(status_code=400, detail=f"token_id debe ser 1-{MAX_COOP_TOKEN}")
    s = _nft_status.get(token_id) or {"growth": 0.0, "last_update": None}
    return {"token_id": token_id, "growth": s["growth"], "last_update": s["last_update"], "status": "LIVE"}
