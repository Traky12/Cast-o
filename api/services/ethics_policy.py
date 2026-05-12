from __future__ import annotations

import re
from typing import Final

from fastapi import HTTPException


_DISALLOWED_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\bodio\s+a\b", re.IGNORECASE),
    re.compile(r"\bexcluir\s+a\b", re.IGNORECASE),
    re.compile(r"\bdiscriminar\s+a\b", re.IGNORECASE),
    re.compile(r"\binferior(es)?\b", re.IGNORECASE),
    re.compile(r"\blimpiar\s+de\b", re.IGNORECASE),
    re.compile(r"\bviolencia\s+contra\b", re.IGNORECASE),
]

_PROTECTED_GROUPS: Final[re.Pattern[str]] = re.compile(
    r"\b(mujeres|hombres|migrantes|extranjeros|minorias|discapacidad|religion|etnia|raza)\b",
    re.IGNORECASE,
)


def _looks_discriminatory(text: str) -> bool:
    if not text.strip():
        return False

    has_protected_group = bool(_PROTECTED_GROUPS.search(text))
    has_disallowed_pattern = any(pattern.search(text) for pattern in _DISALLOWED_PATTERNS)
    return has_protected_group and has_disallowed_pattern


def enforce_ethical_equity_text(text: str, *, context: str) -> None:
    """Bloquea contenido contrario a ética/equidad antes de procesar."""
    if _looks_discriminatory(text):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Contenido bloqueado por política de ética y equidad en {context}"
            ),
        )