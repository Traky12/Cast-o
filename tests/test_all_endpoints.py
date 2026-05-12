# tests/test_all_endpoints.py — Verificar que los nuevos routers responden correctamente
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

import pytest
import requests

# Raíz del proyecto
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE_URL = "http://localhost:8000/api"


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


def _now():
    return datetime.now().isoformat()


def test_environment_control():
    """Prueba el endpoint de control ambiental."""
    data = {
        "tray_id": "CASTUO-TRAY-001",
        "crop_type": "microgreens",
        "growth_stage": "growing",
        "ozone": {
            "value": 0.03,
            "threshold_min": 0.01,
            "threshold_max": 0.05,
            "status": "normal",
            "timestamp": _now(),
        },
        "reverse_osmosis": {
            "input_ec": 0.75,
            "output_ec": 0.03,
            "rejection_rate": 96.0,
            "flow_rate": 500.0,
            "filter_life": 85.0,
            "timestamp": _now(),
        },
        "uv_light": {
            "intensity": 200.0,
            "exposure_time": 15.0,
            "status": "on",
            "timestamp": _now(),
        },
        "nutrients": {
            "ec": 1.0,
            "ph": 6.0,
            "temperature": 20.5,
            "orp": 280.0,
            "timestamp": _now(),
        },
        "co2": 450.0,
        "temperature": 21.0,
        "humidity": 65.0,
        "timestamp": _now(),
    }
    r = requests.post(f"{BASE_URL}/environment/data", json=data, timeout=10)
    print("Control ambiental:", r.status_code, r.json() if r.ok else r.text[:200])


def test_microgreens():
    """Prueba los endpoints de microgreens."""
    r = requests.post(
        f"{BASE_URL}/microgreens/batches",
        params={"variety_name": "radish", "tray_id": "CASTUO-TRAY-001", "quantity": 100},
        timeout=10,
    )
    print("Crear lote microgreens:", r.status_code, r.json() if r.ok else r.text[:200])
    if r.status_code != 200:
        return
    batch_id = r.json().get("batch", {}).get("batch_id")
    if not batch_id:
        return
    r = requests.put(
        f"{BASE_URL}/microgreens/batches/{batch_id}",
        params={"status": "germinating"},
        timeout=10,
    )
    print("Actualizar estado:", r.status_code, r.json() if r.ok else r.text[:200])
    r = requests.post(f"{BASE_URL}/microgreens/batches/{batch_id}/certificate", timeout=10)
    print("Generar certificado:", r.status_code, r.json() if r.ok else r.text[:200])


def test_water_treatment():
    """Prueba los endpoints de tratamiento de agua."""
    t = _now()
    treatment_data = {
        "treatment_id": "WT-20231101-001",
        "system": {
            "input_water": {
                "ec": 0.75,
                "tds": 380.0,
                "ph": 7.2,
                "orp": 150.0,
                "temperature": 18.0,
                "timestamp": t,
            },
            "output_water": {
                "ec": 0.03,
                "tds": 15.0,
                "ph": 6.0,
                "orp": 300.0,
                "temperature": 20.0,
                "timestamp": t,
            },
            "rejection_rate": 96.0,
            "flow_rate": 500.0,
            "pressure": 4.5,
            "filter_life": 85.0,
            "maintenance_needed": False,
            "timestamp": t,
        },
        "treatments_applied": ["reverse_osmosis", "ph_adjustment", "ozone"],
        "post_treatment_quality": {
            "ec": 0.03,
            "tds": 15.0,
            "ph": 6.0,
            "orp": 300.0,
            "temperature": 20.0,
            "timestamp": t,
        },
        "operator": "TEC-001",
        "timestamp": t,
    }
    r = requests.post(f"{BASE_URL}/water/treatments", json=treatment_data, timeout=10)
    print("Tratamiento de agua:", r.status_code, r.json() if r.ok else r.text[:200])


def test_certification():
    """Prueba los endpoints de certificación."""
    r = requests.post(
        f"{BASE_URL}/certificates/product",
        params={
            "batch_id": "MG-RADISH-20231101",
            "product_type": "microgreens",
            "variety": "radish",
        },
        timeout=10,
    )
    print("Certificado de producto:", r.status_code, r.json() if r.ok else r.text[:200])
    if r.status_code != 200:
        return
    cert = r.json().get("certificate", {})
    cert_id = cert.get("certificate_id") if isinstance(cert, dict) else None
    if cert_id:
        r = requests.get(f"{BASE_URL}/certificates/verify/{cert_id}", timeout=10)
        print("Verificar certificado:", r.status_code, r.json() if r.ok else r.text[:200])


def test_ecommerce():
    """Prueba los endpoints de e-commerce (simulado)."""
    config = {
        "platform": "shopify_test",
        "api_key": "fake_api_key",
        "api_secret": "fake_secret",
        "store_url": "https://fake-shop.myshopify.com",
        "webhook_secret": "fake_webhook_secret",
        "active": True,
    }
    r = requests.post(f"{BASE_URL}/ecommerce/platforms", json=config, timeout=10)
    print("Añadir plataforma:", r.status_code, r.json() if r.ok else r.text[:200])
    product = {
        "title": "Microgreens de Rábano (100g)",
        "description": "Cultivados en sistema hidropónico con trazabilidad blockchain.",
        "handle": "microgreens-rabano-100g",
        "product_type": "microgreens",
        "variants": [
            {
                "id": "var_100g",
                "sku": "MG-RADISH-100G",
                "name": "100g",
                "price": 4.99,
                "weight": 100.0,
                "inventory_quantity": 50,
                "inventory_policy": "deny",
            }
        ],
    }
    r = requests.post(
        f"{BASE_URL}/ecommerce/products/sync",
        params={"platform": "shopify_test"},
        json=product,
        timeout=10,
    )
    print("Sincronizar producto:", r.status_code, r.json() if r.ok else r.text[:200])


if __name__ == "__main__":
    print("Iniciando pruebas de endpoints...")
    test_environment_control()
    test_microgreens()
    test_water_treatment()
    test_certification()
    test_ecommerce()
    print("Pruebas completadas.")
