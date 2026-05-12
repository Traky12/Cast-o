from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.demo_trl101.paths import ensure_demo_dirs, invoice_dir

logger = logging.getLogger(__name__)

try:
    import qrcode
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    from reportlab.pdfgen import canvas

    _HAS_RL = True
except ImportError:
    _HAS_RL = False


def generate_invoice_pdf_xml(
    gemelo_data: dict[str, Any],
    customer_data: dict[str, str],
) -> dict[str, str]:
    """
    PDF + XML inspirado en factura electronica (estructura simplificada).
    No validado contra XSD AEAT: etiquetar siempre como demo fiscal.
    """
    ensure_demo_dirs()
    invoice_id = f"FACT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    gemelo_id = str(gemelo_data["gemelo_id"])
    gref = str(gemelo_data.get("gaiachain_ref", gemelo_data.get("gaiachain_tx", "")))

    xml_path = invoice_dir() / f"{invoice_id}.xml"
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- DEMO CASTUO — NO ES FACTURAE AEAT VALIDADO -->
<FacturaDemo>
  <IDFactura>{invoice_id}</IDFactura>
  <Fecha>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</Fecha>
  <GemeloID>{gemelo_id}</GemeloID>
  <WitnessRef>{gref}</WitnessRef>
  <Receptor nombre="{customer_data.get('name','')}" nif="{customer_data.get('nif','')}" />
  <Lineas>
    <Linea concepto="Trazabilidad gemelo demo" base="100.00" iva="21" total="121.00"/>
  </Lineas>
</FacturaDemo>
"""
    xml_path.write_text(xml_content, encoding="utf-8")

    pdf_rel = f"/agents/gemelo/artifacts/invoice/{invoice_id}.pdf"
    if not _HAS_RL:
        logger.warning("ReportLab no disponible: solo XML de demo")
        return {"pdf": "", "xml": f"/agents/gemelo/artifacts/invoice/{invoice_id}.xml", "invoice_id": invoice_id}

    pdf_path = invoice_dir() / f"{invoice_id}.pdf"
    qr_path = invoice_dir() / f"{invoice_id}_qr.png"

    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 50, "FACTURA DEMO (no fiscal AEAT)")
    c.setFont("Helvetica", 10)
    y = h - 80
    for line in (
        f"Numero: {invoice_id}",
        f"Fecha: {datetime.now(timezone.utc).strftime('%d/%m/%Y')}",
        f"Gemelo: {gemelo_id}",
        f"Cliente: {customer_data.get('name', '')}",
        f"NIF: {customer_data.get('nif', '')}",
        f"Direccion: {customer_data.get('address', '')}",
    ):
        c.drawString(50, y, line)
        y -= 14

    data = [
        ["Concepto", "Cant.", "P.Unit.", "Total"],
        ["Trazabilidad gemelo (demo)", "1", "100.00 EUR", "100.00 EUR"],
        ["IVA 21%", "", "", "21.00 EUR"],
        ["TOTAL", "", "", "121.00 EUR"],
    ]
    t = Table(data, colWidths=[8 * cm, 2 * cm, 3 * cm, 3 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    t.wrapOn(c, 50, y - 20)
    t.drawOn(c, 50, y - 120)

    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(f"castuo:demo:invoice:{invoice_id}:gemelo:{gemelo_id}")
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(str(qr_path))
    c.drawImage(str(qr_path), w - 4 * cm, 3 * cm, width=3 * cm, height=3 * cm)

    c.setFont("Helvetica-Oblique", 7)
    c.drawString(50, 28, f"Witness ref: {gref[:64]}")
    c.save()

    return {
        "pdf": pdf_rel,
        "xml": f"/agents/gemelo/artifacts/invoice/{invoice_id}.xml",
        "invoice_id": invoice_id,
    }
