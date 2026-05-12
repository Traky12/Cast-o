# -*- coding: utf-8 -*-
"""API de agentes personalizables SABIONDA: CRUD, ética, adaptabilidad, agritech."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.agent import (
    Achievement,
    AgentConfiguration,
    AgentEthics,
    AgentProfile,
    CustomAgent,
    ImprovementTrack,
    UserAgentRelation,
)
from backend.services.adaptability_engine import AdaptabilityEngine
from backend.services.equity_engine import EquityEngine
from backend.services.ethics_validator import EthicsValidator
from backend.services.sabionda_master import get_sabionda_master

router = APIRouter(prefix="/agents", tags=["Agents"])

try:
    from backend.demo_trl101.router import router as _gemelo_demo_router

    router.include_router(_gemelo_demo_router, prefix="/gemelo", tags=["Gemelo digital demo ICEX"])
except ImportError:
    pass

agents_db: Dict[str, CustomAgent] = {}
engine = AdaptabilityEngine()
validator = EthicsValidator()
equity_engine = EquityEngine()
master = get_sabionda_master()


class CreateAgentBody(BaseModel):
    """Body para crear agente (perfil sin agent_id/created_at)."""
    name: str = ""
    description: str = ""
    type: str = "assistant"
    created_by: str = ""
    ethics: Dict[str, Any] = {}
    capabilities: List[str] = []
    knowledge_areas: List[str] = []
    language: str = "es"
    personality: Dict[str, float] = {}
    accessibility: Dict[str, bool] = {}
    custom_fields: Dict[str, str] = {}


class InteractBody(BaseModel):
    user_id: str = ""
    feedback: str | None = None


class ChatBody(BaseModel):
    user_input: str = ""
    user_profile: Dict[str, Any] = {}


class AdaptBody(BaseModel):
    feedback: str = ""
    user_preferences: Dict[str, float] = {}


@router.get("/", response_model=List[CustomAgent])
async def list_agents() -> List[CustomAgent]:
    """Lista todos los agentes."""
    return list(agents_db.values())


@router.post("/", response_model=CustomAgent)
async def create_agent(body: CreateAgentBody) -> CustomAgent:
    """Crea un nuevo agente personalizable."""
    agent_id = str(uuid.uuid4())
    now = datetime.utcnow()
    ethics = AgentEthics(**(body.ethics or {}))
    agent_type = body.type if body.type in ("assistant", "bot", "expert", "farmer", "psychologist") else "assistant"
    profile = AgentProfile(
        agent_id=agent_id,
        name=body.name or "Nuevo Agente",
        description=body.description,
        type=agent_type,
        created_by=body.created_by,
        created_at=now,
        updated_at=now,
        ethics=ethics,
        capabilities=body.capabilities or ["natural_language", "data_analysis"],
        knowledge_areas=body.knowledge_areas,
        language=body.language,
        personality=body.personality or {"empathy": 0.8, "precision": 0.9, "creativity": 0.7, "patience": 0.8},
        accessibility=body.accessibility or {
            "visual_impairment": False,
            "hearing_impairment": False,
            "motor_impairment": False,
            "cognitive_impairment": False,
        },
        custom_fields=body.custom_fields,
    )
    new_agent = CustomAgent(
        **profile.model_dump(),
        config=AgentConfiguration(),
        version="1.0",
        status="active",
    )
    agents_db[agent_id] = new_agent
    return new_agent


@router.get("/{agent_id}", response_model=CustomAgent)
async def get_agent(agent_id: str) -> CustomAgent:
    """Obtiene un agente por su ID."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return agents_db[agent_id]


@router.put("/{agent_id}/config", response_model=CustomAgent)
async def update_agent_config(agent_id: str, config: AgentConfiguration) -> CustomAgent:
    """Actualiza la configuración técnica de un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agents_db[agent_id].config = config
    agents_db[agent_id].updated_at = datetime.utcnow()
    return agents_db[agent_id]


@router.put("/{agent_id}/ethics", response_model=CustomAgent)
async def update_agent_ethics(agent_id: str, ethics: AgentEthics) -> CustomAgent:
    """Actualiza la configuración ética de un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agents_db[agent_id].ethics = ethics
    agents_db[agent_id].updated_at = datetime.utcnow()
    return agents_db[agent_id]


