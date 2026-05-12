#!/usr/bin/env python3
"""
Genera propuestas comerciales PDF para las 3 cooperativas (SaaS €140/ha/mes).
Uso: python3 scripts/generar_propuestas_3_coops.py [--output-dir backend/propuestas]
"""
from __future__ import annotations

import argparse
import os
from datetime import datetime
from pathlib import Path

COOPS = [
    {"id": 1, "nombre": "Sabionda Educa SAT", "hectareas": 2.5, "cultivo": "lechuga"},
    {"id": 2, "nombre": "Cooperativa #2", "hectareas": 5.0, "cultivo": "vid"},
    {"id": 3, "nombre": "Cooperativa #3", "hectareas": 3.0, "cultivo": "tomate"},
]
PRECIO_HA_MES = 140.0
CONTACTO = "gregorio@castuo.es"
ASUNTO_EMAIL = "Contrato SaaS CASTÚO-SYSTEM - €140/ha/mes"


def _total(ha: float) -> float:
    return round(ha * PRECIO_HA_MES, 2)


def generar_pdf(coop: dict, out_dir: Path) -> str | None:
    total = _total(coop["hectareas"])
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        print("reportlab no instalado: pip install reportlab", flush=True)
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = coop["nombre"].lower().replace(" ", "_").replace("#", "n")
    filename = f"propuesta_castuo_{safe_name}.pdf"
    path = out_dir / filename
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(80, 750, "PROPUESTA COMERCIAL")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(80, 720, "Contrato SaaS CASTÚO-SYSTEM — Plataforma agrovoltaica")
    c.setFont("Helvetica", 11)
    c.drawString(80, 690, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawString(80, 670, "Destinatario:")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(80, 650, coop["nombre"])
    c.setFont("Helvetica", 11)
    c.drawString(80, 620, f"Cultivo principal: {coop['cultivo']}")
    c.drawString(80, 600, f"Superficie: {coop['hectareas']} ha")
    c.drawString(80, 570, f"Tarifa: €{PRECIO_HA_MES:.0f}/ha/mes (SaaS gestión + IoT + NFT)")
    c.drawString(80, 540, f"Total mensual: €{total:.2f}/mes")
    c.drawString(80, 500, "Condiciones: facturación mensual, plazo pago 30-60 días.")
    c.drawString(80, 480, "Firma digital eIDAS disponible tras aceptación.")
    c.drawString(80, 430, f"Contacto: {CONTACTO}")
    c.drawString(80, 410, "CC: gregorio@castuo.es")
    c.drawString(80, 370, "CASTÚO 360 S.L. — CASTÚO-SYSTEM™ v1.7.3")
    c.save()
    return str(path)


def main():
    parser = argparse.ArgumentParser(description="Generar propuestas PDF 3 cooperativas")
    parser.add_argument("--output-dir", type=str, default=None, help="Carpeta de salida (default: backend/propuestas)")
    parser.add_argument("--all-coops", action="store_true", help="Ignorado; siempre se generan las 3")
    args = parser.parse_args()
    script_dir = Path(__file__).resolve().parent
    backend = script_dir.parent
    out_dir = Path(args.output_dir) if args.output_dir else backend / "propuestas"
    out_dir = out_dir.resolve()
    print(f"Asunto email sugerido: {ASUNTO_EMAIL}")
    print(f"Salida: {out_dir}")
    for coop in COOPS:
        path = generar_pdf(coop, out_dir)
        if path:
            total = _total(coop["hectareas"])
            print(f"  OK Coop {coop['id']} {coop['nombre']}: €{total}/mes → {os.path.basename(path)}")
        else:
            print(f"  SKIP Coop {coop['id']} (reportlab no disponible)")
    total_mes = sum(_total(c["hectareas"]) for c in COOPS)
    print(f"Total facturable: €{total_mes:.0f}/mes (10.5 ha)")


if __name__ == "__main__":
    main()
