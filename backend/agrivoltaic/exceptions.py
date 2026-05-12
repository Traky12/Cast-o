"""Excepciones agrivoltaicas: payload corrupto vs flujos certificables."""
from __future__ import annotations


class AgrivoltaicPayloadError(ValueError):
    """Datos de sensores o finca incoherentes; respuesta API 400 + auditoría."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
