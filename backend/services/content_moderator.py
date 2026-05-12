# -*- coding: utf-8 -*-
"""Moderación de contenido según restricciones de la cuenta Pro."""
from __future__ import annotations

import re
from typing import Tuple
from urllib.parse import urlparse

from backend.models.pro_account import ContentRestriction


class ContentModerator:
    """Modera contenido según las restricciones de la cuenta Pro."""

    def __init__(self, restrictions: ContentRestriction) -> None:
        self.restrictions = restrictions
        self.blocked_patterns = [
            re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
            for word in (restrictions.blocked_keywords or [])
        ]

    def moderate_text(self, text: str) -> Tuple[bool, str]:
        """Modera un texto según las restricciones."""
        if len(text) > self.restrictions.max_content_length:
            return (
                False,
                f"Texto demasiado largo (máx. {self.restrictions.max_content_length} caracteres)",
            )
        for pattern in self.blocked_patterns:
            if pattern.search(text):
                return False, "Contenido bloqueado: palabra prohibida detectada"
        return True, "Contenido aprobado"

    def moderate_url(self, url: str) -> bool:
        """Verifica si un dominio está permitido."""
        try:
            domain = urlparse(url).netloc.lower()
        except Exception:
            return False
        allowed = [d.lower() for d in (self.restrictions.allowed_domains or [])]
        if not allowed:
            return True
        return any(domain.endswith(d) for d in allowed)

    def moderate_file(self, filename: str, content_type: str) -> bool:
        """Verifica si un tipo de archivo está permitido."""
        if "." in filename:
            ext = filename.rsplit(".", 1)[-1].lower()
        else:
            ext = ""
        return ext in (self.restrictions.allowed_file_types or [])
