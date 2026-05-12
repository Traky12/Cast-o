"""Visión estratégica Castúo-System 1.0."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StrategicVision:
    vision: dict[str, Any] = field(
        default_factory=lambda: {
            "description": (
                "El Castúo-System no busca sustituir al agricultor, sino dotarle de las "
                "herramientas del siglo XXII. Extremadura deja de ser una exportadora de "
                "materia prima para convertirse en una exportadora de servicios bioenergéticos "
                "y datos certificados, con un enfoque en la soberanía europea y la encriptación "
                "de toda la trazabilidad."
            ),
            "features": [
                "Herramientas del siglo XXII",
                "Exportadora de servicios bioenergéticos",
                "Exportadora de datos certificados",
                "Soberanía europea",
                "Encriptación de toda la trazabilidad",
            ],
        }
    )

    def get_vision(self) -> dict[str, Any]:
        return {"vision": self.vision}
