# -*- coding: utf-8 -*-
"""Comprobaciones técnicas vía HTTP interno (health) para agentes de soporte."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AITechnicalSupport:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_TECHNICAL_SUPPORT_ENABLED", "0").strip() in ("1", "true", "True")
        self.base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

    def check_health(self) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "AI Technical Support not enabled"}
        try:
            with httpx.Client(timeout=15.0) as client:
                r = client.get(f"{self.base_url}/water/ctaex/health")
                r.raise_for_status()
                return {"status": "ok", "health": r.json(), "base_url": self.base_url}
        except Exception as e:
            logger.warning("Health check IA: %s", e)
            return {"status": "error", "message": str(e), "base_url": self.base_url}

    def diagnose_issue(self, error_message: str) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "AI Technical Support not enabled"}
        return {
            "status": "diagnosed",
            "error": error_message,
            "solution": "Revisar docs/agrotech/WATER-SYSTEM-CTAEX.md y ejecutar scripts/smoke_test.py",
            "documentation_relative": "docs/agrotech/WATER-SYSTEM-CTAEX.md",
        }
