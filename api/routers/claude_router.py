"""
SABIONDA — Integración con Claude (Anthropic)

Endpoints:
  - POST /api/v1/claude/generate → Genera texto/código con Claude
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
router = APIRouter(prefix="/api/v1/claude", tags=["claude"])

_CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1024"))
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
        raise HTTPException(status_code=401, detail="Authorization Bearer requerido para Claude")
    authorize_token(token, _PRIVILEGED_ROLES)


def _require_claude_enabled() -> None:
    runtime_env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()
    if runtime_env != "production":
        return
    if os.getenv("ENABLE_CLAUDE_INTEGRATION", "false").strip().lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        raise HTTPException(
            status_code=503,
            detail="Integración Claude deshabilitada por política",
        )


# ─── Modelos ──────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Texto de entrada para Claude")
    max_tokens: int = Field(default=_MAX_TOKENS, ge=1, le=4096)
    system: str = Field(
        default=(
            "Eres SABIONDA, asistente técnico especializado en agricultura "
            "agrovoltaica, trazabilidad y cumplimiento normativo europeo."
        ),
        description="Instrucción de sistema para Claude",
    )


class GenerateResponse(BaseModel):
    response: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GenerateResponse)
async def generate_with_claude(
    request: GenerateRequest,
    authorization: str | None = Header(default=None),
) -> GenerateResponse:
    """
    Genera texto con Claude enviando un prompt.

    La API key se lee de la variable de entorno CLAUDE_API_KEY.
    Devuelve 503 si el SDK de Anthropic no está disponible o la llamada falla.
    """
    _require_privileged_access(authorization)
    _require_claude_enabled()
    enforce_ethical_equity_text(request.prompt, context="/api/v1/claude/generate")

    api_key = os.getenv("CLAUDE_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="CLAUDE_API_KEY no configurada. Añade la clave al entorno.",
        )

    try:
        import anthropic  # importación diferida — opcional en runtime

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=request.max_tokens,
            system=request.system,
            messages=[{"role": "user", "content": request.prompt}],
        )

        text_content: str = ""
        for block in message.content:
            block_text = cast(Any, getattr(block, "text", None))
            if isinstance(block_text, str):
                text_content = block_text
                break

        usage = getattr(message, "usage", None)
        in_tok = getattr(usage, "input_tokens", 0) if usage else 0
        out_tok = getattr(usage, "output_tokens", 0) if usage else 0

        logger.info(
            "Claude generate: model=%s tokens_in=%d tokens_out=%d",
            _CLAUDE_MODEL,
            in_tok,
            out_tok,
        )

        return GenerateResponse(
            response=text_content,
            model=_CLAUDE_MODEL,
            input_tokens=in_tok,
            output_tokens=out_tok,
        )

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="SDK de Anthropic no instalado. Ejecuta: pip install anthropic",
        )
    except Exception as exc:
        logger.error("Error llamando a Claude: %s", exc)
        raise HTTPException(status_code=503, detail=f"Error de Claude: {exc}")
