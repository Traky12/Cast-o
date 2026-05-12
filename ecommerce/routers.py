# -*- coding: utf-8 -*-
"""Routers FastAPI para e-commerce (plataformas, productos, pedidos)."""
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from ecommerce.connector import EcommerceConnector
from ecommerce.models.product import EcommercePlatformConfig, EcommerceProduct

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


def get_gaiachain():
    """Dependencia GaiaChain."""
    if GaiaChainClient is None:
        return None
    return GaiaChainClient(rpc_url=os.getenv("GAIA_CHAIN_RPC_URL", ""))


def get_ecommerce_connector(gaiachain=Depends(get_gaiachain)) -> EcommerceConnector:
    return EcommerceConnector(gaiachain)


ecommerce_router = APIRouter()


@ecommerce_router.post("/platforms", summary="Añadir plataforma de e-commerce")
async def add_ecommerce_platform(
    config: EcommercePlatformConfig,
    connector: EcommerceConnector = Depends(get_ecommerce_connector),
):
    """Añade una nueva plataforma de e-commerce al sistema."""
    connector.add_platform(config)
    return {"status": "success", "platform": config.platform}


@ecommerce_router.post("/products/sync", summary="Sincronizar producto con e-commerce")
async def sync_ecommerce_product(
    platform: str,
    product: EcommerceProduct,
    connector: EcommerceConnector = Depends(get_ecommerce_connector),
):
    """Sincroniza un producto con una plataforma de e-commerce."""
    result = connector.sync_product(platform, product)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@ecommerce_router.post("/orders/webhook", summary="Webhook genérico para pedidos")
async def ecommerce_order_webhook(
    request: Request,
    platform: str,
    connector: EcommerceConnector = Depends(get_ecommerce_connector),
):
    """Recibe pedidos desde plataformas de e-commerce (webhook). Firma opcional según plataforma."""
    try:
        body = await request.body()
        order_data = json.loads(body) if body else {}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear cuerpo: {e}")
    result = connector.sync_order(platform, order_data)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@ecommerce_router.get("/products/{platform}/{product_id}", summary="Estado de producto en plataforma")
async def get_ecommerce_product_status(
    platform: str,
    product_id: str,
    connector: EcommerceConnector = Depends(get_ecommerce_connector),
):
    """Obtiene el estado de un producto en una plataforma de e-commerce."""
    result = connector.get_product_status(platform, product_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", "No encontrado"))
    return result
