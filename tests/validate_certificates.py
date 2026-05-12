# tests/validate_certificates.py — Flujo completo de generación y verificación de certificados
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASE_URL = "http://localhost:8000/api/certificates"


def test_certificate_flow():
    """Prueba generación de certificado de producto, exportación y verificación."""
    r = requests.post(
        f"{BASE_URL}/product",
        params={
            "batch_id": "MG-RADISH-20231101",
            "product_type": "microgreens",
            "variety": "radish",
        },
        timeout=10,
    )
    print("Generar certificado de producto:", r.status_code)
    if r.status_code != 200:
        print("Error:", r.json().get("message", r.text[:200]))
        return
    product_cert = r.json()
    cert_id = product_cert.get("certificate", {}).get("certificate_id")
    print("  Certificado generado:", cert_id)

    r = requests.post(
        f"{BASE_URL}/export",
        params={
            "product_cert_id": cert_id,
            "destination_country": "Portugal",
            "importer": "Algarve Fresh Produce Lda.",
        },
        timeout=10,
    )
    print("Generar certificado de exportación:", r.status_code)
    if r.status_code != 200:
        print("Error:", r.json().get("message", r.text[:200]))
        return
    export_cert = r.json()
    export_cert_id = export_cert.get("export_certificate", {}).get("certificate_id")
    print("  Certificado de exportación:", export_cert_id)

    for cid in [cert_id, export_cert_id]:
        r = requests.get(f"{BASE_URL}/verify/{cid}", timeout=10)
        print(f"Verificar {cid}:", r.status_code)
        if r.status_code == 200:
            d = r.json()
            print("  Válido:", d.get("valid"), "GaiaChain TX:", d.get("gaiachain_tx"))
        else:
            print("  Error:", r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:150])


if __name__ == "__main__":
    print("Validando flujo de certificados...")
    test_certificate_flow()
    print("Validación completada.")
