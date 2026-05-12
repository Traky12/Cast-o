"""Cuatro pilares de la soberanía."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SovereigntyPillars:
    pillars: dict[str, Any] = field(
        default_factory=lambda: {
            "energy_independence": {
                "description": (
                    "Independencia Energética: Transformación de residuos (arroz/sorgo) en "
                    "combustible de grado aeronáutico ([BIO-HUB-DIGITAL]), con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Transformación de residuos (arroz/sorgo)",
                    "Combustible de grado aeronáutico",
                    "BIO-HUB-DIGITAL",
                    "Soberanía europea",
                ],
            },
            "persistent_infrastructure": {
                "description": (
                    "Infraestructura Persistente: Redes de datos e intercambio de energía por "
                    "láser que no dependen de terceros países ([OMEGA-LINK]), con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Redes de datos",
                    "Intercambio de energía por láser",
                    "OMEGA-LINK",
                    "Soberanía europea",
                ],
            },
            "post_quantum_security": {
                "description": (
                    "Seguridad Post-Cuántica: Blindaje total contra ciberamenazas futuras "
                    "mediante protocolos de criptografía de retícula ([ML-DSA]), con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Blindaje total contra ciberamenazas futuras",
                    "Protocolos de criptografía de retícula",
                    "ML-DSA",
                    "Soberanía europea",
                ],
            },
            "transparent_governance": {
                "description": (
                    "Gobernanza Transparente: Liquidación instantánea de pagos a cooperativas "
                    "basada en la verdad física de los sensores, no en la burocracia ([BIOPAY-V2-PULL]), "
                    "con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Liquidación instantánea de pagos a cooperativas",
                    "Verdad física de los sensores",
                    "BIOPAY-V2-PULL",
                    "Soberanía europea",
                ],
            },
        }
    )

    def get_pillars(self) -> dict[str, Any]:
        return {"pillars": self.pillars}
