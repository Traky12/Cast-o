# -*- coding: utf-8 -*-
"""Ingesta de observaciones agrovoltaicas de campo → Postgres (irradiancia, sombra, transpiración)."""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from backend.services import agrovoltaic_field_store as av_store

router = APIRouter(prefix="/agrovoltaic", tags=["agrovoltaic-field"])


def _allowed_keys() -> List[str]:
    raw = os.getenv("HYDROPONICS_SAAS_API_KEYS", "").strip()
    if raw:
        return [x.strip() for x in raw.split(",") if x.strip()]
    k = os.getenv("N8N_API_KEY", "").strip()
    if k:
        return [k]
    return ["default_n8n_key_123"]


def _require_x_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-KEY")) -> str:
    if not x_api_key or x_api_key not in set(_allowed_keys()):
        raise HTTPException(status_code=401, detail="X-API-KEY inválida o ausente")
    return x_api_key


class ObservationIn(BaseModel):
    zone_id: str = Field(..., min_length=1)
    irradiance_wm2: float = Field(..., ge=0)
    shading_wm2: float = Field(..., ge=0)
    transpiration_mmol_m2_s: Optional[float] = None
    source: str = "edge"


@router.post("/observations")
async def post_observation(body: ObservationIn, _: str = Depends(_require_x_api_key)):
    row = av_store.insert_observation(
        body.zone_id,
        body.irradiance_wm2,
        body.shading_wm2,
        body.transpiration_mmol_m2_s,
        body.source,
    )
    if row is None:
        raise HTTPException(status_code=503, detail="PostgreSQL no disponible o tabla agrovoltaic_observations no creada")
    return {"status": "ok", **row}


@router.get("/zones/{zone_id}/shadow-factor")
async def get_shadow_factor(zone_id: str, _: str = Depends(_require_x_api_key)):
    sf = av_store.latest_shadow_factor(zone_id)
    if sf is None:
        raise HTTPException(status_code=404, detail="Sin datos agrovoltaicos para la zona")
    return {"zone_id": zone_id, "shadow_factor": sf}
