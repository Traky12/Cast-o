"""
Perfiles terpénicos para investigación agronómica en laboratorio.

research_literature_tags: indexación bibliográfica / taxonomía interna, sin validez clínica.
regulatory_reference_frameworks: referencias legales para asesoría jurídica; no declaración de conformidad.
trl: etiqueta de puerta de integración del monorepo (tests/compose TRL-6); no implica validación de campo ni de silicio neuromórfico.
"""

from __future__ import annotations

from typing import Dict, List, TypedDict

TERPENE_PROFILES_VERSION: str = "v2.1.0"

ETHICS_NOTICE_SHORT: str = (
    "Perfil orientativo para investigación agronómica en laboratorio. No constituye consejo médico "
    "ni declaración de conformidad normativa."
)


class TerpeneProfile(TypedDict):
    description: str
    optimal_conditions: Dict[str, str]
    research_literature_tags: List[str]
    regulatory_reference_frameworks: Dict[str, List[str]]
    trl: str


TERPENE_PROFILES: Dict[str, TerpeneProfile] = {
    "mirceno": {
        "description": "Perfil de investigación para cultivos con potencial relajante (TRL-6)",
        "optimal_conditions": {
            "luz_umol": "800-1200",
            "temp": "24-28°C",
            "ph": "5.8-6.2",
            "ec": "1.0-1.6",
            "uvb_ratio": "0.05",
        },
        "research_literature_tags": ["sleep_research", "stress_response", "muscle_relaxation"],
        "regulatory_reference_frameworks": {
            "UE": ["Reglamento (UE) 2015/2283"],
            "ES": ["Real Decreto 130/2018"],
            "DE": ["PflSchG"],
        },
        "trl": "TRL-6-staging-gate",
    },
    "limoneno": {
        "description": "Perfil de investigación para cultivos con potencial elevador del ánimo (TRL-6)",
        "optimal_conditions": {
            "luz_umol": "600-900",
            "temp": "22-26°C",
            "ph": "6.0-6.5",
            "ec": "1.2-1.8",
            "uvb_ratio": "0.02",
        },
        "research_literature_tags": ["mood_research", "stress_response", "antioxidant_properties"],
        "regulatory_reference_frameworks": {
            "UE": ["Directiva 2002/46/CE"],
            "ES": ["Real Decreto 130/2018"],
            "DE": ["PflSchG"],
        },
        "trl": "TRL-6-staging-gate",
    },
}
