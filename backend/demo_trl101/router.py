from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from backend.demo_trl101.certificate_generator import generate_certificate
from backend.demo_trl101.invoice_generator import generate_invoice_pdf_xml
from backend.demo_trl101.paths import cert_dir, ensure_demo_dirs, invoice_dir

try:
    from backend.energy_audit.witness_minimal import witness_event
except ImportError:
    witness_event = None  # type: ignore[misc, assignment]

logger = logging.getLogger(__name__)

router = APIRouter()

_SAFE_NAME = re.compile(r"^[a-zA-Z0-9._-]+$")


class CustomerInvoice(BaseModel):
    name: str = Field(default="ICEX HLTH Demo", max_length=200)
    nif: str = Field(default="B00000000", max_length=32)
    address: str = Field(default="Espana (demo)", max_length=500)


class GemeloIngestRequest(BaseModel):
    agent_type: str = Field(..., min_length=1, max_length=80)
    sensor_data: dict[str, Any]
    metadata: dict[str, Any] | None = None
    customer: CustomerInvoice | None = None
    generate_invoice: bool = True


class GemeloIngestResponse(BaseModel):
    gemelo_id: str
    status: str
    timestamp: datetime
    gaiachain_tx: str | None = Field(None, description="Hash witness o referencia; no es tx mainnet sin evidencia")
    gaiachain_witness: dict[str, Any] | None = None
    certificate_url: str | None = None
    certificate_html_url: str | None = None
    invoice_pdf_url: str | None = None
    invoice_xml_url: str | None = None


def _witness_payload(processed: dict[str, Any]) -> dict[str, Any] | None:
    if witness_event is None:
        return None
    try:
        out = witness_event(processed, "CASTUO-DEMO-01")
        return out if isinstance(out, dict) else {"raw": str(out)}
    except Exception as e:
        logger.warning("witness_event demo: %s", e)
        return None


def _ref_from_witness(w: dict[str, Any] | None) -> str | None:
    if not w:
        return None
    h = w.get("hash")
    if isinstance(h, str) and h:
        return h
    return None


@router.post("/ingest", response_model=GemeloIngestResponse)
async def ingest_gemelo_data(request: GemeloIngestRequest) -> GemeloIngestResponse:
    ensure_demo_dirs()
    if not request.sensor_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sensor_data no puede estar vacio",
        )

    gemelo_id = f"gemelo-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    processed: dict[str, Any] = {
        "action": "gemelo_ingest",
        "gemelo_id": gemelo_id,
        "agent_type": request.agent_type,
        "sensor_data": request.sensor_data,
        "metadata": request.metadata or {},
        "ingest_timestamp": now.isoformat(),
    }

    w = _witness_payload(processed)
    gref = _ref_from_witness(w)

    bundle: dict[str, Any] = {
        "gemelo_id": gemelo_id,
        "agent_type": request.agent_type,
        "ingest_timestamp": processed["ingest_timestamp"],
        "sensor_data": request.sensor_data,
        "gaiachain_ref": gref or "sin_witness",
        "gaiachain_tx": gref,
    }

    cert = generate_certificate(bundle)
    cert_pdf = cert.get("pdf") or None
    cert_html = cert.get("html") or None

    inv_pdf: str | None = None
    inv_xml: str | None = None
    if request.generate_invoice:
        cust = (request.customer or CustomerInvoice()).model_dump()
        inv = generate_invoice_pdf_xml(bundle, cust)
        inv_pdf = inv.get("pdf") or None
        inv_xml = inv.get("xml")

    logger.info("gemelo ingest demo: %s tipo=%s witness=%s", gemelo_id, request.agent_type, bool(gref))

    return GemeloIngestResponse(
        gemelo_id=gemelo_id,
        status="success",
        timestamp=now,
        gaiachain_tx=gref,
        gaiachain_witness=w,
        certificate_url=cert_pdf,
        certificate_html_url=cert_html,
        invoice_pdf_url=inv_pdf,
        invoice_xml_url=inv_xml,
    )


