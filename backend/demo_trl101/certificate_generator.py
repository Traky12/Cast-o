from __future__ import annotations

import html
import logging
from datetime import datetime, timezone
from typing import Any

from backend.demo_trl101.paths import cert_dir, ensure_demo_dirs

logger = logging.getLogger(__name__)

try:
    import qrcode
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    _HAS_RL = True
except ImportError:
    _HAS_RL = False


def _sensor(gemelo_data: dict[str, Any], key: str) -> str:
    sd = gemelo_data.get("sensor_data") or {}
    v = sd.get(key)
    return str(v) if v is not None else "N/A"


def generate_certificate(gemelo_data: dict[str, Any]) -> dict[str, str]:
    """
    PDF + HTML bajo data/demo_trl101/certificates/.
    Sin ReportLab solo HTML (el stand sigue teniendo evidencia verificable por hash witness).
    """
    ensure_demo_dirs()
    gemelo_id = str(gemelo_data["gemelo_id"])
    agent_type = str(gemelo_data.get("agent_type", ""))
    ts = str(gemelo_data.get("ingest_timestamp", ""))
    gref = str(gemelo_data.get("gaiachain_ref", gemelo_data.get("gaiachain_tx", "pendiente")))

    html_path = cert_dir() / f"{gemelo_id}.html"
    html_body = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>Certificado gemelo {html.escape(gemelo_id)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; }}
.cert {{ border: 2px solid #1a5f2a; padding: 24px; max-width: 720px; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background: #e8f5e9; }}
</style></head><body>
<div class="cert">
<h1>Certificado de gemelo digital (demo)</h1>
<p><strong>ID:</strong> {html.escape(gemelo_id)}</p>
<p><strong>Tipo agente:</strong> {html.escape(agent_type)}</p>
<p><strong>Ingesta:</strong> {html.escape(ts)}</p>
<p><strong>Referencia witness:</strong> {html.escape(gref)}</p>
<table>
<tr><th>Parametro</th><th>Valor</th><th>Unidad</th></tr>
<tr><td>Temperatura</td><td>{html.escape(_sensor(gemelo_data, 'temperature'))}</td><td>°C</td></tr>
<tr><td>Humedad</td><td>{html.escape(_sensor(gemelo_data, 'humidity'))}</td><td>%</td></tr>
<tr><td>Radiacion</td><td>{html.escape(_sensor(gemelo_data, 'radiation'))}</td><td>W/m2</td></tr>
<tr><td>CO2</td><td>{html.escape(_sensor(gemelo_data, 'co2'))}</td><td>ppm</td></tr>
</table>
<p><small>Documento de demostracion — no es certificado oficial AEAT/ENAC.</small></p>
</div></body></html>"""
    html_path.write_text(html_body, encoding="utf-8")

    pdf_rel = f"/agents/gemelo/artifacts/certificate/{gemelo_id}.pdf"
    html_rel = f"/agents/gemelo/artifacts/certificate/{gemelo_id}.html"

    if not _HAS_RL:
        logger.warning("ReportLab/qrcode no disponibles: solo HTML generado")
        return {"pdf": "", "html": html_rel, "path_pdf": "", "path_html": str(html_path)}

    pdf_path = cert_dir() / f"{gemelo_id}.pdf"
    qr_png = cert_dir() / f"{gemelo_id}_qr.png"

    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, letter[1] - 72, "CERTIFICADO GEMELO DIGITAL (DEMO)")
    c.setFont("Helvetica", 10)
    y = letter[1] - 100
    for line in (
        f"ID: {gemelo_id}",
        f"Tipo: {agent_type}",
        f"Fecha: {ts}",
        f"Witness: {gref}",
    ):
        c.drawString(72, y, line)
        y -= 16

    rows = [
        ("Temperatura", _sensor(gemelo_data, "temperature"), "°C"),
        ("Humedad", _sensor(gemelo_data, "humidity"), "%"),
        ("Radiacion", _sensor(gemelo_data, "radiation"), "W/m2"),
        ("CO2", _sensor(gemelo_data, "co2"), "ppm"),
    ]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(72, y, "Parametro / Valor / Unidad")
    y -= 18
    c.setFont("Helvetica", 9)
    for label, val, unit in rows:
        c.drawString(72, y, f"{label}: {val} {unit}")
        y -= 14

    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(f"castuo:demo:gemelo:{gemelo_id}:witness:{gref[:32]}")
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(str(qr_png))
    c.drawImage(str(qr_png), letter[0] - 200, 72, width=120, height=120)

    c.setFont("Helvetica-Oblique", 7)
    c.drawString(72, 36, f"Generado {datetime.now(timezone.utc).isoformat()} — Castuo demo")
    c.save()

    return {"pdf": pdf_rel, "html": html_rel, "path_pdf": str(pdf_path), "path_html": str(html_path)}
