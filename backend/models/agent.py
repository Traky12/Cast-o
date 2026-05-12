# -*- coding: utf-8 -*-
"""Modelos para agentes personalizables SABIONDA (ética AI Act UE, perfiles, progreso)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AgentEthics(BaseModel):
    """Configuración ética del agente (basado en AI Act UE 2024/1689)."""

    equity: float = Field(1.0, ge=0.0, le=1.0, description="0.0 (bajo) a 1.0 (alto)")
    equality: float = Field(1.0, ge=0.0, le=1.0)
    transparency: float = Field(1.0, ge=0.0, le=1.0)
    privacy: float = Field(1.0, ge=0.0, le=1.0)
    sustainability: float = Field(1.0, ge=0.0, le=1.0)
    compliance: List[str] = Field(
        default_factory=lambda: [
            "AI_Act_UE_2024_1689",
            "GDPR",
            "ISO_9001",
            "ISO_27001",
        ]
    )


class AgentProfile(BaseModel):
    """Perfil base del agente (adaptable a necesidades personales)."""

    agent_id: str = ""
    name: str = ""
    description: str = ""
    type: Literal["assistant", "bot", "expert", "farmer", "psychologist"] = "assistant"
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    ethics: AgentEthics = Field(default_factory=AgentEthics)
    capabilities: List[str] = Field(
        default_factory=lambda: [
            "natural_language",
            "data_analysis",
            "decision_making",
            "emotional_support",
        ]
    )
    knowledge_areas: List[str] = Field(default_factory=list)
    language: str = "es"
    personality: Dict[str, float] = Field(
        default_factory=lambda: {
            "empathy": 0.8,
            "precision": 0.9,
            "creativity": 0.7,
            "patience": 0.8,
        }
    )
    accessibility: Dict[str, bool] = Field(
        default_factory=lambda: {
            "visual_impairment": False,
            "hearing_impairment": False,
            "motor_impairment": False,
            "cognitive_impairment": False,
        }
    )
    progress: Dict[str, float] = Field(
        default_factory=lambda: {
            "training": 0.0,
            "effectiveness": 0.0,
            "user_satisfaction": 0.0,
        }
    )
    custom_fields: Dict[str, str] = Field(default_factory=dict)


class AgentConfiguration(BaseModel):
    """Configuración técnica del agente."""

    model: str = "mistral-large"
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(4096, ge=256, le=32768)
    memory_window: int = Field(10, ge=1, le=100)
    tools: List[str] = Field(
        default_factory=lambda: [
            "web_search",
            "database_query",
            "blockchain_reader",
            "iot_controller",
        ]
    )
    data_sources: List[str] = Field(default_factory=list)
    security_level: Literal["low", "medium", "high"] = "high"


class UserAgentRelation(BaseModel):
    """Relación entre usuario y agente (adaptabilidad)."""

    user_id: str = ""
    agent_id: str = ""
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    preferences: Dict[str, str] = Field(default_factory=dict)
    feedback: List[Dict[str, Any]] = Field(default_factory=list)


class ImprovementTrack(BaseModel):
    """Rastro de mejoras del agente."""

    date: datetime = Field(default_factory=datetime.utcnow)
    metric: str = ""
    old_value: float = 0.0
    new_value: float = 0.0
    cause: str = ""
    notes: Optional[str] = None


class Achievement(BaseModel):
    """Logro desbloqueado por el agente."""

    name: str = ""
    description: str = ""
    unlocked_at: datetime = Field(default_factory=datetime.utcnow)
    criteria: str = ""


class CustomAgent(AgentProfile):
    """Agente personalizable con configuración técnica, historial y logros."""

    config: AgentConfiguration = Field(default_factory=AgentConfiguration)
    user_relations: List[UserAgentRelation] = Field(default_factory=list)
    version: str = "1.0"
    status: Literal["draft", "active", "deprecated"] = "draft"
    improvement_history: List[ImprovementTrack] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
