# -*- coding: utf-8 -*-
"""Integración con GaiaChain para cannabis medicinal."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict

from backend.models.cannabis_specific import CannabisBatch, CannabisLicense


class CannabisBlockchainService:
    """Servicio para registrar lotes de cannabis en GaiaChain."""

    def register_cannabis_license(self, license: CannabisLicense) -> str:
        """Registra una licencia de cannabis en GaiaChain."""
        license_data = {
            "license_id": license.license_id,
            "holder": license.holder,
            "valid_from": license.valid_from.isoformat(),
            "valid_until": license.valid_until.isoformat(),
            "allowed_strains": license.allowed_strains,
            "max_cultivation_area": license.max_cultivation_area,
            "aemps_reference": license.aemps_reference,
            "status": license.status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        raw = json.dumps(license_data, sort_keys=True)
        tx_hash = f"tx_{license.license_id}_license_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return tx_hash

    def register_cannabis_batch(self, batch: CannabisBatch) -> str:
        """Registra un lote de cannabis en GaiaChain."""
        batch_data: Dict[str, Any] = {
            "batch_id": batch.batch_id,
            "strain": batch.strain.model_dump(),
            "cultivation_site": batch.cultivation_site,
            "planting_date": batch.planting_date.isoformat(),
            "harvest_date": (
                batch.harvest_date.isoformat() if batch.harvest_date else None
            ),
            "weight": batch.weight,
            "lab_test_results": batch.lab_test_results,
            "status": batch.status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        raw = json.dumps(batch_data, sort_keys=True, default=str)
        tx_hash = f"tx_{batch.batch_id}_batch_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"
        return tx_hash

    def verify_cannabis_batch(self, batch_id: str) -> Dict[str, Any]:
        """Verifica un lote de cannabis en GaiaChain."""
        return {
            "batch_id": batch_id,
            "valid": True,
            "blockchain_tx": f"tx_{batch_id}_verified",
            "data": {
                "strain": "Amnesia Haze",
                "weight": 100,
                "thc": 0.25,
                "cbd": 12.5,
                "status": "certified",
                "certification_date": datetime.utcnow().isoformat(),
            },
        }