@router.put("/{agent_id}/personality", response_model=CustomAgent)
async def update_agent_personality(agent_id: str, personality: Dict[str, float]) -> CustomAgent:
    """Actualiza la personalidad del agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agents_db[agent_id].personality = personality
    agents_db[agent_id].updated_at = datetime.utcnow()
    return agents_db[agent_id]


@router.post("/{agent_id}/interact", response_model=UserAgentRelation)
async def register_interaction(agent_id: str, body: InteractBody) -> UserAgentRelation:
    """Registra una interacción entre usuario y agente (para adaptabilidad)."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    user_id = body.user_id or "anonymous"
    relation = next(
        (r for r in agents_db[agent_id].user_relations if r.user_id == user_id),
        None,
    )

    if not relation:
        relation = UserAgentRelation(user_id=user_id, agent_id=agent_id)
        agents_db[agent_id].user_relations.append(relation)

    relation.interaction_count += 1
    relation.last_interaction = datetime.utcnow()
    if body.feedback:
        sentiment = "positive" if any(w in body.feedback.lower() for w in ["bueno", "excelente", "útil"]) else "neutral"
        relation.feedback.append({
            "date": datetime.utcnow().isoformat(),
            "content": body.feedback,
            "sentiment": sentiment,
        })
        # Actualizar satisfacción
        if sentiment == "positive":
            agents_db[agent_id].progress["user_satisfaction"] = min(
                agents_db[agent_id].progress.get("user_satisfaction", 0) + 0.1,
                1.0,
            )

    return relation


@router.post("/{agent_id}/chat")
async def chat_with_agent(agent_id: str, body: ChatBody) -> Dict[str, Any]:
    """Interactúa con un agente y obtiene respuesta adaptada."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    if agent_id not in master.agents:
        master.register_agent(agents_db[agent_id])

    response = master.get_agent_response(agent_id, body.user_input or "", body.user_profile or {})
    return {
        "agent_id": agent_id,
        "response": response,
        "adaptation_notes": "Respuesta adaptada a tu perfil y preferencias.",
    }


@router.get("/{agent_id}/progress")
async def get_agent_progress(agent_id: str) -> Dict[str, float]:
    """Obtiene el progreso de un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return agents_db[agent_id].progress


@router.post("/{agent_id}/adapt", response_model=CustomAgent)
async def adapt_agent(agent_id: str, body: AdaptBody) -> CustomAgent:
    """Adapta un agente según feedback y preferencias del usuario."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")

    user_id = "current_user"
    relation = next(
        (r for r in agents_db[agent_id].user_relations if r.user_id == user_id),
        None,
    )
    if not relation:
        relation = UserAgentRelation(user_id=user_id, agent_id=agent_id)
        agents_db[agent_id].user_relations.append(relation)

    agents_db[agent_id] = engine.adjust_agent_ethics(
        agents_db[agent_id],
        body.feedback,
        body.user_preferences,
    )
    agents_db[agent_id] = engine.update_agent_progress(agents_db[agent_id], relation)
    return agents_db[agent_id]


@router.get("/{agent_id}/improvements", response_model=List[ImprovementTrack])
async def get_improvements(agent_id: str) -> List[ImprovementTrack]:
    """Obtiene el historial de mejoras de un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return agents_db[agent_id].improvement_history


@router.post("/{agent_id}/improvements", response_model=CustomAgent)
async def log_improvement(agent_id: str, improvement: ImprovementTrack) -> CustomAgent:
    """Registra una mejora en el historial del agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agents_db[agent_id].improvement_history.append(improvement)
    agents_db[agent_id].updated_at = datetime.utcnow()
    return agents_db[agent_id]


@router.get("/{agent_id}/achievements", response_model=List[Achievement])
async def get_achievements(agent_id: str) -> List[Achievement]:
    """Obtiene los logros de un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    return agents_db[agent_id].achievements


