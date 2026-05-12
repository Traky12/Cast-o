# -*- coding: utf-8 -*-
"""Conector genérico para plataformas e-commerce (Shopify, WooCommerce, Amazon)."""
import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ecommerce.models.product import EcommerceOrder, EcommercePlatformConfig, EcommerceProduct

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore

logger = logging.getLogger(__name__)


class EcommerceConnector:
    """Conector genérico para plataformas de e-commerce."""

    def __init__(self, gaiachain_client: Optional[Any] = None):
        self.gaiachain = gaiachain_client
        self.platforms: Dict[str, EcommercePlatformConfig] = {}

    def add_platform(self, config: EcommercePlatformConfig) -> None:
        """Añade una plataforma de e-commerce."""
        self.platforms[config.platform] = config

    def sync_product(self, platform: str, product: EcommerceProduct) -> Dict[str, Any]:
        """Sincroniza un producto con una plataforma de e-commerce."""
        try:
            config = self.platforms.get(platform)
            if not config or not config.active:
                return {"status": "error", "message": "Plataforma no configurada o inactiva"}

            if platform == "shopify":
                return self._sync_to_shopify(config, product)
            if platform == "woocommerce":
                return self._sync_to_woocommerce(config, product)
            if platform == "amazon":
                return self._sync_to_amazon(config, product)
            return {"status": "error", "message": f"Plataforma {platform} no soportada"}
        except Exception as e:
            logger.exception("Error al sincronizar producto con %s: %s", platform, e)
            return {"status": "error", "message": str(e)}

    def _sync_to_shopify(
        self, config: EcommercePlatformConfig, product: EcommerceProduct
    ) -> Dict[str, Any]:
        """Sincroniza un producto con Shopify."""
        if not requests:
            return {"status": "error", "message": "requests no instalado"}
        try:
            url = f"{config.store_url.rstrip('/')}/admin/api/2023-10/products.json"
            headers = {
                "X-Shopify-Access-Token": config.api_key,
                "Content-Type": "application/json",
            }
            payload = product.model_dump() if hasattr(product, "model_dump") else product.dict()
            shopify_product = {
                "product": {
                    "title": product.title,
                    "body_html": product.description,
                    "vendor": product.vendor,
                    "product_type": product.product_type,
                    "status": product.status,
                    "tags": ", ".join(product.tags),
                    "images": [img.model_dump() if hasattr(img, "model_dump") else img.dict() for img in product.images],
                    "variants": [v.model_dump() if hasattr(v, "model_dump") else v.dict() for v in product.variants],
                    "options": product.options,
                    "metafields": product.metafields,
                }
            }
            if product.id:
                url = f"{config.store_url.rstrip('/')}/admin/api/2023-10/products/{product.id}.json"
                resp = requests.put(url, headers=headers, json=shopify_product, timeout=30)
            else:
                resp = requests.post(url, headers=headers, json=shopify_product, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_ecommerce_sync(
                    {
                        "platform": "shopify",
                        "action": "product_sync",
                        "product_id": str(result.get("product", {}).get("id", "")),
                        "product_title": product.title,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                    }
                )
            return {
                "status": "success",
                "platform": "shopify",
                "product_id": result.get("product", {}).get("id"),
                "gaiachain_tx": tx_hash,
                "response": result,
            }
        except requests.exceptions.RequestException as e:
            logger.exception("Error en sincronización con Shopify: %s", e)
            return {
                "status": "error",
                "message": str(e),
                "details": getattr(e, "response", None) and getattr(e.response, "text", None),
            }

    def _sync_to_woocommerce(
        self, config: EcommercePlatformConfig, product: EcommerceProduct
    ) -> Dict[str, Any]:
        """Sincroniza un producto con WooCommerce."""
        if not requests:
            return {"status": "error", "message": "requests no instalado"}
        try:
            url = f"{config.store_url.rstrip('/')}/wp-json/wc/v3/products"
            auth = (config.api_key, config.api_secret)
            payload = {
                "name": product.title,
                "type": "variable" if product.variants else "simple",
                "status": product.status,
                "description": product.description,
                "short_description": product.description[:150],
                "categories": [{"id": 1}],
                "tags": product.tags,
                "images": [{"src": img.url, "alt": img.alt_text} for img in product.images],
                "meta_data": product.metafields,
            }
            if product.id:
                url = f"{url}/{product.id}"
                resp = requests.put(url, auth=auth, json=payload, timeout=30)
            else:
                resp = requests.post(url, auth=auth, json=payload, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_ecommerce_sync(
                    {
                        "platform": "woocommerce",
                        "action": "product_sync",
                        "product_id": str(result.get("id", "")),
                        "product_title": product.title,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                    }
                )
            return {
                "status": "success",
                "platform": "woocommerce",
                "product_id": result.get("id"),
                "gaiachain_tx": tx_hash,
                "response": result,
            }
        except requests.exceptions.RequestException as e:
            logger.exception("Error en sincronización con WooCommerce: %s", e)
            return {
                "status": "error",
                "message": str(e),
                "details": getattr(e, "response", None) and getattr(e.response, "text", None),
            }

    def _sync_to_amazon(
        self, config: EcommercePlatformConfig, product: EcommerceProduct
    ) -> Dict[str, Any]:
        """Sincroniza un producto con Amazon (stub SP-API)."""
        try:
            pid = f"AMZ-{hashlib.md5(product.title.encode()).hexdigest()[:8]}"
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_ecommerce_sync(
                    {
                        "platform": "amazon",
                        "action": "product_sync",
                        "product_id": pid,
                        "product_title": product.title,
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                    }
                )
            return {
                "status": "success",
                "platform": "amazon",
                "product_id": pid,
                "gaiachain_tx": tx_hash,
                "message": "Producto sincronizado con Amazon (stub)",
            }
        except Exception as e:
            logger.exception("Error en sincronización con Amazon: %s", e)
            return {"status": "error", "message": str(e)}

    def sync_order(self, platform: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza un pedido desde la plataforma de e-commerce a CASTUO-SYSTEM."""
        try:
            config = self.platforms.get(platform)
            if not config or not config.active:
                return {"status": "error", "message": "Plataforma no configurada o inactiva"}
            signature = order_data.pop("signature", None)
            if config.webhook_secret and signature:
                if not self._verify_webhook_signature(order_data, signature, config.webhook_secret):
                    return {"status": "error", "message": "Firma de webhook inválida"}
            order = EcommerceOrder(**order_data)
            tx_hash = ""
            if self.gaiachain:
                tx_hash = self.gaiachain.log_ecommerce_order(
                    {
                        "platform": platform,
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "customer": order.customer,
                        "items": order.line_items,
                        "total_price": order.total_price,
                        "status": order.financial_status,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            return {
                "status": "success",
                "order_id": order.id,
                "gaiachain_tx": tx_hash,
                "message": f"Pedido {order.order_number} sincronizado correctamente",
            }
        except Exception as e:
            logger.exception("Error al sincronizar pedido desde %s: %s", platform, e)
            return {"status": "error", "message": str(e)}

    def _verify_webhook_signature(self, data: Dict, signature: str, secret: str) -> bool:
        """Verifica la firma de un webhook."""
        if not signature:
            return False
        body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        generated = hmac.new(
            secret.encode("utf-8"), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(generated, signature)

    def get_product_status(self, platform: str, product_id: str) -> Dict[str, Any]:
        """Obtiene el estado de un producto en una plataforma de e-commerce."""
        if not requests:
            return {"status": "error", "message": "requests no instalado"}
        try:
            config = self.platforms.get(platform)
            if not config or not config.active:
                return {"status": "error", "message": "Plataforma no configurada o inactiva"}
            if platform == "shopify":
                url = f"{config.store_url.rstrip('/')}/admin/api/2023-10/products/{product_id}.json"
                resp = requests.get(url, headers={"X-Shopify-Access-Token": config.api_key}, timeout=10)
                resp.raise_for_status()
                return {"status": "success", "platform": "shopify", "product_id": product_id, "data": resp.json().get("product", {})}
            if platform == "woocommerce":
                url = f"{config.store_url.rstrip('/')}/wp-json/wc/v3/products/{product_id}"
                resp = requests.get(url, auth=(config.api_key, config.api_secret), timeout=10)
                resp.raise_for_status()
                return {"status": "success", "platform": "woocommerce", "product_id": product_id, "data": resp.json()}
            return {"status": "error", "message": f"Plataforma {platform} no soportada para consulta"}
        except requests.exceptions.RequestException as e:
            logger.exception("Error al obtener producto %s en %s: %s", product_id, platform, e)
            return {"status": "error", "message": str(e)}
