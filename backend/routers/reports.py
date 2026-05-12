# -*- coding: utf-8 -*-
"""Informes de KPIs y reporting para el Consejo Asesor y monitoreo."""
from __future__ import annotations

from fastapi import APIRouter, Query

from backend.services.reporting import generate_kpi_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/kpis")
async def get_kpi_report(
    days: int = Query(30, ge=1, le=365, description="Número de días del período"),
):
    """Genera un informe de KPIs para el último período (tiempo certificación, yield, tasa certificación)."""
    return generate_kpi_report(days=days)


@router.get("/blockchain/pending")
async def get_blockchain_pending():
    """Estado de la cola de transacciones pendientes (modo degradado GaiaChain)."""
    try:
        from backend.services.gaia_chain import GaiaChainService
        svc = GaiaChainService()
        count = svc.get_pending_count()
        batches = svc.get_pending_batches()
        return {"pending_count": count, "batches": batches}
    except Exception as e:
        return {"pending_count": 0, "batches": [], "error": str(e)}


@router.post("/blockchain/sync_pending")
async def sync_blockchain_pending():
    """Sincroniza transacciones pendientes con GaiaChain (recuperación tras caída)."""
    try:
        from backend.services.gaia_chain import GaiaChainService
        svc = GaiaChainService()
        result = await svc.sync_pending_transactions()
        return result
    except Exception as e:
        return {"synced": 0, "failed": 0, "error": str(e)}
