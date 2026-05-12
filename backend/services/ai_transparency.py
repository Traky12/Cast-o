# -*- coding: utf-8 -*-
"""Informes de transparencia para AI Act (UE 2024/1689) Art. 13."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class AITransparencyReport(BaseModel):
    """Genera informe de transparencia según Art. 13 AI Act."""

    model_name: str
    training_data: Dict[str, Any] = {}
    metrics: Dict[str, float] = {}
    bias_test: Dict[str, float] = {}
    compliance: bool = False

    def generate_report(self) -> Dict[str, Any]:
        """Genera un informe de transparencia según Art. 13 AI Act."""
        self.compliance = all([
            self.metrics.get("accuracy", 0) >= 0.95,
            self.bias_test.get("demographic_parity", 0) >= 0.9,
            "data_source" in self.training_data or "source" in self.training_data,
        ])
        return {
            "model": self.model_name,
            "compliance": self.compliance,
            "details": {
                "metrics": self.metrics,
                "bias": self.bias_test,
                "data": self.training_data,
            },
        }
