"""
SABIONDA Skills API — Castúo-System v3.0
Endpoint de validación de lote agrícola con trazabilidad inmutable:
  - Firma digital JWT (HS256) — verificación de operador
  - Registro en GaiaChain 3.0 (con fallback de simulación)
  - Generación de rutas para QR y certificado PDF
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger("castuo.skills")

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

# Leer secreto JWT desde cualquiera de las dos variables de entorno que el
# proyecto define (JWT_SECRET para scripts de usuario, JWT_SECRET_KEY para
# la configuración interna de SABIONDA).
_JWT_SECRET: str = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY", "")
_JWT_ALGORITHM = "HS256"

# URL del nodo GaiaChain (simulación si no está disponible)
_GAIACHAIN_RPC: str = os.getenv("GAIACHAIN_RPC_URL", "")


# ─────────────────────────────────────────────────────────────────────────────
# Modelos
# ─────────────────────────────────────────────────────────────────────────────

class MetadatosLote(BaseModel):
    humedad: Optional[float] = Field(None, description="Humedad relativa (%)")
    thc: Optional[float] = Field(None, description="Contenido THC (%)")
    cbd: Optional[float] = Field(None, description="Contenido CBD (%)")
    fecha_cosecha: Optional[str] = Field(None, description="Fecha de cosecha (YYYY-MM-DD)")
    ubicacion: Optional[str] = Field(None, description="Ubicación de la parcela")

    class Config:
        extra = "allow"


class ValidarLoteRequest(BaseModel):
    lote_id: str = Field(..., description="Identificador único del lote")
    metadatos: MetadatosLote = Field(..., description="Metadatos del lote")
    firma_digital: str = Field(..., description="JWT firmado por el operador")


class ValidarLoteResponse(BaseModel):
    status: str
    lote_id: str
    tx_hash: str = Field(..., description="Hash de transacción en GaiaChain (sim- si es simulado)")
    qr_path: str = Field(..., description="Ruta al archivo QR generado")
    certificado_path: str = Field(..., description="Ruta al certificado PDF generado")
    generado_en: str


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verifica la firma JWT del operador.
    Si JWT_SECRET / JWT_SECRET_KEY no están configurados (entorno de desarrollo)
    se omite la verificación y se devuelve el payload sin validar.
    """
    if not _JWT_SECRET:
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.DecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token JWT malformado: {exc}",
            ) from exc

    try:
        return jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT expirado",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token JWT inválido: {exc}",
        ) from exc


def _compute_lote_hash(lote_id: str, metadatos: Dict[str, Any]) -> str:
    """SHA-256 del lote_id + metadatos — integridad verificable."""
    payload = json.dumps(
        {"lote_id": lote_id, "metadatos": metadatos}, sort_keys=True, default=str
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _register_gaiachain(lote_id: str, content_hash: str) -> str:
    """
    Registra el hash del lote en GaiaChain.
    Si GAIACHAIN_RPC_URL no está configurado o el nodo no está disponible,
    devuelve un tx_hash de simulación con prefijo «sim-».
    """
    if not _GAIACHAIN_RPC:
        sim_hash = hashlib.sha256(f"sim:{lote_id}:{content_hash}".encode()).hexdigest()[:16]
        logger.info("GaiaChain RPC no configurado — simulando tx para lote %s", lote_id)
        return f"sim-{sim_hash}"

    try:
        import httpx  # importación local para no contaminar el módulo si httpx no está
        rpc_payload = {
            "jsonrpc": "2.0",
            "method": "gaiachain_registerHash",
            "params": [lote_id, f"0x{content_hash}"],
            "id": 1,
        }
        private_key = os.getenv("GAIACHAIN_PRIVATE_KEY", "")
        headers: Dict[str, str] = {}
        if private_key:
            headers["X-Private-Key"] = private_key
        with httpx.Client(timeout=10) as client:
            resp = client.post(_GAIACHAIN_RPC, json=rpc_payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            tx_hash = result.get("result", {}).get("tx_hash") or result.get("result")
            if tx_hash:
                return str(tx_hash)
    except (httpx.HTTPError, httpx.TimeoutException, ValueError, KeyError) as exc:
        logger.warning("GaiaChain no disponible, usando simulación: %s", exc)

    sim_hash = hashlib.sha256(f"sim:{lote_id}:{content_hash}".encode()).hexdigest()[:16]
    return f"sim-{sim_hash}"


def _output_paths(lote_id: str) -> tuple[str, str]:
    """Devuelve (qr_path, certificado_path) para un lote."""
    output_dir = os.getenv("OUTPUT_DIR", "/tmp/castuo/output")
    safe_id = lote_id.replace("/", "_").replace(" ", "_")
    qr_path = f"{output_dir}/qr/{safe_id}.png"
    cert_path = f"{output_dir}/certificados/{safe_id}.pdf"
    return qr_path, cert_path


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/validar_lote",
    response_model=ValidarLoteResponse,
    summary="Validar y registrar lote agrícola en GaiaChain",
    description=(
        "Valida la firma digital del operador (JWT HS256), registra el hash "
        "del lote en GaiaChain 3.0 y devuelve las rutas del QR y certificado PDF."
    ),
)
async def validar_lote(
    request: ValidarLoteRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> ValidarLoteResponse:
    """
    Flujo:
    1. Verificar JWT (desde Authorization header o campo firma_digital)
    2. Calcular hash SHA-256 del lote
    3. Registrar en GaiaChain (con fallback de simulación)
    4. Retornar rutas de QR y certificado
    """
    # Determinar token: header tiene precedencia sobre el campo del body
    token: str
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
    else:
        token = request.firma_digital

    _verify_jwt(token)

    metadatos_dict = request.metadatos.model_dump(exclude_none=True)
    content_hash = _compute_lote_hash(request.lote_id, metadatos_dict)
    tx_hash = _register_gaiachain(request.lote_id, content_hash)
    qr_path, cert_path = _output_paths(request.lote_id)
    now = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Lote validado: id=%s tx=%s hash=%s",
        request.lote_id,
        tx_hash,
        content_hash[:16],
    )

    return ValidarLoteResponse(
        status="OK",
        lote_id=request.lote_id,
        tx_hash=tx_hash,
        qr_path=qr_path,
        certificado_path=cert_path,
        generado_en=now,
    )
