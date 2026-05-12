# -*- coding: utf-8 -*-
"""Modelo de feedback de usabilidad (pruebas con usuarios europeos)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class UsabilityFeedback(BaseModel):
    """Registro de feedback para validación con usuarios en España, Francia, Alemania."""

    user_id: str
    country: str  # ES, FR, DE, etc.
    task: str  # ej: generate_certificate, view_traceability
    success: bool
    time_seconds: int
    errors: Optional[List[str]] = None
    comments: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
