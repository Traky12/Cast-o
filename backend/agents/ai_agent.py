# backend/agents/ai_agent.py — Agente de IA tunado (Mistral, recomendaciones, cumplimiento, federated learning)

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from backend.ai.mistral_client import MistralAIClient
    from mistralai.models.chat_completion import ChatMessage
    _MISTRAL = True
except ImportError:
    MistralAIClient = None
    ChatMessage = None
    _MISTRAL = False

try:
    from backend.ai.knowledge_base import KnowledgeBase
    _KB = True
except ImportError:
    KnowledgeBase = None
    _KB = False

try:
    from backend.ai.model_registry import ModelRegistry
    _REG = True
except ImportError:
    ModelRegistry = None
    _REG = False

try:
    from backend.ai.federated_learning import FederatedLearningCoordinator
    _FL = True
except ImportError:
    FederatedLearningCoordinator = None
    _FL = False


NORMATIVE_CONTEXT = """
Normativas CASTÚO-SYSTEM™: ISO 27001:2022 (A.12.6.1, A.14.2.1, A.16.1.1), GDPR (Art. 25, 32, 35),
EU AI Act (2024/1689 Anexo III, Art. 13-14), NIS2 (2022/2555 Art. 21, 23), Ley 3/2023 Extremadura (Art. 20, 25).
"""


class TunedAIAgent:
    """
    Agente de IA tunado: recomendaciones, predicción de demanda, análisis de seguridad,
    cumplimiento normativo, optimización de código. Integración con base de conocimiento
    y federated learning opcionales.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.client: Any = MistralAIClient() if _MISTRAL else None
        self.knowledge_base = KnowledgeBase() if _KB else None
        self.model_registry = ModelRegistry() if _REG else None
        self.fed_learning = FederatedLearningCoordinator() if _FL else None
        self.performance_metrics: Dict[str, float] = {
            "recommendation_accuracy": 0.85,
            "demand_prediction_error": 0.12,
            "response_time_ms": 450.0,
            "compliance_score": 0.98,
        }

    async def get_recommendations(self, user_id: str, current_product_id: str, user_history: List[Dict]) -> Dict:
        if not self.client or not self.client.client:
            return {"recommendations": [], "reasoning": "Mistral no configurado", "compliance_note": "N/A"}
        try:
            prompt = f"""
{NORMATIVE_CONTEXT}
Tarea: Recomendaciones personalizadas de productos agroalimentarios.
Historial usuario: {json.dumps(user_history)[:2000]}
Producto actual: {current_product_id}
Responde JSON: {{ "recommendations": [...], "reasoning": "...", "compliance_note": "..." }}
"""
            messages = [
                ChatMessage(role="system", content="Experto en recomendaciones para sistemas críticos UE. Responde solo JSON."),
                ChatMessage(role="user", content=prompt),
            ]
            r = self.client.chat_completion(messages=messages, log_to_gaiachain=False)
            msg = r["choices"][0]["message"]
            text = msg.get("content", getattr(msg, "content", ""))
            return json.loads(text)
        except Exception as e:
            self.logger.error("get_recommendations: %s", e)
            return {"recommendations": [], "reasoning": str(e), "compliance_note": "Incidente ISO 27001:A.16.1.1"}

    async def predict_demand(self, product_id: str, historical_data: List[Dict]) -> Dict:
        if not self.client or not self.client.client:
            return {"forecast": {"demand": 0, "confidence": 0.5}, "key_factors": [], "compliance_note": "N/A"}
        try:
            prompt = f"""
{NORMATIVE_CONTEXT}
Tarea: Predecir demanda. Producto: {product_id}. Datos históricos: {json.dumps(historical_data)[:3000]}.
Responde JSON: {{ "forecast": {{ "demand": n, "confidence": 0-1 }}, "key_factors": [...], "compliance_note": "..." }}
"""
            messages = [
                ChatMessage(role="system", content="Experto en predicción de demanda para agroalimentación UE. Solo JSON."),
                ChatMessage(role="user", content=prompt),
            ]
            r = self.client.chat_completion(messages=messages, log_to_gaiachain=False)
            text = r["choices"][0]["message"].get("content", getattr(r["choices"][0]["message"], "content", "{}"))
            return json.loads(text)
        except Exception as e:
            self.logger.error("predict_demand: %s", e)
            return {"forecast": {"demand": 0, "confidence": 0.5}, "key_factors": [str(e)], "compliance_note": "NIS2:Art.21"}

    async def check_compliance(self, process: str, data: Dict) -> Dict:
        if not self.client or not self.client.client:
            return {"compliance_status": "unknown", "issues": ["Mistral no configurado"], "evidence": []}
        try:
            prompt = f"""
{NORMATIVE_CONTEXT}
Proceso: {process}. Datos: {json.dumps(data)[:2000]}.
Responde JSON: {{ "compliance_status": "compliant|warning|non_compliant", "issues": [...], "evidence": [...] }}
"""
            messages = [
                ChatMessage(role="system", content="Auditor de cumplimiento normativo UE. Solo JSON."),
                ChatMessage(role="user", content=prompt),
            ]
            r = self.client.chat_completion(messages=messages, log_to_gaiachain=False)
            text = r["choices"][0]["message"].get("content", getattr(r["choices"][0]["message"], "content", "{}"))
            return json.loads(text)
        except Exception as e:
            self.logger.error("check_compliance: %s", e)
            return {"compliance_status": "unknown", "issues": [str(e)], "evidence": []}

    async def run_continuous_improvement(self) -> None:
        """Bucle de mejora continua (auto-tuneo y federated learning periódico)."""
        self.logger.info("Agente IA: mejora continua iniciada")
        while True:
            try:
                if self.fed_learning and self.model_registry and datetime.utcnow().hour % 6 == 0:
                    local = self.model_registry.get_local_models()
                    if local:
                        await self.fed_learning.coordinate_round(local, min_participants=2)
                await asyncio.sleep(3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("run_continuous_improvement: %s", e)
                await asyncio.sleep(600)

    async def run(self) -> None:
        """Punto de entrada para ejecución como proceso agente."""
        await self.run_continuous_improvement()


def main() -> None:
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Agente de IA CASTÚO-SYSTEM™ v2.0")
    parser.add_argument("--federated-learning", action="store_true", help="Solo ejecutar bucle de federated learning / mejora continua")
    args = parser.parse_args()
    agent = TunedAIAgent()
    if os.environ.get("CASTUO_AGENT_ONESHOT"):
        asyncio.run(agent.get_recommendations("user1", "MG-KALE-50G", []))
        return
    if args.federated_learning:
        asyncio.run(agent.run_continuous_improvement())
        return
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
