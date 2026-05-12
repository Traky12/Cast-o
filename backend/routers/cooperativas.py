# -*- coding: utf-8 -*-
"""Router Cooperativas — CAPA 3 Core Business (listado, parcelas, PAC 2040 eligibilidad)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..models.cooperativa import Cooperativa, Parcela

router = APIRouter(tags=["Cooperativas"])


class CooperativaOnboardingRequest(BaseModel):
    """Payload para onboarding de nueva cooperativa (POST /cooperativas)."""
    nombre: str = Field(..., min_length=1, description="Nombre de la cooperativa")
    hectareas: float = Field(..., ge=0.1, le=1000, description="Hectáreas totales")
    nif: str = Field(default="", description="NIF/CIF (opcional)")
    socios: int = Field(default=3, ge=1, description="Número de socios")
    cultivo: str = Field(default="mixto", description="Cultivo principal")


# MVP: 3 cooperativas integradas v1.7.1 (producción pending)
COOPERATIVAS_MVP = [
    Cooperativa(
        id=1,
        nombre="Sabionda Educa SAT",
        nif="B12345678",
        parcelas=[
            Parcela(id=1, hectares=2.5, cultivo="lechuga", kw_paneles=3000, pac2040_eligible=True),
        ],
        socios=5,
        capital_social=30000.0,
    ),
    Cooperativa(
        id=2,
        nombre="Cooperativa #2",
        nif="B87654321",
        parcelas=[
            Parcela(id=2, hectares=5.0, cultivo="vid", kw_paneles=5000, pac2040_eligible=True),
        ],
        socios=4,
        capital_social=50000.0,
    ),
    Cooperativa(
        id=3,
        nombre="Cooperativa #3",
        nif="B11223344",
        parcelas=[
            Parcela(id=3, hectares=3.0, cultivo="tomate", kw_paneles=3600, pac2040_eligible=True),
        ],
        socios=6,
        capital_social=30000.0,
    ),
]

_next_coop_id = 4


@router.post("/cooperativas", status_code=201)
async def onboard_cooperativa(body: CooperativaOnboardingRequest):
    """Onboarding nueva cooperativa. MVP: añade a lista en memoria (producción: persistir en BD)."""
    global _next_coop_id
    parcela = Parcela(
        id=_next_coop_id * 10,
        hectares=body.hectareas,
        cultivo=body.cultivo,
        kw_paneles=max(0, body.hectareas * 400),
        pac2040_eligible=True,
    )
    coop = Cooperativa(
        id=_next_coop_id,
        nombre=body.nombre,
        nif=body.nif or f"B{_next_coop_id:08d}",
        parcelas=[parcela],
        socios=body.socios,
        capital_social=30000.0,
    )
    COOPERATIVAS_MVP.append(coop)
    _next_coop_id += 1
    return {
        "id": coop.id,
        "nombre": coop.nombre,
        "hectareas": body.hectareas,
        "message": "Cooperativa registrada. GET /cooperativas para listado.",
    }


@router.get("/cooperativas", response_model=list[Cooperativa])
async def list_cooperativas():
    """Lista cooperativas (MVP: datos estáticos)."""
    return COOPERATIVAS_MVP


# ROI validado/proyectado por cooperativa (v1.7.1 — ARR proyectado, producción pending)
ROI_COOPERATIVAS = {
    1: {"energia_eur": 112_000, "cultivo_eur": 30_000, "pac2040_eur": 25_000, "total_eur": 352_000, "break_even_anios": 5.2},   # Sabionda 2.5ha lechuga
    2: {"energia_eur": 450_000, "cultivo_eur": 150_000, "pac2040_eur": 100_000, "total_eur": 700_000, "break_even_anios": 4.0},   # Coop #2 5ha vid
    3: {"energia_eur": 270_000, "cultivo_eur": 90_000, "pac2040_eur": 60_000, "total_eur": 420_000, "break_even_anios": 4.5},   # Coop #3 3ha tomate
}


@router.get("/cooperativas/{coop_id}")
async def get_cooperativa(coop_id: int):
    """Detalle cooperativa con ROI proyectado (3 cooperativas integradas v1.7.1)."""
    for c in COOPERATIVAS_MVP:
        if c.id == coop_id:
            total_ha = sum(p.hectares for p in c.parcelas)
            roi_data = ROI_COOPERATIVAS.get(coop_id)
            if roi_data:
                roi_anual = roi_data["total_eur"]
                desglose = {
                    "energia_eur": roi_data["energia_eur"],
                    "cultivo_eur": roi_data["cultivo_eur"],
                    "pac2040_eur": roi_data["pac2040_eur"],
                }
                break_even_anios = roi_data["break_even_anios"]
            else:
                energia = sum(p.kw_paneles * 45 for p in c.parcelas)
                cultivo = sum(p.hectares * 12000 for p in c.parcelas)
                pac = sum(25000 for p in c.parcelas if p.pac2040_eligible)
                roi_anual = c.roi_anual
                desglose = {"energia_eur": energia, "cultivo_eur": cultivo, "pac2040_eur": pac}
                break_even_anios = round(150000 / roi_anual, 1) if roi_anual else 0
            return {
                "id": c.id,
                "nombre": c.nombre,
                "nif": c.nif,
                "socios": c.socios,
                "capital_social": c.capital_social,
                "parcelas": [p.model_dump() for p in c.parcelas],
                "roi_anual_eur": roi_anual,
                "roi_desglose": desglose,
                "hectareas_totales": total_ha,
                "break_even_anios": break_even_anios,
                "pac2040_eligible": c.pac2040_eligible,
            }
    raise HTTPException(status_code=404, detail="Cooperativa no encontrada")


@router.get("/cooperativas/{coop_id}/parcelas", response_model=list[Parcela])
async def get_parcelas(coop_id: int):
    """Parcelas de una cooperativa."""
    for c in COOPERATIVAS_MVP:
        if c.id == coop_id:
            return c.parcelas
    raise HTTPException(status_code=404, detail="Cooperativa no encontrada")


@router.get("/pac2040/eligibilidad")
async def pac2040_check():
    """Criterios y ayuda máxima PAC 2040 (submedidas agrovoltaica)."""
    return {
        "submedidas": ["14.2.1 Agrovoltaica", "6.1 Jóvenes agricultores"],
        "ayuda_max": "€120.000/hectárea",
        "plazo": "31/12/2026",
        "elegibilidad": "Superficie mínima, cultivo compatible, kWp/ha dentro de ratio.",
    }
