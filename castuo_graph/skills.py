"""
CASTÚO-SYSTEM™ v3.1 — Skills de Trazabilidad
Punto 2: registro real en GaiaChain (Web3 JSON-RPC)
Punto 4: generación de certificado PDF (reportlab)

Uso:
    from skills import registrar_en_blockchain, generar_pdf

    tx  = registrar_en_blockchain(lote_id, metadata)
    pdf = generar_pdf(lote_id, tx_hash=tx, metadata=metadata, output_dir="/tmp")

Fallbacks seguros:
    - registrar_en_blockchain: sim-<hash> determinista si clave o nodo no configurados
    - generar_pdf: fichero de texto plano (.pdf) si reportlab no instalado

Variables de entorno:
    GAIACHAIN_RPC_URL      — Endpoint JSON-RPC del nodo GaiaChain (ej. http://gaia:8545)
    GAIACHAIN_PRIVATE_KEY  — Clave privada hex 0x... para firmar TXs
    QR_OUTPUT_DIR          — Directorio de salida para PDFs y QRs (default: /tmp)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Web3 import (optional) ────────────────────────────────────────────────────
try:
    from web3 import Web3
    _WEB3_AVAILABLE = True
except ImportError:
    Web3 = None  # type: ignore[assignment]
    _WEB3_AVAILABLE = False

# ── reportlab import (optional) ───────────────────────────────────────────────
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    _REPORTLAB_AVAILABLE = True
except ImportError:
    _REPORTLAB_AVAILABLE = False

# ── qrcode import (optional) ─────────────────────────────────────────────────
try:
    import qrcode as _qrcode
    _QRCODE_AVAILABLE = True
except ImportError:
    _QRCODE_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Punto 2: Registro en GaiaChain
# ─────────────────────────────────────────────────────────────────────────────

_FALLBACK_PREFIX = "sim-"


def _sim_hash(lote_id: str, metadata: dict) -> str:
    """Hash determinista de fallback cuando blockchain no está disponible."""
    content = json.dumps({"lote_id": lote_id, "metadata": metadata}, sort_keys=True)
    return _FALLBACK_PREFIX + hashlib.sha256(content.encode()).hexdigest()[:40]


def registrar_en_blockchain(lote_id: str, metadata: dict[str, Any]) -> str:
    """
    Registra los metadatos del lote en GaiaChain via Web3 JSON-RPC.

    Firma una self-transaction con los metadatos codificados en `data`.
    Devuelve el tx_hash real del nodo (0x...) o un hash determinista
    (sim-...) si la clave o el nodo no están disponibles.

    Args:
        lote_id:  Identificador único del lote (ej. "LOTE-20260401-001").
        metadata: Dict con los campos a registrar on-chain.

    Returns:
        str — tx_hash (0x...) o fallback (sim-...).

    Env vars:
        GAIACHAIN_RPC_URL     — URL del nodo JSON-RPC.
        GAIACHAIN_PRIVATE_KEY — Clave privada hex (0x + 64 hex chars).
    """
    private_key = os.getenv("GAIACHAIN_PRIVATE_KEY", "")
    rpc_url     = os.getenv("GAIACHAIN_RPC_URL", "")

    if not private_key or not rpc_url:
        logger.info(
            "GaiaChain no configurado (lote=%s) — usando hash simulado", lote_id
        )
        return _sim_hash(lote_id, metadata)

    if not _WEB3_AVAILABLE or Web3 is None:
        logger.warning("web3 no instalado — usando hash simulado para lote=%s", lote_id)
        return _sim_hash(lote_id, metadata)

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 5}))

        if not w3.is_connected():
            logger.warning("GaiaChain RPC no responde (lote=%s) — usando sim", lote_id)
            return _sim_hash(lote_id, metadata)

        account = w3.eth.account.from_key(private_key)
        payload  = json.dumps({"lote_id": lote_id, **metadata}, sort_keys=True)

        tx = {
            "from":  account.address,
            "to":    account.address,   # self-TX para registrar datos
            "value": 0,
            "gas":   100_000,
            "gasPrice": w3.eth.gas_price,
            "nonce": w3.eth.get_transaction_count(account.address),
            "data":  ("0x" + payload.encode("utf-8").hex()),
        }
        signed = w3.eth.account.sign_transaction(tx, private_key)
        raw_tx = signed.rawTransaction
        tx_hash_bytes = w3.eth.send_raw_transaction(raw_tx)
        tx_hash = w3.to_hex(tx_hash_bytes)

        logger.info("Lote %s registrado en GaiaChain → %s", lote_id, tx_hash)
        return tx_hash

    except Exception as exc:
        logger.warning(
            "Error al registrar lote=%s en GaiaChain: %s — usando sim", lote_id, exc
        )
        return _sim_hash(lote_id, metadata)


# ─────────────────────────────────────────────────────────────────────────────
# Punto 4: Generación de certificado PDF
# ─────────────────────────────────────────────────────────────────────────────

_CASTUO_GREEN  = "#2e7d32"
_CASTUO_LIGHT  = "#e8f5e9"
_CASTUO_DARK   = "#1b5e20"


def generar_pdf(
    lote_id: str,
    tx_hash: str,
    metadata: dict[str, Any],
    output_dir: str | None = None,
) -> str:
    """
    Genera un certificado de trazabilidad en formato PDF.

    Estilo CASTÚO: verde #2e7d32, tabla de metadatos, hash blockchain.
    Fallback a fichero de texto plano con extensión .pdf si reportlab falla.

    Args:
        lote_id:    Identificador del lote.
        tx_hash:    Hash de la transacción blockchain (0x… o sim-…).
        metadata:   Metadatos a incluir en el certificado.
        output_dir: Directorio de salida (default: QR_OUTPUT_DIR o /tmp).

    Returns:
        str — Ruta absoluta al fichero generado.
    """
    out_dir  = Path(output_dir or os.getenv("QR_OUTPUT_DIR", tempfile.gettempdir()))
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"certificado-{lote_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.pdf"
    filepath = str(out_dir / filename)

    if not _REPORTLAB_AVAILABLE:
        logger.warning("reportlab no instalado — generando PDF de texto plano")
        return _generar_pdf_texto(lote_id, tx_hash, metadata, filepath)

    return _generar_pdf_reportlab(lote_id, tx_hash, metadata, filepath)


def _generar_pdf_reportlab(
    lote_id: str, tx_hash: str, metadata: dict[str, Any], filepath: str
) -> str:
    """Genera PDF con reportlab (rich layout A4)."""
    styles = getSampleStyleSheet()
    doc    = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Estilo de título personalizado
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    title_style = ParagraphStyle(
        "CastúoTitle",
        parent=styles["Title"],
        textColor=colors.HexColor(_CASTUO_DARK),
        fontSize=20,
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "CastúoSubtitle",
        parent=styles["Normal"],
        textColor=colors.HexColor(_CASTUO_GREEN),
        fontSize=11,
        spaceAfter=4,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        "CastúoBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=14,
    )

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    story = [
        Paragraph("CASTÚO-SYSTEM™", title_style),
        Paragraph("Certificado de Trazabilidad Agrovoltaica", subtitle_style),
        Spacer(1, 0.4 * cm),
        Paragraph(
            f"<b>Lote ID:</b> {lote_id} &nbsp; | &nbsp; <b>Emisión:</b> {now_str}",
            body_style,
        ),
        Paragraph(
            f"<b>TX Hash:</b> <font size='8'>{tx_hash}</font>",
            body_style,
        ),
        Spacer(1, 0.5 * cm),
        Paragraph("<b>Metadatos del lote</b>", styles["Heading2"]),
        Spacer(1, 0.2 * cm),
    ]

    # Tabla de metadatos
    table_data = [["Campo", "Valor"]] + [
        [str(k), str(v)] for k, v in sorted(metadata.items())
    ]

    if len(table_data) > 1:
        col_widths = [6 * cm, 11 * cm]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor(_CASTUO_GREEN)),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 9),
            ("BACKGROUND",   (0, 1), (-1, -1), colors.HexColor(_CASTUO_LIGHT)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor(_CASTUO_LIGHT)]),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#a5d6a7")),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Documento generado automáticamente por CASTÚO-SYSTEM™ · "
        "Soberanía Europea · RGPD | AI Act UE | eIDAS",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=7,
                       textColor=colors.grey, alignment=TA_CENTER),
    ))

    doc.build(story)
    logger.info("PDF generado: %s", filepath)
    return filepath


def _generar_pdf_texto(
    lote_id: str, tx_hash: str, metadata: dict[str, Any], filepath: str
) -> str:
    """Fallback: fichero de texto plano con extensión .pdf."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "CASTUO-SYSTEM(tm) — Certificado de Trazabilidad",
        "=" * 50,
        f"Lote ID : {lote_id}",
        f"TX Hash : {tx_hash}",
        f"Emision : {now_str}",
        "",
        "Metadatos",
        "-" * 30,
    ]
    for k, v in sorted(metadata.items()):
        lines.append(f"  {k}: {v}")
    lines += ["", "Generado por CASTUO-SYSTEM(tm)"]
    Path(filepath).write_text("\n".join(lines), encoding="utf-8")
    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# Punto 4b: Generación de QR
