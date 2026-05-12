"""Manifiesto atómico V1.0-SOVEREIGNTY: pitch_deck no exportable aislado."""
from __future__ import annotations

from typing import Any

from .admin import AdminProfile
from .exceptions import SovereigntyViolationError
from .impact import SocioeconomicImpact
from .pillars import SovereigntyPillars
from .pitch_deck import StrategicPitchDeck
from .sovereignty import assert_eu_sovereignty_block_complete, eu_sovereignty_framework
from .vision import StrategicVision


def manifest_bundle() -> dict[str, Any]:
    admin = AdminProfile().get_profile()
    vision = StrategicVision().get_vision()
    pillars = SovereigntyPillars().get_pillars()
    impact = SocioeconomicImpact().get_impact()
    pitch_deck = StrategicPitchDeck().get_pitch_deck()
    eu_sovereignty = eu_sovereignty_framework()
    assert_eu_sovereignty_block_complete(eu_sovereignty)

    return {
        "version": "1.0",
        "design_freeze": "V1.0-SOVEREIGNTY",
        "admin": admin,
        "vision": vision,
        "pillars": pillars,
        "impact": impact,
        "pitch_deck": pitch_deck,
        "eu_sovereignty": eu_sovereignty,
    }


def export_strategic_pitch_deck_only() -> dict[str, Any]:
    """Prohibido por Sabionda: el pitch sin soberanía rompe el sello RED III / NIS2."""
    raise SovereigntyViolationError(
        "StrategicPitchDeck no exportable sin bloque eu_sovereignty. "
        "Usar manifest_bundle() como unidad atómica V1.0-SOVEREIGNTY."
    )
