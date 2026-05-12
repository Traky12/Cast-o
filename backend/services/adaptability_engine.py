# -*- coding: utf-8 -*-
"""Motor de adaptabilidad: ajusta agentes según feedback y preferencias del usuario."""
from __future__ import annotations

from datetime import datetime
from typing import Dict

from backend.models.agent import CustomAgent, UserAgentRelation


class AdaptabilityEngine:
    """Motor para adaptar agentes según interacciones y feedback."""

    def __init__(self) -> None:
        self.ethics_weights = {
            "equity": 0.3,
            "equality": 0.3,
            "transparency": 0.2,
            "privacy": 0.1,
            "sustainability": 0.1,
        }

    def adjust_agent_ethics(
        self,
        agent: CustomAgent,
        feedback: str,
        user_preferences: Dict[str, float],
    ) -> CustomAgent:
        """Ajusta la configuración ética del agente basado en feedback."""
        sentiment_score = self._analyze_feedback_sentiment(feedback)

        for ethic, weight in self.ethics_weights.items():
            current_value = getattr(agent.ethics, ethic, 0.5)
            adjustment = (sentiment_score * weight) / 10
            new_value = min(max(current_value + adjustment, 0.0), 1.0)
            setattr(agent.ethics, ethic, new_value)

        for trait, value in user_preferences.items():
            if trait in agent.personality:
                agent.personality[trait] = min(max(float(value), 0.0), 1.0)

        agent.updated_at = datetime.utcnow()
        return agent

    def _analyze_feedback_sentiment(self, feedback: str) -> float:
        """Analiza el sentimiento del feedback (-1 a 1)."""
        positive_words = ["bueno", "excelente", "genial", "útil", "amable"]
        negative_words = ["malo", "pésimo", "inútil", "lento", "confuso"]

        score = 0.0
        lower = feedback.lower()
        for word in positive_words:
            if word in lower:
                score += 0.2
        for word in negative_words:
            if word in lower:
                score -= 0.2

        return max(min(score, 1.0), -1.0)

    def update_agent_progress(
        self,
        agent: CustomAgent,
        interaction: UserAgentRelation,
    ) -> CustomAgent:
        """Actualiza el progreso del agente basado en interacciones."""
        agent.progress["effectiveness"] = min(
            0.1 * interaction.interaction_count,
            1.0,
        )

        if interaction.feedback:
            last_feedback = interaction.feedback[-1]
            if last_feedback.get("sentiment") == "positive":
                agent.progress["training"] = min(
                    agent.progress.get("training", 0.0) + 0.05,
                    1.0,
                )

        agent.updated_at = datetime.utcnow()
        return agent
