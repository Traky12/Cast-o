# -*- coding: utf-8 -*-
"""API de cumplimiento y logística para mercados asiáticos (Japón, Corea, Tailandia)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.models.pro_account import ProUserProfile
from backend.routers.pro_accounts import get_current_user
from backend.services.asia_validation import AsiaComplianceValidator
from backend.services.asia_documents import AsiaExportDocuments
from backend.services.asia_logistics import AsiaLogisticsService

# Cargar reglas de país (JP, KR, TH)
import backend.models.asia_compliance  # noqa: F401

router = APIRouter(prefix="/international/asia", tags=["International - Asia"])

asia_validator = AsiaComplianceValidator()
asia_documents = AsiaExportDocuments()
asia_logistics = AsiaLogisticsService()


@router.post("/validate/jas-organic")
async def validate_jas_organic(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de microgreens según JAS Organic (Japón)."""
    return asia_validator.validate_jas_organic(batch_data)


@router.post("/validate/jp-gmp")
async def validate_jp_gmp(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de cannabis según JP GMP."""
    return asia_validator.validate_jp_gmp(batch_data)


@router.post("/validate/kr-kfda")
async def validate_kr_kfda(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote según normativas del KFDA (Corea)."""
    return asia_validator.validate_kr_kfda(batch_data)


@router.post("/validate/thai-fda")
async def validate_thai_fda(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de cannabis según Thai FDA."""
    return asia_validator.validate_thai_fda(batch_data)


@router.post("/documents/jas-certificate")
async def generate_jas_certificate(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un certificado JAS Organic para exportación a Japón."""
    return asia_documents.generate_jas_certificate(batch_data)


@router.post("/documents/kfda-permit")
async def generate_kfda_permit(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un permiso de importación del KFDA para Corea."""
    return asia_documents.generate_kfda_import_permit(batch_data)


@router.post("/documents/plaook-gan")
async def generate_plaook_gan_registration(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un registro en el sistema Plaook Gan para Tailandia."""
    return asia_documents.generate_plaook_gan_registration(batch_data)


@router.post("/logistics/{carrier}/shipment")
async def create_asia_shipment(
    carrier: str,
    shipment_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Crea un envío con un transportista asiático (yamato, cj, kerry)."""
    try:
        return asia_logistics.create_shipment(carrier, shipment_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logistics/{carrier}/tracking")
async def track_asia_shipment(
    carrier: str,
    tracking_number: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Rastrea un envío con un transportista asiático."""
    try:
        return asia_logistics.track_shipment(carrier, tracking_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logistics/{carrier}/rates")
async def get_asia_shipping_rates(
    carrier: str,
    origin: str = "ES",
    destination: str = "JP",
    weight: float = 1.0,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Obtiene tarifas de envío para transportistas asiáticos."""
    try:
        return asia_logistics.get_shipping_rates(carrier, origin, destination, weight)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
