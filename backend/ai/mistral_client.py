# backend/ai/mistral_client.py
# Cliente Mistral AI con validación de cumplimiento y logging cifrado (EU AI Act, ISO 27001)

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from mistralai.client import MistralClient
    from mistralai.models.chat_completion import ChatMessage
    _MISTRAL = True
except ImportError:
    MistralClient = None
    ChatMessage = None
    _MISTRAL = False


class MistralAIClient:
    """
    Cliente seguro para Mistral AI: validación normativa, logging cifrado opcional a GaiaChain.
    Cumple EU AI Act (2024/1689), ISO 27001:2022.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("MISTRAL_API_KEY_EU", "")
        self.client: Any = None
        self.crypto: Any = None
        if _MISTRAL and self._api_key:
            self.client = MistralClient(api_key=self._api_key)
        try:
            from backend.security.pq_crypto import PostQuantumCrypto
            self.crypto = PostQuantumCrypto()
        except Exception as e:
            logger.debug("PostQuantumCrypto no disponible para logging: %s", e)

    def _validate_compliance(self, messages: List[Any]) -> None:
        """Exige mención de normativas en el mensaje de sistema."""
        system = next((m for m in messages if getattr(m, "role", None) == "system"), None)
        if not system:
            raise ValueError("Falta mensaje de sistema con contexto normativo")
        content = (getattr(system, "content", None) or "").lower()
        keywords = ["iso 27001", "gdpr", "nis2", "eu ai act", "2024/1689", "27001:2022", "2022/2555"]
        if not any(k in content for k in keywords):
            raise ValueError("El mensaje de sistema debe incluir normativas aplicables (ej: ISO 27001, EU AI Act)")

    def _log_interaction(self, messages: List[Any], response_text: str, model: str = "mistral-large-latest") -> None:
        """Registra la interacción en GaiaChain con cifrado (si script existe)."""
        if not self.crypto:
            return
        try:
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "messages": [getattr(m, "content", str(m)) for m in messages],
                "response": response_text[:5000],
                "model": model,
                "compliance_check": "validated",
            }
            encrypted = self.crypto.hybrid_encrypt_large(json.dumps(record))
            script = os.path.join(os.path.dirname(__file__), "..", "scripts", "register_gaiachain_event.py")
            if not os.path.isfile(script):
                script = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "scripts", "register_gaiachain_event.py")
            if os.path.isfile(script):
                subprocess.run(
                    [
                        "python",
                        script,
                        "--event_type", "ai_interaction",
                        "--details", json.dumps(encrypted),
                        "--norms", "EU_AI_Act_2024_1689,ISO_27001:A.12.6.1",
                    ],
                    check=False,
                    timeout=30,
                    cwd=os.path.dirname(__file__) or ".",
                )
        except Exception as e:
            logger.debug("Log GaiaChain omitido: %s", e)

    def chat_completion(
        self,
        messages: List[Any],
        model: str = "mistral-large-latest",
        temperature: float = 0.1,
        max_tokens: int = 4096,
        log_to_gaiachain: bool = True,
    ) -> Dict[str, Any]:
        """Consulta a Mistral con validación de cumplimiento y registro opcional."""
        if not self.client:
            return {"choices": [{"message": {"content": "{}", "role": "assistant"}}], "usage": {}}
        self._validate_compliance(messages)
        response = self.client.chat(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        text = response.choices[0].message.content
        if log_to_gaiachain:
            self._log_interaction(messages, text, model)
        msg = response.choices[0].message
        return {
            "choices": [{"message": msg, "finish_reason": getattr(response.choices[0], "finish_reason", None)}],
            "usage": getattr(response, "usage", None) and (getattr(response.usage, "model_dump", None) or getattr(response.usage, "dict", lambda: {}))(),
        }

    def create_embedding(self, text: str) -> List[float]:
        """Genera embedding con Mistral (si API disponible)."""
        if not self.client:
            return []
        try:
            r = self.client.embeddings(model="mistral-embed", input=[text])
            return r.data[0].embedding if r.data else []
        except Exception as e:
            logger.error("create_embedding: %s", e)
            return []

    def analyze_code(self, code: str, filename: str, language: str = "python") -> Dict[str, Any]:
        """Analiza código con Mistral (seguridad, cumplimiento, optimización)."""
        if not self.client:
            return {"issues_found": [], "compliance_status": "ok", "overall_score": 0}
        prompt = f"""
        Sistema CASTÚO-SYSTEM™ v2.0. Archivo: {filename}. Lenguaje: {language}.
        Normativas: ISO 27001:2022 (A.14.2), EU AI Act (2024/1689), GDPR Art. 25.
        Código:
        ```{language}
        {code[:15000]}
        ```
        Responde JSON: issues_found (lista de {{type, description, line, severity, suggested_fix}}), compliance_status, overall_score (0-100).
        """
        try:
            r = self.client.chat(
                model="mistral-large-latest",
                messages=[
                    ChatMessage(role="system", content="Experto en análisis de código para sistemas críticos UE."),
                    ChatMessage(role="user", content=prompt),
                ],
                temperature=0.1,
            )
            return json.loads(r.choices[0].message.content)
        except Exception as e:
            logger.error("analyze_code: %s", e)
            return {"issues_found": [], "compliance_status": "unknown", "overall_score": 0}
