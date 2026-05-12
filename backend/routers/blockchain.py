# -*- coding: utf-8 -*-
"""Blockchain privada: tokenización de activos y materiales (stub; prod: Hyperledger/Ethereum)."""
import hashlib
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/blockchain", tags=["blockchain"])


class TokenCreateBody(BaseModel):
    asset_id: int
    token_name: str
    total_supply: int


class TokenTransferBody(BaseModel):
    token_name: str
    new_owner_id: int
    amount: int


def _tx_id(prefix: str, *parts) -> str:
    data = f"{prefix}-" + "-".join(str(p) for p in parts)
    return hashlib.sha256(data.encode()).hexdigest()[:32]


@router.post("/token/create")
async def token_create(body: TokenCreateBody):
    """Crea token en blockchain privada (stub; en prod: Hyperledger Fabric)."""
    tx_id = _tx_id("create", body.asset_id, body.token_name, body.total_supply)
    return {"tx_id": tx_id, "status": "created"}


@router.post("/token/transfer")
async def token_transfer(body: TokenTransferBody):
    """Transfiere tokens (stub; en prod: chaincode transferToken)."""
    tx_id = _tx_id("transfer", body.token_name, body.new_owner_id, body.amount)
    return {"tx_id": tx_id, "status": "transferred"}


# --- Materiales: producción, venta, certificación (BioCoin Castúo) ---

class MaterialRegisterProductionBody(BaseModel):
    material_id: int
    kg_produced: float
    raw_material_kg: float = 0.0
    energy_kwh: float = 0.0


class MaterialRegisterSaleBody(BaseModel):
    sale_id: int
    partner_id: int
    lines: List[dict]  # [{"material_id": int, "kg": float}, ...]


class MaterialRegisterCertificationBody(BaseModel):
    certification_id: int
    certification_body: str
    date: str
    validity: str = ""


class MaterialRegisterInvoiceBody(BaseModel):
    invoice_id: int
    partner_id: int
    amount_total: float
    date: str


@router.post("/material/register_invoice")
async def material_register_invoice(body: MaterialRegisterInvoiceBody):
    """Registra factura en blockchain (trazabilidad BioCoin Castúo)."""
    tx_id = _tx_id("inv", body.invoice_id, body.partner_id, body.amount_total)
    return {"tx_id": tx_id, "status": "registered"}


@router.post("/material/register_production")
async def material_register_production(body: MaterialRegisterProductionBody):
    """Registra lote de producción (stub; en prod: MaterialCertification.sol)."""
    tx_id = _tx_id("prod", body.material_id, body.kg_produced, body.raw_material_kg)
    return {"tx_id": tx_id, "status": "registered"}


@router.post("/material/register_sale")
async def material_register_sale(body: MaterialRegisterSaleBody):
    """Registra venta (stub; en prod: registerSale en contrato)."""
    tx_id = _tx_id("sale", body.sale_id, body.partner_id, len(body.lines))
    return {"tx_id": tx_id, "status": "registered"}


@router.post("/material/register_certification")
async def material_register_certification(body: MaterialRegisterCertificationBody):
    """Registra certificación ecológica (stub; en prod: registerCertification)."""
    tx_id = _tx_id("cert", body.certification_id, body.certification_body, body.date)
    return {"tx_id": tx_id, "status": "registered"}


# --- Créditos de carbono (CarbonCredits.sol) ---

class CarbonRegisterCreditBody(BaseModel):
    material_id: int
    kg_produced: float
    savings_kg_co2: float
    date: str


class CarbonSellCreditBody(BaseModel):
    credit_id: int
    buyer_id: int
    price_per_ton: float


@router.post("/carbon/register_credit")
async def carbon_register_credit(body: CarbonRegisterCreditBody):
    """Registra crédito de carbono (stub; en prod: CarbonCredits.sol)."""
    tx_id = _tx_id("co2", body.material_id, body.kg_produced, body.savings_kg_co2)
    return {"tx_id": tx_id, "status": "registered"}


@router.post("/carbon/sell_credit")
async def carbon_sell_credit(body: CarbonSellCreditBody):
    """Vende crédito de carbono (stub)."""
    tx_id = _tx_id("co2sell", body.credit_id, body.buyer_id, body.price_per_ton)
    return {"tx_id": tx_id, "status": "sold"}
