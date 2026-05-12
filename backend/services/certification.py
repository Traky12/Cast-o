# -*- coding: utf-8 -*-
"""Generación de certificados AEMPS/GlobalGAP: PDF + QR (GaiaChain)."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    _HAS_REPORTLAB = True
except ImportError:
    _HAS_REPORTLAB = False

try:
    import qrcode
    _HAS_QRCODE = True
except ImportError:
    _HAS_QRCODE = False

CERT_DIR = Path(__file__).resolve().parents[1].parent / "certificates"


def _ensure_cert_dir() -> Path:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    return CERT_DIR


def generate_certificate(
    batch_id: str,
    strain: str,
    thc: float,
    cbd: float,
    lab_results: Dict[str, Any],
) -> str:
    """Genera certificado PDF con QR que enlaza a GaiaChain."""
    if not _HAS_REPORTLAB:
        raise RuntimeError("reportlab not installed. pip install reportlab")
    if not _HAS_QRCODE:
        raise RuntimeError("qrcode not installed. pip install qrcode[pil]")

    _ensure_cert_dir()
    pdf_path = CERT_DIR / f"{batch_id}.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "CERTIFICADO DE CALIDAD AEMPS")
    c.setFont("Helvetica", 12)
    c.drawString(100, 730, f"Batch ID: {batch_id}")
    c.drawString(100, 710, f"Strain: {strain}")
    c.drawString(100, 690, f"THC: {thc}% | CBD: {cbd}%")

    c.drawString(100, 650, "Resultados de Laboratorio:")
    y = 630
    for key, value in (lab_results or {}).items():
        c.drawString(120, y, f"{key}: {value}")
        y -= 20

    qr_url = f"https://gaia-chain.com/batch/{batch_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_path = CERT_DIR / f"{batch_id}_qr.png"
    img.save(str(img_path))
    c.drawImage(str(img_path), 400, 600, width=100, height=100)

    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, 50, f"Generado el {datetime.now().strftime('%d/%m/%Y')}")
    c.save()

    return str(pdf_path)
