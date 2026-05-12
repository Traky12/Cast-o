# -*- coding: utf-8 -*-
"""Validador de ética: asegura cumplimiento con AI Act UE, GDPR, ISO."""
from __future__ import annotations

from typing import Dict, List, Tuple

from backend.models.agent import AgentEthics, CustomAgent


class EthicsValidator:
    """Valida que un agente cumpla con estándares éticos."""

    def __init__(self) -> None:
        self.min_ethics_thresholds = {
            "equity": 0.7,
            "equality": 0.7,
            "transparency": 0.8,
            "privacy": 0.9,
            "sustainability": 0.6,
        }
        self.required_compliance = [
            "AI_Act_UE_2024_1689",
            "GDPR",
            "ISO_9001",
        ]

    def validate_agent_ethics(self, agent: CustomAgent) -> Tuple[bool, List[str]]:
        """Valida la configuración ética de un agente."""
        errors: List[str] = []
        valid = True

        for ethic, threshold in self.min_ethics_thresholds.items():
            value = getattr(agent.ethics, ethic, 0.0)
            if value < threshold:
                errors.append(f"{ethic} ({value}) < {threshold}")
                valid = False

        for norm in self.required_compliance:
            if norm not in agent.ethics.compliance:
                errors.append(f"Falta cumplimiento con {norm}")
                valid = False

        return valid, errors

    def suggest_improvements(self, agent: CustomAgent) -> Dict[str, float]:
        """Sugiere mejoras para cumplir con estándares éticos."""
        suggestions: Dict[str, float] = {}
        for ethic, threshold in self.min_ethics_thresholds.items():
            current = getattr(agent.ethics, ethic, 0.0)
            if current < threshold:
                suggestions[ethic] = threshold - current
        return suggestions
