"""
SABIONDA — Análisis IA con Mistral

Endpoint:
  - POST /api/v1/mistral/analyze → Analiza texto agrícola con Mistral AI
"""
from __future__ import annotations

import logging
import os
from typing import Any, cast

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from security.rbac import authorize_token, token_from_authorization_header
    from services.ethics_policy import enforce_ethical_equity_text
except ModuleNotFoundError:  # pragma: no cover
    from api.security.rbac import authorize_token, token_from_authorization_header
    from api.services.ethics_policy import enforce_ethical_equity_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mistral", tags=["mistral"])
_PRIVILEGED_ROLES = {
    "admin_general",
    "administrador",
    "ciso",
    "cumplimiento",
    "devops",
}


def _require_privileged_access(authorization: str | None) -> None:
    runtime_env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    if runtime_env != "production":
        return
    token = token_from_authorization_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authorization Bearer requerido para Mistral")
    authorize_token(token, _PRIVILEGED_ROLES)


def _require_mistral_enabled() -> None:
    runtime_env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    if runtime_env != "production":
        return
    if os.getenv("ENABLE_MISTRAL_INTEGRATION", "false").strip().lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        raise HTTPException(
            status_code=503,
            detail="Integración Mistral deshabilitada por política",
        )


# ─── Modelos ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Texto a analizar con Mistral AI")


class AnalyzeResponse(BaseModel):
    analysis: str
    model: str = "mistral-small"


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_with_mistral(
    request: AnalyzeRequest,
    authorization: str | None = Header(default=None),
) -> AnalyzeResponse:
    """
    Analiza o genera contenido con Mistral AI.

    La API key se lee de la variable de entorno MISTRAL_API_KEY.
    Devuelve 503 si el conector falla.
    """
    _require_privileged_access(authorization)
    _require_mistral_enabled()
    enforce_ethical_equity_text(request.text, context="/api/v1/mistral/analyze")

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="MISTRAL_API_KEY no configurada. Añade la clave al entorno.",
        )

    try:
        from castuo_graph.ai.mistral_connector import MistralConnector  # noqa: PLC0415

        connector = MistralConnector(api_key=api_key)
        # El conector espera un dict con campo 'text' como mínimo
        agricultural_data: dict[str, Any] = {
            "humidity": 0,
            "temperature": 0,
            "soil_ph": 0,
            "text_query": request.text,
        }
        result: dict[str, Any] = connector.analyze_agricultural_data(agricultural_data)

        # Extraer contenido de la respuesta (formato OpenAI-like de Mistral)
        analysis_text: str = _extract_content(result)
        model_id = str(result.get("model", "mistral-small"))

        logger.info("Mistral análisis completado. model=%s", model_id)
        return AnalyzeResponse(analysis=analysis_text, model=model_id)

    except Exception as exc:
        logger.error("Error llamando a Mistral: %s", exc)
        raise HTTPException(status_code=503, detail=f"Error de Mistral: {exc}")


def _extract_content(result: dict[str, Any]) -> str:
    """Extrae el texto del la respuesta de Mistral (choices[0].message.content)."""
    choices = cast(list[Any], result.get("choices", []))
    if not choices:
        return str(result)

    first = choices[0]
    if not isinstance(first, dict):
        return str(result)

    first_dict = cast(dict[str, Any], first)
    message = cast(dict[str, Any], first_dict.get("message", {}))
    return str(message.get("content", ""))
