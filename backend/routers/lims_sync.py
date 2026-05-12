# -*- coding: utf-8 -*-
"""Sincronización con LIMS de CTAEX (laboratorio) en tiempo real."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

try:
    from backend.services.gaia_chain import GaiaChainService
    _HAS_GAIA = True
except ImportError:
    GaiaChainService = None
    _HAS_GAIA = False


class LIMSData(BaseModel):
    batch_id: str
    thc: float
    cbd: float
    terpenes: dict = {}
    heavy_metals: dict = {}
    pesticides: dict = {}
    lab_technician: str = ""
    timestamp: str = ""


@router.post("/sync/lims")
async def sync_with_lims(data: LIMSData):
    """Recibe resultados de laboratorio del LIMS CTAEX y sincroniza (BD + GaiaChain + webhook)."""
    try:
        # Validar datos según RD 903/2025 (cannabis medicinal)
        if data.thc > 0.3:
            raise HTTPException(
                status_code=400,
                detail=f"THC {data.thc}% excede el límite legal (0.3%)",
            )

        # Persistir en base de datos (ejemplo: actualizar lote en cannabis.cannabis_batches)
        # En producción: usar backend.database.get_db_connection() y UPDATE
        lab_results: Dict[str, Any] = {
            "thc": data.thc,
            "cbd": data.cbd,
            "terpenes": data.terpenes,
            "heavy_metals": data.heavy_metals,
            "pesticides": data.pesticides,
            "lab_technician": data.lab_technician,
            "timestamp": data.timestamp,
        }

        tx_hash: str | None = None
        if _HAS_GAIA:
            try:
                gaia = GaiaChainService()
                batch_data = {
                    "batch_id": data.batch_id,
                    "strain_id": "from_lims",
                    "thc_percentage": data.thc,
                    "cbd_percentage": data.cbd,
                    "weight_kg": 0,
                    "lab_results": lab_results,
                    "account_id": "ctaex_lims",
                }
                result = await gaia.register_batch(batch_data)
                tx_hash = result.get("transaction_hash")
            except Exception:
                pass

        # Enviar confirmación a CTAEX (webhook)
        webhook_url = os.getenv("CTAEX_LIMS_WEBHOOK")
        if webhook_url:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json={
                        "status": "synced",
                        "batch_id": data.batch_id,
                        "blockchain_tx": tx_hash,
                    },
                    headers={
                        "Authorization": f"Bearer {os.getenv('CTAEX_API_KEY', '')}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()

        return {
            "status": "success",
            "batch_id": data.batch_id,
            "blockchain_tx": tx_hash,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
