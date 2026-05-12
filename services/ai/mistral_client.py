"""
CASTÚO-SYSTEM™ v3.0 — Clientes AI Europeos
Mistral AI (soberanía UE) + Cursor AI + SABIONDA
Conformes AI Act UE | Datos procesados en infraestructura europea
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional

import httpx

from config.global_config import CursorConfig, MistralConfig, SabiondaConfig

logger = logging.getLogger("castuo.ai")


@dataclass
class ChatMessage:
    role: str   # system | user | assistant
    content: str


@dataclass
class InferenceResult:
    provider: str
    model: str
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    finish_reason: str = "stop"


class MistralClient:
    """
    Cliente Mistral AI — IA soberana europea.
    Modelos: mistral-large-latest (inferencia) | open-mistral-7b (fine-tuning)
    Endpoint: api.mistral.ai — infraestructura UE GDPR-compliant
    """

    def __init__(self, config: MistralConfig) -> None:
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> InferenceResult:
        """Inferencia de chat con Mistral. Soporta tool calling."""
        payload: Dict[str, Any] = {
            "model": model or self.config.inference_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        return InferenceResult(
            provider="mistral",
            model=data.get("model", payload["model"]),
            content=choice["message"]["content"] or "",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def agricultural_analysis(
        self,
        context: str,
        query: str,
        system_prompt: Optional[str] = None,
    ) -> InferenceResult:
        """
        Análisis agrícola especializado usando Mistral Large.
        Contexto: datos de sensores IoT, registros SIEX, etc.
        """
        sys_prompt = system_prompt or (
            "Eres un experto en agricultura europea, ganadería y cumplimiento normativo PAC. "
            "Respondes en español. Tus análisis son precisos, auditables y conformes RGPD."
        )
        messages = [
            ChatMessage(role="system", content=sys_prompt),
            ChatMessage(
                role="user",
                content=f"Contexto de la explotación:\n{context}\n\nConsulta:\n{query}",
            ),
        ]
        return await self.chat(messages, model=self.config.inference_model)

    async def list_models(self) -> List[str]:
        """Lista los modelos Mistral disponibles en el endpoint configurado."""
        response = await self.client.get("/models")
        response.raise_for_status()
        data = response.json()
        return [m["id"] for m in data.get("data", [])]


class CursorAIClient:
    """
    Cliente Cursor AI — asistente de código europeo.
    Integrado para generación y revisión de código en el orquestador.
    """

    def __init__(self, config: CursorConfig) -> None:
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Genera código mediante Cursor AI con descripción en lenguaje natural."""
        payload: Dict[str, Any] = {
            "description": description,
            "language": language,
        }
        if context:
            payload["context"] = context

        response = await self.client.post("/generate", json=payload)
        response.raise_for_status()
        return response.json()

    async def review_code(
        self,
        code: str,
        language: str = "python",
        focus: str = "security,performance,rgpd",
    ) -> Dict[str, Any]:
        """Revisa código buscando problemas de seguridad, rendimiento y cumplimiento RGPD."""
        response = await self.client.post(
            "/review",
            json={"code": code, "language": language, "focus": focus},
        )
        response.raise_for_status()
        return response.json()

    async def health(self) -> bool:
        """Verifica disponibilidad del servicio Cursor AI."""
        try:
            response = await self.client.get("/health")
            return response.status_code < 400
        except Exception:
            return False


class SabiondaAIClient:
    """
    Cliente SABIONDA IA — motor de decisiones agro-ganadero.
    Modelos: agriculture-v3.1 (análisis de cultivos) | sabionda-governor-v2 (decisiones)
    """

    def __init__(self, config: SabiondaConfig) -> None:
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.endpoint,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=httpx.Timeout(self.config.timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def analyze_crop(
        self,
        sensor_data: Dict[str, Any],
        parcela_sigpac: str,
        cultivo: str,
    ) -> Dict[str, Any]:
        """Análisis de cultivo con datos de sensores IoT usando el modelo agriculture-v3.1."""
        response = await self.client.post(
            "/crop/analyze",
            json={
                "sensor_data": sensor_data,
                "parcela_sigpac": parcela_sigpac,
                "cultivo": cultivo,
                "model": self.config.crop_analysis_model,
            },
        )
        response.raise_for_status()
        return response.json()

    async def irrigation_decision(
        self,
        tension_matricial_cb: float,
        humedad_pct: float,
        cultivo: str,
        temperatura_c: float,
        vpd_kpa: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Decide si activar riego y calcula la dosis óptima.
        Basado en potencial matricial, humedad y VPD.
        """
        payload: Dict[str, Any] = {
            "tension_matricial_cb": tension_matricial_cb,
            "humedad_pct": humedad_pct,
            "cultivo": cultivo,
            "temperatura_c": temperatura_c,
        }
        if vpd_kpa is not None:
            payload["vpd_kpa"] = vpd_kpa

        response = await self.client.post("/irrigation/decision", json=payload)
        response.raise_for_status()
        return response.json()

    async def livestock_health_check(
        self,
        especie: str,
        raza: str,
        temperatura_c: float,
        peso_kg: float,
        estado_productivo: str,
    ) -> Dict[str, Any]:
        """
        Evalúa el estado de salud animal y activa protocolos si detecta anomalías.
        Umbral de fiebre: >39.4°C para razas Retinta/Avileña.
        """
        response = await self.client.post(
            "/livestock/health",
            json={
                "especie": especie,
                "raza": raza,
                "temperatura_c": temperatura_c,
                "peso_kg": peso_kg,
                "estado_productivo": estado_productivo,
                "model": self.config.decision_engine_model,
            },
        )
        response.raise_for_status()
        return response.json()

    async def calculate_ration(
        self,
        especie: str,
        raza: str,
        peso_vivo_kg: float,
        estado_productivo: str,
    ) -> Dict[str, Any]:
        """Calcula ración diaria óptima para especie y condición productiva."""
        response = await self.client.post(
            "/livestock/ration",
            json={
                "especie": especie,
                "raza": raza,
                "peso_vivo_kg": peso_vivo_kg,
                "estado_productivo": estado_productivo,
            },
        )
        response.raise_for_status()
        return response.json()
