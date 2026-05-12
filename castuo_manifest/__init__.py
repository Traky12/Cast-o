"""Manifiesto Castúo-System 1.0 — módulos por dominio."""

from .admin import AdminProfile
from .bundle import export_strategic_pitch_deck_only, manifest_bundle
from .exceptions import SovereigntyViolationError
from .impact import SocioeconomicImpact
from .pillars import SovereigntyPillars
from .pitch_deck import StrategicPitchDeck
from .sovereignty import assert_eu_sovereignty_block_complete, eu_sovereignty_framework
from .vision import StrategicVision

__all__ = [
    "AdminProfile",
    "StrategicVision",
    "SovereigntyPillars",
    "SocioeconomicImpact",
    "StrategicPitchDeck",
    "SovereigntyViolationError",
    "assert_eu_sovereignty_block_complete",
    "eu_sovereignty_framework",
    "export_strategic_pitch_deck_only",
    "manifest_bundle",
]
