# -*- coding: utf-8 -*-
"""Microservicio Cannabis: trazabilidad y certificación AEMPS (CTAEX)."""
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AEMPSCertificationRequest(BaseModel):
    batch_id: str
    strain_id: str
    thc_percentage: float
    cbd_percentage: float
    lab_results: dict


@router.post("/certify_aemps")
async def certify_with_aemps(request: AEMPSCertificationRequest):
    """Solicita certificación AEMPS para un lote de cannabis (integración CTAEX)."""
    try:
        if request.thc_percentage > 0.3:
            raise HTTPException(
                status_code=400,
                detail="THC exceeds legal limit (RD 903/2025). Max 0.3%.",
            )
        aemps_data: Dict[str, Any] = {
            "batch_id": request.batch_id,
            "strain": request.strain_id,
            "thc": request.thc_percentage,
            "cbd": request.cbd_percentage,
            "lab_results": request.lab_results,
            "timestamp": datetime.now().isoformat(),
        }
        # En producción: llamada real a la API de AEMPS
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.aemps.gob.es/cannabis/certify",
        #         json=aemps_data,
        #         headers={"Authorization": f"Bearer {os.getenv('AEMPS_API_KEY')}"},
        #     )
        #     response.raise_for_status()
        #     return response.json()
        return {
            "status": "pending",
            "certification_id": f"AEM-{request.batch_id}-{datetime.now().strftime('%Y%m%d')}",
            "estimated_completion": "72 hours",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"AEMPS certification failed: {str(e)}"
        )
