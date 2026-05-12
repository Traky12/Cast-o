"""
Skills Router — CASTÚO-SYSTEM™ v3.1
POST /api/v1/skills/validar_lote  — Registro blockchain + QR + PDF en un solo paso.

Flujo:
  1. Validar payload
  2. registrar_en_blockchain() → tx_hash (0x real o sim-* fallback)
  3. generar_pdf()             → certificado_path
  4. generar_qr()              → qr_path
  5. Devolver {status, tx_hash, qr_path, certificado_path}

Autenticación: Bearer JWT (HS256) via cabecera Authorization.
  Secreto: JWT_SECRET env (Opción B) o JWT_SECRET_FILE (Opción A).
  Rol mínimo requerido: editor | admin.
  Sin autenticación configurada: endpoint operativo en modo dev (advertencia en log).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import jwt as _jwt
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

# Asegurar que castuo_graph está en el path para importar skills
_CG = Path(__file__).parent.parent.parent / "castuo_graph"
if str(_CG) not in sys.path:
    sys.path.insert(0, str(_CG))

from skills import generar_pdf, generar_qr, registrar_en_blockchain  # noqa: E402

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

# ── JWT auth (opcional en dev) ─────────────────────────────────────────────────

_ALLOWED_ROLES = {"admin", "editor", "api"}


def _read_jwt_secret() -> str:
    file_path = os.getenv("JWT_SECRET_FILE", "")
    if file_path:
        try:
            return Path(file_path).read_text().strip()
        except OSError:
            return ""
    return os.getenv("JWT_SECRET", "")


def _verify_bearer(authorization: str = Header(default="", alias="Authorization")) -> dict:
    """Valida JWT HS256. En dev (sin JWT_SECRET) solo advierte."""
    secret = _read_jwt_secret()

    if not secret:
        logger.warning("JWT_SECRET no configurado — endpoint skills en modo dev (sin auth)")
        return {"sub": "dev", "role": "admin"}

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cabecera Authorization: Bearer <jwt> requerida",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = _jwt.decode(token, secret, algorithms=["HS256"])
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token JWT expirado")
    except _jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    role = payload.get("role", "")
    if role not in _ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Rol '{role}' no autorizado. Válidos: {sorted(_ALLOWED_ROLES)}",
        )
    return payload


# ── Modelos ───────────────────────────────────────────────────────────────────

class ValidarLoteRequest(BaseModel):
    lote_id: str = Field(..., min_length=3, max_length=120,
                         description="Identificador único del lote")
    metadatos: dict[str, Any] = Field(default_factory=dict,
                                      description="Datos del lote a registrar on-chain")
    firma_digital: Optional[str] = Field(
        default=None,
        description="JWT del operador (opcional — se incluye en los metadatos del certificado)"
    )
    verify_base_url: str = Field(
        default="https://verify.castuo360.eu/lote",
        description="Base URL para el QR de verificación"
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Directorio de salida para QR y PDF (default: QR_OUTPUT_DIR o /tmp)"
    )


class ValidarLoteResponse(BaseModel):
    status: str                 # "OK" | "FALLBACK"
    lote_id: str
    tx_hash: str                # 0x… (real) o sim-… (fallback)
    blockchain: str             # "GaiaChain" | "simulado"
    certificado_path: str
    qr_path: str
    generado_en: str


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "/validar_lote",
    response_model=ValidarLoteResponse,
    summary="Registrar lote en blockchain + generar QR y certificado PDF",
)
async def validar_lote(
    req: ValidarLoteRequest,
    _token: dict = Depends(_verify_bearer),
) -> ValidarLoteResponse:
    """
    Flujo completo de validación de lote:

    1. Registra los metadatos en GaiaChain (Web3 real o sim-* fallback).
    2. Genera certificado PDF A4 con reportlab.
    3. Genera imagen QR que enlaza a la URL de verificación pública.

    Devuelve las rutas de los archivos generados y el tx_hash blockchain.
    """
    lote_id  = req.lote_id.strip()
    metadata = {**req.metadatos}

    # Enriquecer metadatos con contexto de la petición
    metadata["_operador_sub"] = _token.get("sub", "unknown")
    metadata["_validado_en"]  = datetime.now(timezone.utc).isoformat()

    tx_hash = registrar_en_blockchain(lote_id, metadata)

    out_dir = req.output_dir or os.getenv("QR_OUTPUT_DIR", "/tmp")

    cert_path = generar_pdf(
        lote_id=lote_id,
        tx_hash=tx_hash,
        metadata=metadata,
        output_dir=out_dir,
    )
    qr_path = generar_qr(
        lote_id=lote_id,
        verify_url=f"{req.verify_base_url}/{lote_id}",
        output_dir=out_dir,
    )

    is_real = tx_hash.startswith("0x")
    logger.info(
        "Lote %s validado | tx=%s | pdf=%s | qr=%s",
        lote_id, tx_hash[:16], cert_path, qr_path,
    )

    return ValidarLoteResponse(
        status="OK" if is_real else "FALLBACK",
        lote_id=lote_id,
        tx_hash=tx_hash,
        blockchain="GaiaChain" if is_real else "simulado",
        certificado_path=cert_path,
        qr_path=qr_path,
        generado_en=datetime.now(timezone.utc).isoformat(),
    )
