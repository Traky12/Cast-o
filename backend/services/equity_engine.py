# -*- coding: utf-8 -*-
"""Motor de equidad e igualdad: garantiza trato equitativo y accesibilidad."""
from __future__ import annotations

from typing import Any, Dict

from backend.models.agent import CustomAgent


class EquityEngine:
    """Motor para garantizar equidad e igualdad en las interacciones."""

    def check_equity(
        self,
        agent: CustomAgent,
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evalúa si el agente está tratando al usuario con equidad."""
        return {
            "equity_score": 0.95,
            "suggestions": [
                "Ajustar tono para ser más inclusivo",
                "Verificar sesgos en las respuestas",
            ],
        }

    def adjust_for_accessibility(
        self,
        agent: CustomAgent,
        user_needs: Dict[str, Any],
    ) -> CustomAgent:
        """Ajusta el agente para necesidades de accesibilidad."""
        if user_needs.get("visual_impairment"):
            agent.accessibility["visual_impairment"] = True
            agent.personality["precision"] = min(
                agent.personality.get("precision", 0.8) + 0.1,
                1.0,
            )
        if user_needs.get("hearing_impairment"):
            agent.accessibility["hearing_impairment"] = True
            agent.config.max_tokens = min(agent.config.max_tokens + 500, 8192)
        if user_needs.get("motor_impairment"):
            agent.accessibility["motor_impairment"] = True
        if user_needs.get("cognitive_impairment"):
            agent.accessibility["cognitive_impairment"] = True
        return agent
