from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class BioProduct(BaseModel):
    product: str
    quantity: float
    unit: str
    biocoin: float
    market_value_eur: float
    co2_saved_kg: float
    vechain_tx: str


class MoneiTransaction(BaseModel):
    amount: float
    currency: str = "EUR"
    iban: str
    status: str
    vechain_tx: str
    carbon_credit: float


class SesionPsicologica(BaseModel):
    emocion: str
    respuesta: str
    vechain_tx: str
    accion: str = Field("breathing_4x4", description="Acción sugerida")
    biocoin_reward: float = 0.1


class CastuoEcosystem(BaseModel):
    bioeconomia: Optional[BioProduct] = None
    monei: Optional[MoneiTransaction] = None
    psicologo: Optional[SesionPsicologica] = None
    total_value_eur: float
    total_biocoin: float
    vechain_tx: str

