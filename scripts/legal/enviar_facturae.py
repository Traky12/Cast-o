#!/usr/bin/env python3
"""
CASTUO-SYSTEM™ | Generación y envío de facturas SII Facturae 3.2.1 (España).
Genera XML desde plantilla y prepara envío a FACe/SII (configurar WSDL y credenciales).
Uso: python scripts/legal/enviar_facturae.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates" / "legal"

def main():
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        print("Instala: pip install jinja2 lxml zeep")
        return 1

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("facturae.xml")
    data = {
        "empresa": {"nombre": "CASTUO-SYSTEM™", "nif": os.environ.get("CASTUO_NIF", "B12345678")},
        "cliente": {"nombre": "Cliente Ejemplo SA", "nif": "A87654321"},
        "factura": {
            "numero": "FACT-2026-0001",
            "fecha": "2026-03-15",
            "base_imponible": "1000.00",
            "iva": "210.00",
            "total": "1210.00",
        },
        "tx_hash": os.environ.get("BIOCAST_TX", "a1b2c3d4e5f67890123456789abcdef0"),
        "git_commit": os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or "unknown",
    }
    xml_factura = template.render(**data)
    out = ROOT / "docs" / "legal" / "factura_FACT-2026-0001.xml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(xml_factura, encoding="utf-8")
    print(f"✅ XML Facturae generado: {out}")
    print("   Envío a SII: configurar WSDL y ClaveFirma en zeep/requests según documentación FACe.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
