"""Impacto socioeconómico."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SocioeconomicImpact:
    impact: dict[str, Any] = field(
        default_factory=lambda: {
            "decarbonization": {
                "description": (
                    "Descarbonización: Reducción neta de CO2 mediante economía circular real, "
                    "con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Reducción neta de CO2",
                    "Economía circular real",
                    "Soberanía europea",
                ],
            },
            "employment": {
                "description": (
                    "Empleo 4.0: Creación de la Escuela Rural de Operadores de Flotas, "
                    "reteniendo el talento joven en la región, con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Creación de la Escuela Rural de Operadores de Flotas",
                    "Retener el talento joven en la región",
                    "Soberanía europea",
                ],
            },
            "resilience": {
                "description": (
                    "Resiliencia: Capacidad de mantener la producción agrícola y energética "
                    "incluso en escenarios de colapso de infraestructuras globales ([BLACK-BOX-EXIT]), "
                    "con un enfoque en la soberanía europea."
                ),
                "features": [
                    "Mantener la producción agrícola y energética",
                    "Escenarios de colapso de infraestructuras globales",
                    "BLACK-BOX-EXIT",
                    "Soberanía europea",
                ],
            },
        }
    )

    def get_impact(self) -> dict[str, Any]:
        return {"impact": self.impact}
