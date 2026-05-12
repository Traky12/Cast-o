# -*- coding: utf-8 -*-
"""API para energía agrovoltaica (optimización, Modbus)."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/energia", tags=["energia"])


class OptimizarBody(BaseModel):
    pass  # energia_id from path


@router.post("/{energia_id}/optimizar")
async def optimizar_energia(energia_id: int, body: OptimizarBody):
    """Optimiza generación (paneles/geotermia según demanda)."""
    return {"status": "success", "energia_id": energia_id}


@router.get("/market/offers")
async def get_offers():
    """Ofertas de energía excedente (Odoo castu.energia.excedente)."""
    return {"offers": []}


@router.post("/market/sell")
async def sell_energy(
    granja_id: int,
    energia_kwh: float,
    tipo: str,
    precio_kwh: float = 0.15,
):
    """Publica oferta de venta de energía."""
    return {"status": "ok", "granja_id": granja_id, "energia_kwh": energia_kwh}
