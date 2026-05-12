# -*- coding: utf-8 -*-
"""Generación de documentos de exportación para Canadá."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict


class CanadaExportDocuments:
    """Genera documentos de exportación para Canadá."""

    def generate_health_canada_license(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera una licencia de Health Canada para cannabis."""
        doc_id = f"HC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "batch_id": batch_data.get("batch_id", ""),
            "document_type": "Health_Canada_License",
            "country_destination": "CA",
            "issued_by": "Health Canada",
            "issue_date": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "status": "active",
            "blockchain_tx": f"tx_{uuid.uuid4().hex[:16]}_health_canada",
            "qr_code": f"https://certificates.castu.system/health-canada/{uuid.uuid4().hex[:16]}",
            "license_details": {
                "license_number": f"HC-L-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6]}",
                "license_type": "Cultivation, Processing, Sale",
                "authorized_activities": ["Indoor cultivation", "Extraction", "Packaging"],
                "site_address": batch_data.get("site_address", "CTAEX, Badajoz, Spain"),
            },
            "compliance": {
                "thc_limit": batch_data.get("thc", 0.0) <= 0.3,
                "traceability": batch_data.get("blockchain_tx") is not None,
                "packaging": batch_data.get("child_resistant_packaging", False),
            },
            "canadian_requirements": {
                "excise_stamp": "Required for all cannabis products",
                "cannabis_tracking_system": "Must be reported to CTLS",
                "import_permit": "Required for international shipments",
            },
        }

    def generate_canada_organic_certificate(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un certificado orgánico para Canadá."""
        doc_id = f"COC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "batch_id": batch_data.get("batch_id", ""),
            "document_type": "Canada_Organic_Certificate",
            "country_destination": "CA",
            "issued_by": "CFIA (Canadian Food Inspection Agency)",
            "issue_date": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "status": "certified",
            "blockchain_tx": f"tx_{uuid.uuid4().hex[:16]}_canada_organic",
            "qr_code": f"https://certificates.castu.system/canada-organic/{uuid.uuid4().hex[:16]}",
            "certification_details": {
                "certification_body": "Ecocert Canada",
                "certification_number": f"CO-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6]}",
                "certified_products": batch_data.get("products", ["Microgreens", "Cannabis"]),
                "certification_scope": "Production, Processing, Handling",
            },
            "compliance": {
                "no_synthetic_inputs": batch_data.get("no_synthetic_inputs", False),
                "crop_rotation": batch_data.get("crop_rotation", False),
                "buffer_zones": batch_data.get("buffer_zones", False),
            },
            "canadian_requirements": {
                "organic_logo": "Must display Canada Organic logo on packaging",
                "import_notification": "Required 30 days prior to shipment",
                "customs_documentation": "Phytosanitary certificate and invoice required",
            },
        }

    def generate_sfcr_compliance_document(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un documento de cumplimiento con SFCR para microgreens."""
        doc_id = f"SFCR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "batch_id": batch_data.get("batch_id", ""),
            "document_type": "SFCR_Compliance_Document",
            "country_destination": "CA",
            "issued_by": "CTAEX (SFCR Compliant)",
            "issue_date": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "status": "compliant",
            "blockchain_tx": f"tx_{uuid.uuid4().hex[:16]}_sfcr",
            "qr_code": f"https://certificates.castu.system/sfcr/{uuid.uuid4().hex[:16]}",
            "compliance_details": {
                "preventive_control_plan": f"PCP-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6]}",
                "hazard_analysis": "Conducted for biological, chemical, and physical hazards",
                "traceability_system": "Blockchain-based traceability implemented",
                "sanitation_program": "Daily cleaning and disinfection procedures",
            },
            "sfcr_requirements": {
                "license_number": f"SFCR-L-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6]}",
                "inspection_frequency": "Annual unannounced inspections",
                "record_retention": "2 years for all production and distribution records",
            },
        }