# ─────────────────────────────────────────────────────────────────────────────

def generar_qr(
    lote_id: str,
    verify_url: str,
    output_dir: str | None = None,
) -> str:
    """
    Genera imagen QR (.png) para el lote.
    Fallback a fichero de texto con URL si qrcode no está instalado.

    Returns:
        str — Ruta absoluta al fichero QR generado.
    """
    out_dir  = Path(output_dir or os.getenv("QR_OUTPUT_DIR", tempfile.gettempdir()))
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"qr-{lote_id}.png"
    filepath = str(out_dir / filename)

    if not _QRCODE_AVAILABLE:
        # Fallback: fichero de texto con la URL
        Path(filepath.replace(".png", ".txt")).write_text(verify_url, encoding="utf-8")
        return filepath.replace(".png", ".txt")

    img = _qrcode.make(verify_url)
    img.save(filepath)
    logger.info("QR generado: %s → %s", lote_id, filepath)
    return filepath


# ─────────────────────────────────────────────────────────────────────────────
# Función principal (respuesta completa)
# ─────────────────────────────────────────────────────────────────────────────

def procesar_lote(
    lote_id: str,
    metadata: dict[str, Any],
    verify_base_url: str = "https://verify.castuo360.eu/lote",
    output_dir: str | None = None,
) -> dict[str, str]:
    """
    Flujo completo: blockchain → PDF certificado → QR.

    Returns:
        dict con claves tx_hash, certificado_path, qr_path.
    """
    tx_hash  = registrar_en_blockchain(lote_id, metadata)
    cert_pdf = generar_pdf(lote_id, tx_hash, metadata, output_dir=output_dir)
    qr_path  = generar_qr(
        lote_id,
        f"{verify_base_url}/{lote_id}",
        output_dir=output_dir,
    )
    return {
        "tx_hash":          tx_hash,
        "certificado_path": cert_pdf,
        "qr_path":          qr_path,
    }
