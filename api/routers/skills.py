from __future__ import annotations

import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from api.security.rbac import authorize_token, token_from_authorization_header

try:
    from web3 import Web3  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    Web3 = None  # type: ignore[assignment,misc]

try:
    import qrcode  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    qrcode = None  # type: ignore[assignment]

try:
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle
except ImportError:  # pragma: no cover
    colors = None  # type: ignore[assignment]
    A4 = None  # type: ignore[assignment]
    getSampleStyleSheet = None  # type: ignore[assignment]
    Paragraph = None  # type: ignore[assignment]
    SimpleDocTemplate = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    TableStyle = None  # type: ignore[assignment]

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

logger = logging.getLogger(__name__)

GAIACHAIN_URL = os.getenv("GAIACHAIN_RPC_URL", "http://localhost:8545")
DEFAULT_TMP_DIR = "/tmp"
w3 = (
    Web3(Web3.HTTPProvider(GAIACHAIN_URL, request_kwargs={"timeout": 5}))
    if Web3 is not None
    else None
)

# Minimal valid 1x1 PNG used as fallback when qrcode is unavailable.
PNG_FALLBACK = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/ce6f6YAAAAASUVORK5CYII="
)


class LoteData(BaseModel):
    lote_id: str
    metadatos: dict[str, Any]
    firma_digital: str | None = None


class ValidarLoteResponse(BaseModel):
    status: str
    tx_hash: str
    qr_path: str
    certificado_path: str


def _sim_tx_hash(lote_id: str) -> str:
    return f"sim-{lote_id}-{int(datetime.now().timestamp())}"


def _resolve_sender_address(private_key: str) -> str | None:
    if w3 is None:
        return None
    default_account = getattr(w3.eth, "default_account", None)
    if default_account:
        return default_account
    try:
        account = w3.eth.account.from_key(private_key)
    except Exception:
        return None
    w3.eth.default_account = account.address
    return account.address


def registrar_en_blockchain(lote_id: str, metadatos: dict[str, Any]) -> str:
    """Registra metadatos en GaiaChain con fallback simulado si falla Web3."""
    private_key = os.getenv("GAIACHAIN_PRIVATE_KEY")
    if not private_key or w3 is None:
        return _sim_tx_hash(lote_id)

    try:
        if not w3.is_connected():
            raise ConnectionError("No se pudo conectar a GaiaChain")

        sender_address = _resolve_sender_address(private_key)
        if not sender_address:
            raise ValueError("No se pudo resolver la cuenta firmante")

        data_bytes = json.dumps(metadatos).encode("utf-8")

        tx = {
            "from": sender_address,
            "to": sender_address,
            "value": 0,
            "nonce": w3.eth.get_transaction_count(cast(Any, sender_address)),
            "gas": 2_000_000,
            "gasPrice": w3.to_wei("50", "gwei"),
            "data": data_bytes,
        }

        chain_id = getattr(w3.eth, "chain_id", None)
        if chain_id is not None:
            tx["chainId"] = chain_id

        signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
        raw_transaction = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction")
        raw_tx_hash: bytes = w3.eth.send_raw_transaction(raw_transaction)
        tx_hash_hex = raw_tx_hash.hex()
        return tx_hash_hex if tx_hash_hex.startswith("0x") else f"0x{tx_hash_hex}"
    except Exception as exc:
        logger.warning("Fallback GaiaChain para lote %s: %s", lote_id, exc)
        return _sim_tx_hash(lote_id)


def _tmp_dir() -> Path:
    base_dir = Path(os.getenv("SKILLS_TMP_DIR", DEFAULT_TMP_DIR))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _qr_target_path(lote_id: str) -> Path:
    return _tmp_dir() / f"{lote_id}.png"


def _pdf_target_path(lote_id: str) -> Path:
    return _tmp_dir() / f"{lote_id}.pdf"


def generar_qr(lote_id: str, tx_hash: str) -> str:
    qr_url = f"https://castuo-system.cloud/lotes/{lote_id}?tx={tx_hash}"
    output_path = _qr_target_path(lote_id)

    try:
        if qrcode is None:
            raise RuntimeError("qrcode no disponible")
        qr_img = qrcode.make(qr_url)
        cast(Any, qr_img).save(str(output_path))
    except Exception:
        output_path.write_bytes(PNG_FALLBACK)

    return str(output_path)


def generar_pdf(
    lote_id: str,
    metadatos: dict[str, Any],
    tx_hash: str,
    output_path: str | Path | None = None,
) -> str:
    """Genera certificado PDF con reportlab y fallback a texto plano."""
    target_path = Path(output_path) if output_path is not None else _pdf_target_path(lote_id)
    fecha_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        if None in (SimpleDocTemplate, A4, getSampleStyleSheet, Paragraph, Table, TableStyle, colors):
            raise RuntimeError("reportlab no disponible")

        simple_doc_template = cast(Any, SimpleDocTemplate)
        page_size = cast(Any, A4)
        sample_style_sheet = cast(Any, getSampleStyleSheet)
        paragraph = cast(Any, Paragraph)
        table_cls = cast(Any, Table)
        table_style_cls = cast(Any, TableStyle)
        reportlab_colors = cast(Any, colors)

        doc = simple_doc_template(str(target_path), pagesize=page_size)
        styles = sample_style_sheet()
        elements: list[Any] = []

        elements.append(paragraph(f"Certificado de Trazabilidad - Lote {lote_id}", styles["Title"]))

        table_data: list[list[str]] = [["Clave", "Valor"]] + [
            [str(key), str(value)] for key, value in metadatos.items()
        ]
        table = table_cls(table_data)
        table.setStyle(
            table_style_cls([
                ("BACKGROUND", (0, 0), (-1, 0), reportlab_colors.green),
                ("TEXTCOLOR", (0, 0), (-1, 0), reportlab_colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), reportlab_colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, reportlab_colors.black),
            ])
        )
        elements.append(table)
        elements.append(paragraph(f"TX Hash: {tx_hash}", styles["Normal"]))
        elements.append(paragraph(f"Fecha: {fecha_utc}", styles["Normal"]))

        doc.build(elements)
    except Exception as exc:
        logger.warning("Fallback PDF para lote %s: %s", lote_id, exc)
        target_path.write_text(
            f"Certificado para Lote {lote_id}\nTX Hash: {tx_hash}\nMetadatos: {metadatos}"
        )

    return str(target_path)


@router.post("/validar_lote", response_model=ValidarLoteResponse)
async def validar_lote(
    data: LoteData,
    authorization: str | None = Header(default=None),
) -> ValidarLoteResponse:
    token = data.firma_digital or token_from_authorization_header(authorization)

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma invalida")

    try:
        authorize_token(
            token,
            required_roles={"admin_general", "administrador", "tecnico", "usuario", "comercial", "api"},
        )
    except HTTPException as exc:
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rol no autorizado") from exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma invalida") from exc

    tx_hash = registrar_en_blockchain(data.lote_id, data.metadatos)
    qr_path = generar_qr(data.lote_id, tx_hash)
    certificado_path = generar_pdf(data.lote_id, data.metadatos, tx_hash)

    return ValidarLoteResponse(
        status="OK",
        tx_hash=tx_hash,
        qr_path=qr_path,
        certificado_path=certificado_path,
    )
