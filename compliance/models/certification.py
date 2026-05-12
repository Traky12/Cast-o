# -*- coding: utf-8 -*-
"""Modelos para certificados de calidad y exportación (CTAEX, AEMPS)."""
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class QualityParameter(BaseModel):
    """Parámetro de calidad medido."""
    name: str
    value: str
    limit: Optional[str] = None
    method: str
    lab: str


class CertificationStandard(BaseModel):
    """Estándar de certificación aplicado."""
    name: str
    code: str
    scope: str
    issued_by: str
    valid_until: date


class ProductCertificate(BaseModel):
    """Certificado de calidad para un producto."""
    certificate_id: str
    product_type: str
    variety: str
    batch_id: str
    issue_date: datetime
    expiration_date: datetime
    producer: str
    production_site: str
    quality_parameters: List[QualityParameter]
    standards: List[CertificationStandard]
    gaiachain_tx: str = ""
    qr_code: Optional[str] = None
    pdf_url: Optional[str] = None


class ExportCertificate(BaseModel):
    """Certificado de exportación (fitosanitario)."""
    certificate_id: str
    product_certificate_id: str
    destination_country: str
    importer: str
    phytosanitary_requirements: List[str]
    treatment_applied: List[str]
    issue_date: datetime
    expiration_date: datetime
    gaiachain_tx: str = ""
    customs_code: Optional[str] = None
