# -*- coding: utf-8 -*-
"""Manejadores de webhooks por plataforma (Shopify, WooCommerce)."""
import hmac
import hashlib
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ecommerce.connector import EcommerceConnector
from ecommerce.routers import get_ecommerce_connector

logger = logging.getLogger(__name__)

router = APIRouter()


async def _handle_webhook(request: Request, platform: str, connector: EcommerceConnector) -> dict:
    """Procesa un webhook genérico (verificación de firma y sincronización de pedido)."""
    body = await request.body()
    signature_header = (
        request.headers.get("X-Shopify-Hmac-Sha256")
        if platform == "shopify"
        else request.headers.get("X-WC-Webhook-Signature")
    )

    if signature_header:
        config = connector.platforms.get(platform)
        if not config or not config.webhook_secret:
            raise HTTPException(status_code=401, detail="Plataforma no configurada o sin webhook_secret")

        generated = hmac.new(
            config.webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if platform == "woocommerce":
            # WooCommerce puede enviar signature en formato distinto
            if not hmac.compare_digest(generated, signature_header):
                raise HTTPException(status_code=401, detail="Firma de webhook inválida")
        else:
            if not hmac.compare_digest(generated, signature_header):
                raise HTTPException(status_code=401, detail="Firma de webhook inválida")

    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al parsear JSON: {e}")

    logger.info("Webhook recibido de %s: %s", platform, list(data.keys()) if isinstance(data, dict) else "payload")

    # Normalizar a formato EcommerceOrder si hace falta (Shopify/WooCommerce envían estructuras distintas)
    order_data = _normalize_order_payload(platform, data)

    result = connector.sync_order(platform, order_data)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error al sincronizar"))
    return result


def _normalize_order_payload(platform: str, data: dict) -> dict:
    """Convierte payload de Shopify/WooCommerce a campos compatibles con EcommerceOrder."""
    if platform == "shopify":
        return {
            "id": str(data.get("id", "")),
            "order_number": str(data.get("order_number", data.get("name", ""))),
            "customer": data.get("customer", {}),
            "line_items": data.get("line_items", []),
            "shipping_address": data.get("shipping_address", {}),
            "billing_address": data.get("billing_address", {}),
            "payment_method": data.get("gateway", ""),
            "total_price": float(data.get("total_price", 0)),
            "financial_status": data.get("financial_status", "pending"),
            "fulfillment_status": data.get("fulfillment_status", "unfulfilled"),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
        }
    if platform == "woocommerce":
        return {
            "id": str(data.get("id", "")),
            "order_number": str(data.get("number", data.get("id", ""))),
            "customer": data.get("billing", data.get("customer", {})),
            "line_items": data.get("line_items", []),
            "shipping_address": data.get("shipping", {}),
            "billing_address": data.get("billing", {}),
            "payment_method": data.get("payment_method", ""),
            "total_price": float(data.get("total", 0)),
            "financial_status": "paid" if data.get("status") == "processing" else "pending",
            "fulfillment_status": "unfulfilled",
            "created_at": data.get("date_created", ""),
            "updated_at": data.get("date_modified", ""),
        }
    return data


@router.post("/shopify/orders", summary="Webhook pedidos Shopify")
async def shopify_order_webhook(
    request: Request,
    connector: EcommerceConnector = Depends(get_ecommerce_connector),
):
    """Maneja webhooks de pedidos desde Shopify."""
    return await _handle_webhook(request, "shopify", connector)


@router.post("/woocommerce/orders", summary="Webhook pedidos WooCommerce")
async def woocommerce_order_webhook(
    request: Request,
    connector: EcommerceConnector = Depends(get_ecommerce_connector),
):
    """Maneja webhooks de pedidos desde WooCommerce."""
    return await _handle_webhook(request, "woocommerce", connector)
