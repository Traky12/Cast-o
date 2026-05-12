# -*- coding: utf-8 -*-
"""Validador de cumplimiento microgreens (GlobalGAP, ISO 22000)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Tuple

from backend.models.microgreens_specific import MicrogreenBatch, MicrogreenVariety


class MicrogreenComplianceValidator:
    """Valida el cumplimiento con GlobalGAP e ISO 22000 para microgreens."""

    def validate_microgreen_batch(
        self, batch: MicrogreenBatch, variety: MicrogreenVariety
    ) -> Tuple[bool, List[str]]:
        """Valida un lote de microgreens según GlobalGAP."""
        errors: List[str] = []

        if batch.environmental_data:
            env = batch.environmental_data
            ph = env.get("ph")
            if ph is not None and abs(ph - variety.ideal_ph) > 0.5:
                errors.append(
                    f"pH fuera de rango ideal (actual: {ph}, ideal: {variety.ideal_ph})"
                )
            temp = env.get("temperature")
            if temp is not None and (
                temp < variety.ideal_temperature[0]
                or temp > variety.ideal_temperature[1]
            ):
                errors.append(
                    f"Temperatura fuera de rango ideal (actual: {temp}°C, ideal: {variety.ideal_temperature})"
                )
            hum = env.get("humidity")
            if hum is not None and (
                hum < variety.ideal_humidity[0] or hum > variety.ideal_humidity[1]
            ):
                errors.append(
                    f"Humedad fuera de rango ideal (actual: {hum}%, ideal: {variety.ideal_humidity})"
                )
            ec = env.get("ec")
            if ec is not None and abs(ec - variety.ideal_ec) > 0.3:
                errors.append(
                    f"EC fuera de rango ideal (actual: {ec}, ideal: {variety.ideal_ec})"
                )

        if batch.weight is not None and (batch.weight < 200 or batch.weight > 300):
            errors.append(
                f"Peso fuera de rango esperado (actual: {batch.weight}g, esperado: 200-300g)"
            )

        return (len(errors) == 0, errors)

    def generate_globalgap_report(
        self, batch: MicrogreenBatch, variety: MicrogreenVariety
    ) -> dict:
        """Genera un informe de cumplimiento con GlobalGAP."""
        compliant, _ = self.validate_microgreen_batch(batch, variety)
        env = batch.environmental_data or {}
        ph = env.get("ph", variety.ideal_ph)
        temp = env.get("temperature", variety.ideal_temperature[0])
        hum = env.get("humidity", variety.ideal_humidity[0])
        ec = env.get("ec", variety.ideal_ec)
        return {
            "batch_id": batch.batch_id,
            "variety": variety.name,
            "scientific_name": variety.scientific_name,
            "growth_cycle_days": variety.growth_cycle,
            "environmental_compliance": {
                "ph": {
                    "actual": ph,
                    "ideal": variety.ideal_ph,
                    "compliant": abs(ph - variety.ideal_ph) <= 0.5,
                },
                "temperature": {
                    "actual": temp,
                    "ideal": f"{variety.ideal_temperature[0]}-{variety.ideal_temperature[1]}°C",
                    "compliant": (
                        variety.ideal_temperature[0]
                        <= temp
                        <= variety.ideal_temperature[1]
                    ),
                },
                "humidity": {
                    "actual": hum,
                    "ideal": f"{variety.ideal_humidity[0]}-{variety.ideal_humidity[1]}%",
                    "compliant": (
                        variety.ideal_humidity[0] <= hum <= variety.ideal_humidity[1]
                    ),
                },
                "ec": {
                    "actual": ec,
                    "ideal": variety.ideal_ec,
                    "compliant": abs(ec - variety.ideal_ec) <= 0.3,
                },
            },
            "weight_compliance": {
                "actual": batch.weight,
                "expected": "200-300g",
                "compliant": (
                    200 <= batch.weight <= 300 if batch.weight is not None else False
                ),
            },
            "globalgap_compliance": compliant,
            "certification_standards": variety.certification_standards,
            "blockchain_tx": batch.blockchain_tx,
            "issued_by": "CTAEX + GlobalGAP",
            "issue_date": datetime.utcnow().isoformat(),
        }