@router.post("/{agent_id}/achievements", response_model=CustomAgent)
async def add_achievement(agent_id: str, achievement: Achievement) -> CustomAgent:
    """Añade un logro al agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agents_db[agent_id].achievements.append(achievement)
    agents_db[agent_id].updated_at = datetime.utcnow()
    return agents_db[agent_id]


@router.get("/{agent_id}/ethics/validate")
async def validate_ethics(agent_id: str) -> Dict[str, Any]:
    """Valida la ética de un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    is_valid, errors = validator.validate_agent_ethics(agents_db[agent_id])
    suggestions = validator.suggest_improvements(agents_db[agent_id])
    return {
        "valid": is_valid,
        "errors": errors,
        "suggestions": suggestions,
        "compliance": agents_db[agent_id].ethics.compliance,
    }


@router.post("/{agent_id}/equity/check")
async def check_equity(agent_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Evalúa la equidad en el trato del agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    equity_report = equity_engine.check_equity(agents_db[agent_id], user_profile)
    return {
        "agent_id": agent_id,
        "equity_report": equity_report,
        "message": "El agente cumple con estándares de equidad e igualdad.",
    }


@router.post("/{agent_id}/accessibility/adjust", response_model=CustomAgent)
async def adjust_accessibility(agent_id: str, user_needs: Dict[str, Any]) -> CustomAgent:
    """Ajusta el agente para necesidades de accesibilidad."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agents_db[agent_id] = equity_engine.adjust_for_accessibility(
        agents_db[agent_id],
        user_needs,
    )
    return agents_db[agent_id]


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str) -> Dict[str, str]:
    """Elimina un agente."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    del agents_db[agent_id]
    if agent_id in master.agents:
        del master.agents[agent_id]
    return {"status": "deleted"}


# --- Agritech ---
from backend.agents.agritech_agent import AgritechAgent


@router.post("/agritech/create", response_model=CustomAgent)
async def create_agritech_agent(body: CreateAgentBody) -> CustomAgent:
    """Crea un agente especializado en agritech."""
    agent_id = str(uuid.uuid4())
    now = datetime.utcnow()
    ethics = AgentEthics(
        sustainability=1.0,
        transparency=1.0,
        **(body.ethics or {}),
    )
    agent = AgritechAgent(
        agent_id=agent_id,
        name=body.name or "Asistente Agritech",
        description=body.description or "Agente para cultivos hidropónicos y trazabilidad",
        type=body.type or "expert",
        created_by=body.created_by,
        created_at=now,
        updated_at=now,
        ethics=ethics,
        capabilities=["natural_language", "data_analysis", "iot_controller", "blockchain_reader"],
        knowledge_areas=body.knowledge_areas or [
            "hydroponics",
            "microgreens",
            "blockchain_traceability",
            "iot_sensors",
            "sustainable_agriculture",
        ],
        language=body.language,
        personality=body.personality or {"precision": 0.9, "patience": 0.8},
        config=AgentConfiguration(
            tools=["iot_controller", "blockchain_writer", "weather_api", "nutrient_calculator"],
        ),
        version="1.0",
        status="active",
    )
    agents_db[agent_id] = agent
    return agent


@router.post("/{agent_id}/agritech/analyze")
async def analyze_environment(agent_id: str, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analiza datos ambientales con un agente agritech."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agent = agents_db[agent_id]
    if not isinstance(agent, AgritechAgent):
        raise HTTPException(status_code=400, detail="Agente no válido para agritech")
    return agent.analyze_environment(sensor_data)


@router.post("/{agent_id}/agritech/certificate")
async def generate_certificate(agent_id: str, batch_data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera un certificado de trazabilidad con un agente agritech."""
    if agent_id not in agents_db:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    agent = agents_db[agent_id]
    if not isinstance(agent, AgritechAgent):
        raise HTTPException(status_code=400, detail="Agente no válido para agritech")
    return agent.generate_certificate(batch_data)
