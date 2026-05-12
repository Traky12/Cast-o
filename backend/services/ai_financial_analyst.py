# -*- coding: utf-8 -*-
"""Informes financieros operativos para agentes (datos locales; sin envío a terceros por defecto)."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from backend.services.water_billing import generate_certification_report, monthly_billing_summary

logger = logging.getLogger(__name__)


class AIFinancialAnalyst:
    def __init__(self) -> None:
        self.enabled = os.getenv("AI_FINANCIAL_ANALYST_ENABLED", "0").strip() in ("1", "true", "True")

    def generate_monthly_report(self, year: int, month: int) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled", "message": "AI Financial Analyst not enabled"}
        try:
            return {
                "status": "success",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report": {
                    "monthly_summary": monthly_billing_summary(year, month),
                    "certification": generate_certification_report(year, month),
                },
            }
        except Exception as e:
            logger.exception("Informe financiero IA fallido")
            return {"status": "error", "message": str(e)}

    def detect_anomalies(self) -> list[dict[str, Any]]:
        if not self.enabled:
            return []
        return []
