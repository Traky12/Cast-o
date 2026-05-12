# -*- coding: utf-8 -*-
"""Enlace con GlobalGAP — certificaciones internacionales para exportación."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel


class GlobalGAPCertificationRequest(BaseModel):
    """Solicitud de certificación GlobalGAP."""

    batch_id: str
    variety: str
    grower_id: str
    environmental_data: dict = {}
    lab_results: Optional[dict] = None


class GlobalGAPService:
    """Cliente para la API de certificaciones GlobalGAP."""

    def __init__(self) -> None:
        self.api_key = os.getenv("GLOBALGAP_API_KEY", "")
        self.base_url = os.getenv(
            "GLOBALGAP_BASE_URL",
            "https://api.globalgap.org/v1",
        )

    async def submit_for_certification(
        self,
        request: GlobalGAPCertificationRequest,
    ) -> Dict[str, Any]:
        """Envía datos para certificación GlobalGAP."""
        payload = {
            "batch": request.batch_id,
            "producer": request.grower_id,
            "product": request.variety,
            "environmental": request.environmental_data,
            "lab": request.lab_results or {},
        }
        if not self.api_key:
            return {
                "status": "pending",
                "message": "GLOBALGAP_API_KEY no configurado (modo simulación)",
                "batch_id": request.batch_id,
            }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/certifications",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()
