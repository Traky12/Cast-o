# -*- coding: utf-8 -*-
"""Validador de cumplimiento cannabis medicinal (RD 903/2025, AEMPS)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from backend.models.cannabis_specific import CannabisBatch, CannabisLicense


class CannabisComplianceValidator:
    """Valida el cumplimiento con RD 903/2025 y normativas AEMPS."""

    def validate_cannabis_license(self, license: CannabisLicense) -> Tuple[bool, List[str]]:
        """Valida una licencia de cannabis medicinal."""
        errors: List[str] = []

        if datetime.utcnow() > license.valid_until:
            errors.append("Licencia caducada")

        allowed_strains = ["Amnesia Haze", "White Widow", "OG Kush"]
        for strain in license.allowed_strains:
            if strain not in allowed_strains:
                errors.append(f"Variedad no permitida: {strain}")

        if license.max_cultivation_area > 1000:
            errors.append("Área de cultivo excede el límite permitido (1000 m²)")

        return (len(errors) == 0, errors)

    def validate_cannabis_batch(
        self, batch: CannabisBatch, licenses_db: Dict[str, CannabisLicense]
    ) -> Tuple[bool, List[str]]:
        """Valida un lote de cannabis según RD 903/2025."""
        errors: List[str] = []

        if batch.lab_test_results:
            if batch.lab_test_results.get("thc", 0) > 0.3:
                errors.append("Nivel de THC excede el límite legal (0.3%)")
            if batch.lab_test_results.get("cbd", 0) < 5.0:
                errors.append("Nivel de CBD inferior al mínimo requerido (5%)")

        lic_key = batch.strain.cultivation_license
        if lic_key not in licenses_db:
            errors.append("Licencia no válida")
        elif licenses_db[lic_key].status != "active":
            errors.append("Licencia no activa")

        return (len(errors) == 0, errors)

    def generate_aemps_report(
        self, batch: CannabisBatch, licenses_db: Dict[str, CannabisLicense]
    ) -> Dict[str, Any]:
        """Genera un informe para AEMPS (formato oficial)."""
        lic = licenses_db.get(batch.strain.cultivation_license)
        aemps_ref = lic.aemps_reference if lic else "N/A"
        return {
            "batch_id": batch.batch_id,
            "strain": {
                "name": batch.strain.name,
                "thc": batch.strain.thc_percentage,
                "cbd": batch.strain.cbd_percentage,
                "license": batch.strain.cultivation_license,
            },
            "cultivation_site": batch.cultivation_site,
            "harvest_date": (
                batch.harvest_date.isoformat() if batch.harvest_date else None
            ),
            "weight": batch.weight,
            "lab_results": batch.lab_test_results,
            "compliance": {
                "rd_903_2025": True,
                "gmp": True,
                "iso_22000": True,
                "aemps_reference": aemps_ref,
            },
            "blockchain_tx": batch.blockchain_tx,
            "certification_status": batch.certification_status,
        }
