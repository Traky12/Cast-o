# -*- coding: utf-8 -*-
"""Microservicio Microgreens: certificación GlobalGAP e integración CTAEX."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

try:
    from backend.services.certification import generate_certificate
    _HAS_CERT = True
except ImportError:
    _HAS_CERT = False

router = APIRouter()


@router.post("/certify_globalgap")
async def certify_globalgap(batch_data: Dict[str, Any]):
    """Genera certificado GlobalGAP (PDF + QR) para un lote de microgreens."""
    try:
        if not _HAS_CERT:
            raise HTTPException(
                status_code=503,
                detail="Certification service unavailable (install reportlab, qrcode[pil])",
            )
        cert_path = generate_certificate(
            batch_data["batch_id"],
            batch_data.get("variety", batch_data.get("strain", "N/A")),
            batch_data.get("thc", 0.0),
            batch_data.get("cbd", 0.0),
            batch_data.get("lab_results", {}),
        )
        return {
            "status": "success",
            "certificate_path": cert_path,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
