"""Pitch deck estratégico."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StrategicPitchDeck:
    pitch_deck: dict[str, Any] = field(
        default_factory=lambda: {
            "slide1": {
                "title": "El Problema y la Solución 'Castúa' con Soberanía Europea",
                "content": [
                    "Contexto: Dependencia energética externa y despoblación rural.",
                    "La Solución: Un sistema autónomo que convierte residuos agrícolas en "
                    "combustible de alta pureza y servicios de datos blindados. Extremadura no "
                    "solo cultiva; ahora procesa y certifica, con un enfoque en la soberanía europea.",
                ],
            },
            "slide2": {
                "title": "La Arquitectura del Valor (The Stack) con Soberanía Europea",
                "content": [
                    "CAPA FÍSICA: [BIO-HUB-DIGITAL] (Energía) + [TERRA-ARMOR-05] (Músculo).",
                    "CAPA DE PERSISTENCIA: [OMEGA-LINK-STATION] (Malla de energía y datos láser).",
                    "CAPA DE INTELIGENCIA: [PROJECT-VULCAN] (Vigilancia) + [SYSTEM-KERNEL] (Orquestación).",
                    "CAPA DE CONFIANZA: [BIOPAY-V2-PULL] (Blockchain PQC).",
                    "SOBERANÍA EUROPEA: Encriptación de toda la trazabilidad y cualquier punto crítico o riesgo.",
                ],
            },
            "slide3": {
                "title": "Seguridad Inexpugnable (VSA & PQC) con Soberanía Europea",
                "content": [
                    "Criptografía: Implementación de ML-DSA (Dilithium) para resistir ataques "
                    "de ordenadores cuánticos, con un enfoque en la soberanía europea.",
                    "Resiliencia: Protocolo [OMEGA-SHIELD] capaz de operar en 'Blackout Total' "
                    "mediante navegación estelar y redes Ghost-Mesh, con un enfoque en la soberanía europea.",
                    "Integridad: Patrón Pull Payment y Triple-Check de oráculos. El fraude es "
                    "matemáticamente inviable, con un enfoque en la soberanía europea.",
                ],
            },
            "slide4": {
                "title": "Impacto y ROI con Soberanía Europea",
                "content": [
                    "Económico: Reducción del 20% en costes operativos y liquidación de pagos en tiempo real, con un enfoque en la soberanía europea.",
                    "Social: Creación de empleo tecnológico de élite en la Escuela Rural 4.0, con un enfoque en la soberanía europea.",
                    "Ambiental: Huella de carbono negativa y residuo cero, con un enfoque en la soberanía europea.",
                ],
            },
        }
    )

    def get_pitch_deck(self) -> dict[str, Any]:
        return {"pitch_deck": self.pitch_deck}
