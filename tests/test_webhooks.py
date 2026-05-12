# tests/test_webhooks.py — Simular pedidos desde Shopify/WooCommerce
import hashlib
import hmac
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE_URL = "http://localhost:8000/webhooks"


def _local_backend_listening() -> bool:
    if os.getenv("CASTUO_SKIP_LIVE_API") == "1":
        return False
    if os.getenv("CASTUO_FORCE_LIVE_API") == "1":
        return True
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=0.25):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _local_backend_listening(),
    reason="Sin servicio en 127.0.0.1:8000 — levantar backend o CASTUO_FORCE_LIVE_API=1",
)


def generate_shopify_signature(data: str, secret: str) -> str:
    return hmac.new(secret.encode(), data.encode(), hashlib.sha256).hexdigest()


def test_shopify_webhook():
    """Simula un webhook de pedido desde Shopify."""
    order_data = {
        "id": 123456789,
        "order_number": "1001",
        "name": "#1001",
        "customer": {"id": 987654, "email": "cliente@ejemplo.com"},
        "line_items": [
            {
                "id": 1,
                "product_id": 67890,
                "title": "Microgreens de Rábano",
                "quantity": 2,
                "price": "4.99",
                "sku": "MG-RADISH-100G",
            }
        ],
        "shipping_address": {
            "address1": "Calle Ejemplo 123",
            "city": "Madrid",
            "country": "España",
        },
        "billing_address": {},
        "gateway": "shopify_payments",
        "financial_status": "paid",
        "fulfillment_status": "unfulfilled",
        "total_price": "9.98",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    secret = "fake_webhook_secret"
    signature = generate_shopify_signature(json.dumps(order_data), secret)
    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}
    r = requests.post(
        f"{BASE_URL}/shopify/orders",
        headers=headers,
        json=order_data,
        timeout=10,
    )
    print("Shopify webhook:", r.status_code, r.json() if r.ok else r.text[:200])


def test_woocommerce_webhook():
    """Simula un webhook de pedido desde WooCommerce."""
    order_data = {
        "id": 789,
        "number": "1002",
        "customer_id": 456,
        "billing": {
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan@ejemplo.com",
        },
        "line_items": [
            {
                "id": 12,
                "product_id": 34,
                "name": "Brotes de Brócoli",
                "quantity": 1,
                "price": "5.99",
                "sku": "SP-BROCCOLI-250G",
            }
        ],
        "shipping": {
            "address_1": "Avenida Principal 456",
            "city": "Barcelona",
            "country": "ES",
        },
        "payment_method": "stripe",
        "total": "5.99",
        "status": "processing",
        "date_created": datetime.now().isoformat(),
        "date_modified": datetime.now().isoformat(),
    }
    r = requests.post(
        f"{BASE_URL}/woocommerce/orders",
        json=order_data,
        timeout=10,
    )
    print("WooCommerce webhook:", r.status_code, r.json() if r.ok else r.text[:200])


if __name__ == "__main__":
    print("Probando webhooks...")
    test_shopify_webhook()
    test_woocommerce_webhook()
    print("Pruebas de webhooks completadas.")
