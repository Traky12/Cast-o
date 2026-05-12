# -*- coding: utf-8 -*-
"""API para riego (válvulas, ozono, pH/EC)."""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/riego", tags=["riego"])


class ActivarBody(BaseModel):
    duracion: Optional[int] = 30


class AjustarBody(BaseModel):
    ph: Optional[float] = None
    ec: Optional[float] = None


@router.post("/{riego_id}/activar")
async def activar_riego(riego_id: int, body: ActivarBody):
    """Activa riego (GPIO/PLC en producción)."""
    return {"status": "success", "riego_id": riego_id, "duracion": body.duracion}


@router.post("/{riego_id}/ajustar")
async def ajustar_agua(riego_id: int, body: AjustarBody):
    """Ajusta pH/EC (dosificadores en producción)."""
    return {"status": "success", "ph": body.ph, "ec": body.ec}
