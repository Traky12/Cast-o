# -*- coding: utf-8 -*-
"""API de cumplimiento y logística para Canadá (Health Canada, GPP, SFCR)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.models.pro_account import ProUserProfile
from backend.routers.pro_accounts import get_current_user
from backend.services.canada_validation import CanadaComplianceValidator
from backend.services.canada_documents import CanadaExportDocuments
from backend.services.canada_logistics import CanadaLogisticsService

# Cargar reglas de país (CA)
import backend.models.canada_compliance  # noqa: F401

router = APIRouter(prefix="/international/canada", tags=["International - Canada"])

canada_validator = CanadaComplianceValidator()
canada_documents = CanadaExportDocuments()
canada_logistics = CanadaLogisticsService()


@router.post("/validate/health-canada")
async def validate_health_canada(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de cannabis según Health Canada."""
    return canada_validator.validate_health_canada(batch_data)


@router.post("/validate/canada-organic")
async def validate_canada_organic(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote según Canada Organic Regime."""
    return canada_validator.validate_canada_organic(batch_data)


@router.post("/validate/sfcr")
async def validate_sfcr(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Valida un lote de microgreens según SFCR."""
    return canada_validator.validate_sfcr(batch_data)


@router.post("/documents/health-canada-license")
async def generate_health_canada_license(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera una licencia de Health Canada para cannabis."""
    return canada_documents.generate_health_canada_license(batch_data)


@router.post("/documents/canada-organic")
async def generate_canada_organic_certificate(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un certificado orgánico para Canadá."""
    return canada_documents.generate_canada_organic_certificate(batch_data)


@router.post("/documents/sfcr-compliance")
async def generate_sfcr_document(
    batch_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Genera un documento de cumplimiento con SFCR para microgreens."""
    return canada_documents.generate_sfcr_compliance_document(batch_data)


@router.post("/logistics/{carrier}/shipment")
async def create_canada_shipment(
    carrier: str,
    shipment_data: Dict[str, Any],
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Crea un envío con un transportista canadiense (canada_post, purolator, fedex_ca)."""
    try:
        return canada_logistics.create_shipment(carrier, shipment_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logistics/{carrier}/tracking")
async def track_canada_shipment(
    carrier: str,
    tracking_number: str,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Rastrea un envío con un transportista canadiense."""
    try:
        return canada_logistics.track_shipment(carrier, tracking_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/logistics/{carrier}/rates")
async def get_canada_shipping_rates(
    carrier: str,
    origin: str = "ES",
    destination: str = "CA",
    weight: float = 1.0,
    is_cannabis: bool = False,
    current_user: ProUserProfile = Depends(get_current_user),
) -> Dict[str, Any]:
    """Obtiene tarifas de envío para transportistas canadienses."""
    try:
        return canada_logistics.get_shipping_rates(
            carrier, origin, destination, weight, is_cannabis
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
