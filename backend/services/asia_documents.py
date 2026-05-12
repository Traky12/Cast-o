# -*- coding: utf-8 -*-
"""Generación de documentos de exportación para mercados asiáticos."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict


class AsiaExportDocuments:
    """Genera documentos de exportación para mercados asiáticos."""

    def generate_jas_certificate(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera certificado JAS Organic para Japón."""
        doc_id = f"JAS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "batch_id": batch_data.get("batch_id", ""),
            "document_type": "JAS_Organic_Certificate",
            "country_destination": "JP",
            "issued_by": "CTAEX (EU Organic Certified)",
            "issue_date": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "status": "issued",
            "blockchain_tx": f"tx_{uuid.uuid4().hex[:16]}_jas",
            "qr_code": f"https://certificates.castu.system/jas/{uuid.uuid4().hex[:16]}",
            "compliance": {
                "pesticide_free": batch_data.get("pesticide_free", False),
                "chemical_fertilizer_free": batch_data.get("chemical_fertilizer_free", False),
                "soil_management_plan": batch_data.get("soil_management_plan", False),
            },
            "japanese_requirements": {
                "maff_registration_number": f"MAFF-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6]}",
                "import_notification": "Required 30 days prior to shipment",
                "radiation_inspection": "Mandatory for all agricultural imports",
            },
        }

    def generate_kfda_import_permit(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera permiso de importación del KFDA (Corea)."""
        doc_id = f"KFDA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "batch_id": batch_data.get("batch_id", ""),
            "document_type": "KFDA_Import_Permit",
            "country_destination": "KR",
            "issued_by": "Korea Food & Drug Administration",
            "issue_date": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(days=180)).isoformat(),
            "status": "approved",
            "blockchain_tx": f"tx_{uuid.uuid4().hex[:16]}_kfda",
            "qr_code": f"https://certificates.castu.system/kfda/{uuid.uuid4().hex[:16]}",
            "permit_details": {
                "importer_name": batch_data.get("importer_name", "Unknown"),
                "importer_address": batch_data.get("importer_address", ""),
                "product_description": batch_data.get("product_description", ""),
                "quantity": batch_data.get("quantity", 0),
                "thc_content": batch_data.get("thc", 0.0),
                "cbd_content": batch_data.get("cbd", 0.0),
            },
            "kfda_requirements": {
                "quarantine_inspection": "Mandatory at Incheon Airport",
                "customs_clearance": "Required prior to distribution",
                "storage_conditions": "Temperature-controlled (2-8°C)",
            },
        }

    def generate_plaook_gan_registration(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera registro en el sistema Plaook Gan (Tailandia)."""
        doc_id = f"PG-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        return {
            "document_id": doc_id,
            "batch_id": batch_data.get("batch_id", ""),
            "document_type": "Plaook_Gan_Registration",
            "country_destination": "TH",
            "issued_by": "Thai Food and Drug Administration",
            "issue_date": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(days=365)).isoformat(),
            "status": "registered",
            "blockchain_tx": f"tx_{uuid.uuid4().hex[:16]}_plaookgan",
            "qr_code": f"https://certificates.castu.system/plaookgan/{uuid.uuid4().hex[:16]}",
            "registration_details": {
                "cultivation_site": batch_data.get("cultivation_site", ""),
                "strain": batch_data.get("strain", ""),
                "thc_content": batch_data.get("thc", 0.0),
                "cbd_content": batch_data.get("cbd", 0.0),
                "gap_certification_number": f"GAP-TH-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6]}",
            },
            "thai_requirements": {
                "pre_shipment_inspection": "Required by Department of Agriculture",
                "fumigation_certificate": "Mandatory for all plant imports",
                "import_duty": "0% for organic products, 5% for processed products",
            },
        }
