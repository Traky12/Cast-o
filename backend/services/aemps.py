# -*- coding: utf-8 -*-
"""Enlace con AEMPS (Agencia Española de Medicamentos) — certificaciones cannabis medicinal."""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from pydantic import BaseModel


class AEMPSCertificationRequest(BaseModel):
    """Solicitud de certificación AEMPS."""

    batch_id: str
    strain: str
    thc: float
    cbd: float
    lab_results: dict = {}
    grower_id: str = ""


class AEMPSService:
    """Cliente para la API oficial de certificaciones AEMPS."""

    def __init__(self) -> None:
        self.api_key = os.getenv("AEMPS_API_KEY", "")
        self.base_url = os.getenv(
            "AEMPS_BASE_URL",
            "https://api.aemps.gob.es/v2/cannabis",
        )

    async def request_certification(
        self,
        request: AEMPSCertificationRequest,
    ) -> Dict[str, Any]:
        """Envía una solicitud de certificación a la API de AEMPS."""
        if not self.api_key:
            return {
                "status": "pending",
                "message": "AEMPS_API_KEY no configurado (modo simulación)",
                "certification_id": f"AEM-{request.batch_id}",
            }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/certify",
                json=request.model_dump(),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    async def check_status(self, certification_id: str) -> Dict[str, Any]:
        """Consulta el estado de una certificación."""
        if not self.api_key:
            return {
                "certification_id": certification_id,
                "status": "unknown",
                "message": "AEMPS_API_KEY no configurado",
            }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/certifications/{certification_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            return response.json()
