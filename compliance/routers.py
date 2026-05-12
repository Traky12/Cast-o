# -*- coding: utf-8 -*-
"""Routers FastAPI para certificación (producto y exportación)."""
import os

from fastapi import APIRouter, Depends, HTTPException

from compliance.certification_manager import CertificationManager

try:
    # Certificacion soberana (GaiaChain tx) para alias publico sobre /api/certificates/verify/{tx_hash}
    from backend.main_certifier import MainCertifier
except Exception:  # pragma: no cover
    MainCertifier = None  # type: ignore

try:
    from blockchain.gaia_chain import GaiaChainClient
except ImportError:
    GaiaChainClient = None  # type: ignore


def get_gaiachain():
    """Dependencia GaiaChain."""
    if GaiaChainClient is None:
        return None
    return GaiaChainClient(rpc_url=os.getenv("GAIA_CHAIN_RPC_URL", ""))


def get_certification_manager(gaiachain=Depends(get_gaiachain)):
    return CertificationManager(gaiachain)


certification_router = APIRouter()

_main_certifier = None
if MainCertifier is not None:
    try:
        _main_certifier = MainCertifier()
    except Exception:
        _main_certifier = None


def _looks_like_gaia_tx(value: str) -> bool:
    """Heuristica para detectar TXID GaiaChain o tx locales de fallback final_certificate."""
    if not value:
        return False
    v = value.strip()
    if v.startswith("0x"):
        return True
    if v.startswith("local-fallback-"):
        return True
    if "final_certificate" in v:
        return True
    return False


@certification_router.post("/product", summary="Generar certificado de producto")
async def generate_product_certificate(
    batch_id: str,
    product_type: str,
    variety: str,
    manager: CertificationManager = Depends(get_certification_manager),
):
    """Genera un certificado de calidad para un producto (microgreens, cannabis, etc.)."""
    result = manager.generate_product_certificate(batch_id, product_type, variety)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@certification_router.post("/export", summary="Generar certificado de exportación")
async def generate_export_certificate(
    product_cert_id: str,
    destination_country: str,
    importer: str,
    manager: CertificationManager = Depends(get_certification_manager),
):
    """Genera un certificado de exportación (fitosanitario)."""
    result = manager.generate_export_certificate(product_cert_id, destination_country, importer)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Error"))
    return result


@certification_router.get("/verify/{certificate_id}", summary="Verificar certificado")
async def verify_certificate(
    certificate_id: str,
    manager: CertificationManager = Depends(get_certification_manager),
):
    """Verifica la autenticidad de un certificado."""
    # Caso 1: alias para TXID GaiaChain (soberano)
    if _main_certifier is not None and _looks_like_gaia_tx(certificate_id):
        status = _main_certifier.get_certificate_status(certificate_id)
        if not status.get("valid"):
            raise HTTPException(status_code=404, detail=status.get("error", "Certificado no encontrado"))
        data = status.get("data", {}) or {}
        verification_url = f"https://gaiachain.castuo-system.com/verify/{certificate_id}"
        return {
            "status": "success",
            "certificate": {
                "tx_id": certificate_id,
                "certificate_id": data.get("lote_id") or data.get("certificate_id") or certificate_id,
                "certificate_hash": data.get("certificate_hash") or data.get("pdf_hash") or "",
                "timestamp": data.get("timestamp"),
                "legal_seals": data.get("legal_seals", {}),
                "certificate_data": data.get("certificate_data", {}),
            },
            "source": "gaiachain",
            "verification_url": verification_url,
        }

    # Caso 2: verificacion CTAEX/quality export (compliance)
    result = manager.verify_certificate(certificate_id)
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", "No encontrado"))
    return result
