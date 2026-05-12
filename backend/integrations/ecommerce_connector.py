# backend/integrations/ecommerce_connector.py — Conector genérico e-commerce (Shopify, WooCommerce)

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from backend.security.end_to_end_encryption import EndToEndEncryption
    from backend.compliance.immutable_traceability import ImmutableTraceability
    _E2E_AVAILABLE = True
except ImportError:
    EndToEndEncryption = None
    ImmutableTraceability = None
    _E2E_AVAILABLE = False

try:
    import requests
    _REQUESTS = True
except ImportError:
    requests = None
    _REQUESTS = False


class ECommerceConnector(ABC):
    """Interfaz abstracta para conectores de e-commerce."""

    @abstractmethod
    def get_orders(self, since: str, until: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_order_status(self, order_id: str, status: str) -> bool:
        pass

    @abstractmethod
    def get_products(self, updated_since: Optional[str] = None) -> List[Dict[str, Any]]:
        pass


class ShopifyConnector(ECommerceConnector):
    """Conector para Shopify Admin API."""

    def __init__(self, shop_url: str, api_key: str, api_password: str) -> None:
        self.shop_url = shop_url.rstrip("/").replace("https://", "").replace("http://", "")
        self.api_key = api_key
        self.api_password = api_password
        self.logger = logging.getLogger(__name__)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        if not _REQUESTS or requests is None:
            self.logger.warning("requests no instalado")
            return {}
        url = f"https://{self.shop_url}/admin/api/2023-07/{endpoint}"
        auth = (self.api_key, self.api_password)
        try:
            r = requests.request(
                method,
                url,
                auth=auth,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            return r.json() if r.text else {}
        except requests.exceptions.RequestException as e:
            self.logger.error("Error Shopify: %s", e)
            return {}

    def get_orders(self, since: str, until: str) -> List[Dict[str, Any]]:
        endpoint = f"orders.json?status=any&created_at_min={since}&created_at_max={until}&limit=250"
        data = self._make_request("GET", endpoint)
        return data.get("orders", [])

    def update_order_status(self, order_id: str, status: str) -> bool:
        endpoint = f"orders/{order_id}.json"
        data = self._make_request("PUT", endpoint, data={"order": {"id": order_id, "status": status}})
        return "order" in data

    def get_products(self, updated_since: Optional[str] = None) -> List[Dict[str, Any]]:
        endpoint = "products.json?limit=250"
        if updated_since:
            endpoint += f"&updated_at_min={updated_since}"
        data = self._make_request("GET", endpoint)
        return data.get("products", [])


class ConnectorFactory:
    """Fábrica de conectores por plataforma."""

    _registry: Dict[str, type] = {"shopify": ShopifyConnector}

    @classmethod
    def register(cls, platform: str, connector_class: type) -> None:
        cls._registry[platform.lower()] = connector_class

    @classmethod
    def create_connector(cls, platform: str, **kwargs: Any) -> ECommerceConnector:
        impl = cls._registry.get(platform.lower())
        if impl is None:
            raise ValueError(f"Plataforma no soportada: {platform}")
        return impl(**kwargs)


class SecureECommerceConnector(ECommerceConnector):
    """Conector e-commerce con cifrado E2E y trazabilidad para datos sensibles."""

    def __init__(self, platform: str, public_key: Optional[bytes] = None, **kwargs: Any) -> None:
        self.connector = ConnectorFactory.create_connector(platform, **kwargs)
        if not _E2E_AVAILABLE or EndToEndEncryption is None or ImmutableTraceability is None:
            raise ValueError("Se requiere EndToEndEncryption e ImmutableTraceability")
        self.encryption = EndToEndEncryption()
        self.traceability = ImmutableTraceability(self.encryption)
        self.platform_public_key = public_key or kwargs.get("public_key")
        if not self.platform_public_key:
            raise ValueError("Se requiere clave pública de la plataforma para cifrado")
        self._private_key = None

    def get_orders(self, since: str, until: str) -> List[Dict[str, Any]]:
        try:
            orders = self.connector.get_orders(since, until)
            secure_orders = []
            for order in orders:
                envelope = self.encryption.create_encrypted_envelope(
                    order,
                    self.platform_public_key,
                    metadata={"order_id": order.get("id"), "sensitive_fields": ["customer_email", "billing_address", "shipping_address"]},
                )
                if self.traceability:
                    self.traceability.register_event({
                        "type": "order_access",
                        "order_id": order.get("id"),
                        "sensitive_fields": ["customer_email", "billing_address", "shipping_address"],
                        "normative_references": ["GDPR:Art.15", "GDPR:Art.20"],
                    })
                secure_orders.append(envelope)
            return secure_orders
        except Exception as e:
            logger.error("get_orders seguro: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "ecommerce_error",
                    "operation": "get_orders",
                    "error": str(e),
                    "severity": "high",
                    "normative_references": ["ISO_27001:A.16.1.1"],
                })
            raise

    def update_order_status(self, order_id: str, status: str) -> bool:
        try:
            if self.traceability:
                self.traceability.register_event({
                    "type": "order_status_update",
                    "order_id": order_id,
                    "new_status": status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            success = self.connector.update_order_status(order_id, status)
            if self.traceability:
                self.traceability.register_event({
                    "type": "order_status_updated",
                    "order_id": order_id,
                    "status": "success" if success else "failed",
                    "normative_references": ["GDPR:Art.17"],
                })
            return success
        except Exception as e:
            logger.error("update_order_status: %s", e)
            if self.traceability:
                self.traceability.register_event({
                    "type": "order_update_error",
                    "order_id": order_id,
                    "error": str(e),
                    "severity": "high",
                })
            return False

    def get_products(self, updated_since: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.connector.get_products(updated_since=updated_since)