@router.get("/artifacts/certificate/{gemelo_id}.pdf")
async def get_certificate_pdf(gemelo_id: str) -> FileResponse:
    if not _SAFE_NAME.match(gemelo_id):
        raise HTTPException(400, "id invalido")
    path = cert_dir() / f"{gemelo_id}.pdf"
    if not path.is_file():
        raise HTTPException(404, "PDF no generado (instala reportlab o genera con ingest)")
    return FileResponse(path, media_type="application/pdf", filename=f"{gemelo_id}.pdf")


@router.get("/artifacts/certificate/{gemelo_id}.html")
async def get_certificate_html(gemelo_id: str) -> HTMLResponse:
    if not _SAFE_NAME.match(gemelo_id):
        raise HTTPException(400, "id invalido")
    path = cert_dir() / f"{gemelo_id}.html"
    if not path.is_file():
        raise HTTPException(404, "HTML no encontrado")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/artifacts/invoice/{invoice_file}")
async def get_invoice_artifact(invoice_file: str) -> FileResponse:
    if not _SAFE_NAME.match(invoice_file):
        raise HTTPException(400, "nombre invalido")
    if not (invoice_file.endswith(".pdf") or invoice_file.endswith(".xml")):
        raise HTTPException(400, "solo pdf o xml")
    path = invoice_dir() / invoice_file
    if not path.is_file():
        raise HTTPException(404, "factura demo no encontrada")
    mt = "application/pdf" if invoice_file.endswith(".pdf") else "application/xml"
    return FileResponse(path, media_type=mt, filename=invoice_file)


@router.get("/dashboard", response_class=HTMLResponse)
async def demo_dashboard() -> HTMLResponse:
    """Panel HTML estatico: Prometheus/Grafana son la fuente de verdad para SLO reales."""
    body = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>Castuo demo gemelo — ICEX</title>
<style>
body { font-family: system-ui,sans-serif; margin:0; background:#0d1117; color:#e6edf3; }
header { background:#14532d; padding:1rem 1.5rem; }
main { max-width:960px; margin:1.5rem auto; padding:0 1rem; }
.card { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:1rem; margin:1rem 0; }
code { background:#21262d; padding:2px 6px; border-radius:4px; }
a { color:#58a6ff; }
ul { line-height:1.6; }
</style></head><body>
<header><h1>Gemelo digital — demo TRL / feria</h1>
<p>ICEX HLTH Europe: ingest + witness + artefactos locales</p></header>
<main>
<div class="card">
<h2>Endpoints</h2>
<ul>
<li><code>POST /agents/gemelo/ingest</code> — JSON sensor + <code>agent_type</code></li>
<li><code>GET /agents/gemelo/dashboard</code> — esta pagina</li>
<li>Artefactos bajo <code>/agents/gemelo/artifacts/...</code></li>
</ul>
</div>
<div class="card">
<h2>curl ejemplo</h2>
<pre style="overflow:auto;">curl -s -X POST "http://127.0.0.1:8000/agents/gemelo/ingest" \\
  -H "Content-Type: application/json" \\
  -d "{\\"agent_type\\":\\"agrovoltaico\\",\\"sensor_data\\":{\\"temperature\\":28.5,\\"humidity\\":65,\\"radiation\\":850,\\"co2\\":420}}"</pre>
</div>
<div class="card">
<h2>Limites honestos</h2>
<ul>
<li>Factura XML/PDF: <strong>demo</strong>, no FacturaE AEAT validada.</li>
<li><code>gaiachain_tx</code>: hash del witness minimal si hay <code>GAIA_CHAIN_API_KEY</code>; si no, referencia interna.</li>
<li>SLO 99,99% / eIDAS alto: requieren evidencia de explotacion; usar Grafana/Prometheus en el entorno real.</li>
</ul>
</div>
</main></body></html>"""
    return HTMLResponse(body)


@router.get("/health", response_class=PlainTextResponse)
async def gemelo_demo_health() -> str:
    return "ok"
