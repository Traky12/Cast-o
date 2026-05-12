# -*- coding: utf-8 -*-
"""Materiales compuestos ecológicos: producción desde residuos agrícolas."""
from typing import Dict, Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/materiales", tags=["materiales"])

CONVERSION_RATE: Dict[str, float] = {
    "hemp_composite": 0.8,
    "pla_starch": 0.9,
    "cellulose_nano": 0.75,
    "magnesium_alloy": 0.95,
}


class ProducirBody(BaseModel):
    tipo: Literal["hemp_composite", "pla_starch", "cellulose_nano", "magnesium_alloy"]
    kg_materia_prima: float


class FabricarPiezaBody(BaseModel):
    producto: Literal["drone_wing", "drone_frame", "solar_panel", "soil_sensor"]
    kg_composite: float


@router.post("/producir")
async def producir(body: ProducirBody):
    """Simula producción: materia prima → material compuesto (tasa de conversión)."""
    rate = CONVERSION_RATE.get(body.tipo, 0.8)
    kg_producido = body.kg_materia_prima * rate
    return {
        "kg_producido": round(kg_producido, 2),
        "tipo": body.tipo,
        "propiedades": {
            "tensile_strength_mpa": 120,
            "density_kg_m3": 1200,
            "biodegradable": body.tipo in ("hemp_composite", "pla_starch"),
        },
    }


@router.post("/fabricar_pieza")
async def fabricar_pieza(body: FabricarPiezaBody):
    """Convierte kg de compuesto en piezas (ej: alas de drone)."""
    # 1 kg ≈ 2 alas, 1 carcasa, 2 m² panel, 4 sensores
    unidades = {
        "drone_wing": 2.0,
        "drone_frame": 1.0,
        "solar_panel": 2.0,
        "soil_sensor": 4.0,
    }
    por_kg = unidades.get(body.producto, 1.0)
    cantidad = int(body.kg_composite * por_kg)
    return {"producto": body.producto, "cantidad": cantidad, "kg_consumidos": body.kg_composite}
