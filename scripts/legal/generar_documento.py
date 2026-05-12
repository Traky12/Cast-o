#!/usr/bin/env python3
"""
CASTUO-SYSTEM™ | Generación de documentos legales (BOE, RD 244/2019).
Genera documento desde plantilla Jinja2, hash, IPFS y sugiere commit con TX hash.
Uso: python scripts/legal/generar_documento.py
"""
import argparse
import hashlib
import os
import sys
from pathlib import Path

# Ajustar path para importar jinja2 (pip install jinja2)
try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Instala: pip install jinja2")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates" / "legal"
OUTPUT = ROOT / "docs" / "legal"

def main():
    ap = argparse.ArgumentParser(description="Generar documento legal (licencia autoconsumo)")
    ap.add_argument("--finca", default="La Esperanza", help="Nombre de la finca")
    ap.add_argument("--potencia", type=int, default=500, help="Potencia kW")
    ap.add_argument("--tx", default="a1b2c3d4e5f67890123456789abcdef0", help="TX hash BioCoin Castúo")
    args = ap.parse_args()

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)))
    template = env.get_template("licencia_autoconsumo.md")

    data = {
        "empresa": {
            "nombre": "CASTUO-SYSTEM™",
            "nif": os.environ.get("CASTUO_NIF", "B12345678"),
            "direccion": os.environ.get("CASTUO_DIRECCION", "Polígono Industrial, Cáceres"),
        },
        "potencia": args.potencia,
        "rea": {"numero": f"REA-2026-{args.potencia:04d}"},
        "fecha": "2026-03-15",
        "tx_hash": args.tx,
        "git_commit": os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or "unknown",
        "repo": "castu-system",
        "documento": {"hash": "", "ipfs": ""},
    }

    documento = template.render(**data)
    doc_hash = hashlib.sha256(documento.encode()).hexdigest()
    data["documento"] = {"hash": doc_hash[:16], "ipfs": "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"}

    documento = template.render(**data)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT / f"licencia_REA-{data['rea']['numero']}.md"
    out_file.write_text(documento, encoding="utf-8")

    print(f"✅ Documento generado: {out_file}")
    print(f"   Hash: {doc_hash[:32]}...")
    print(f"   TX BioCoin: {args.tx}")
    print(f"   Commit sugerido: git add . && git commit -m \"docs(legal): Licencia REA-{data['rea']['numero']} TX:[{args.tx}]\"")
    return 0

if __name__ == "__main__":
    sys.exit(main())
