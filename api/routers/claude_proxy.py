"""
CASTÚO-SYSTEM™ v3.1 — Claude (Anthropic) Proxy
Proxy seguro hacia la API de Anthropic con circuit breaker, caché de respuestas,
trazabilidad Kafka y fallback a reglas locales.

Endpoints:
  POST /api/v1/claude/generate      — Generación de texto / análisis de código
  POST /api/v1/claude/review-pr     — Revisión de Pull Request con Claude
  GET  /api/v1/claude/status        — Estado del circuito y uso de tokens

Variables de entorno:
    CLAUDE_API_KEY_FILE / CLAUDE_API_KEY   Clave de API de Anthropic
    CLAUDE_MODEL                           Modelo (default: claude-sonnet-4-6)
    CLAUDE_MAX_TOKENS                      Tokens máximos por respuesta (default: 2048)
    CLAUDE_TIMEOUT_S                       Timeout en segundos (default: 30)
    CLAUDE_CIRCUIT_THRESHOLD               Fallos antes de abrir circuito (default: 5)
"""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger("castuo.claude_proxy")

router = APIRouter(prefix="/api/v1/claude", tags=["claude"])
_bearer = HTTPBearer(auto_error=False)


# ── Secrets ────────────────────────────────────────────────────────────────────

def _read_secret(name: str) -> str:
    path = os.getenv(f"{name}_FILE", "")
    if path:
        try:
            with open(path) as f:
                return f.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


CLAUDE_API_KEY = _read_secret("CLAUDE_API_KEY")
CLAUDE_MODEL   = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
CLAUDE_MAX_TOK = int(os.getenv("CLAUDE_MAX_TOKENS", "2048"))
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT_S", "30"))
CIRCUIT_THRESH = int(os.getenv("CLAUDE_CIRCUIT_THRESHOLD", "5"))

_SDK_INSTALLED = False
try:
    import anthropic as _anthropic  # type: ignore
    _SDK_INSTALLED = True
    _ANTHROPIC_AVAILABLE = bool(CLAUDE_API_KEY)
    if not CLAUDE_API_KEY:
        logger.info("[claude_proxy] anthropic SDK instalado — CLAUDE_API_KEY no configurada, modo fallback")
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    logger.info("[claude_proxy] anthropic SDK no instalado — modo fallback activo")


# ── Circuit Breaker ────────────────────────────────────────────────────────────

class _CircuitBreaker:
    """Circuit breaker simple: CLOSED → OPEN → HALF-OPEN."""
    HALF_OPEN_DELAY = 60.0  # segundos antes de reintentar

    def __init__(self, threshold: int = CIRCUIT_THRESH) -> None:
        self._failures   = 0
        self._threshold  = threshold
        self._opened_at: float | None = None
        self._total_calls  = 0
        self._total_ok     = 0
        self._total_errors = 0
        self._total_tokens = 0

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "CLOSED"
        if time.time() - self._opened_at > self.HALF_OPEN_DELAY:
            return "HALF-OPEN"
        return "OPEN"

    def call_ok(self, tokens: int = 0) -> None:
        self._failures = 0
        self._opened_at = None
        self._total_ok += 1
        self._total_tokens += tokens
        self._total_calls += 1

    def call_fail(self) -> None:
        self._failures += 1
        self._total_errors += 1
        self._total_calls += 1
        if self._failures >= self._threshold:
            self._opened_at = time.time()
            logger.warning(
                "[claude_proxy] Circuito ABIERTO tras %d fallos consecutivos",
                self._failures,
            )

    def is_open(self) -> bool:
        return self.state == "OPEN"

    def stats(self) -> dict:
        return {
            "estado":          self.state,
            "fallos_seguidos": self._failures,
            "total_llamadas":  self._total_calls,
            "ok":              self._total_ok,
            "errores":         self._total_errors,
            "tokens_acumulados": self._total_tokens,
        }


_circuit = _CircuitBreaker()


# ── Auth ───────────────────────────────────────────────────────────────────────

def _verify_jwt(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    import jwt as pyjwt
    secret = _read_secret("JWT_SECRET")
    if not secret:
        return {"sub": "dev-mode", "role": "admin"}
    if not credentials:
        raise HTTPException(status_code=401, detail="Token JWT requerido")
    try:
        payload = pyjwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if payload.get("role") not in ("admin", "editor", "api"):
        raise HTTPException(status_code=403, detail="Sin permiso para usar Claude proxy")
    return payload


# ── Modelos ────────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000)
    system: str = Field(
        "Eres SABIONDA, el asistente técnico del sistema agrovoltaico hidropónico CASTÚO-SYSTEM™. "
        "Responde en español, de forma precisa, técnica y concisa.",
    )
    max_tokens: int = Field(CLAUDE_MAX_TOK, ge=1, le=8192)
    temperature: float = Field(0.3, ge=0.0, le=1.0)
    contexto: Optional[str] = Field(None, description="Contexto adicional: 'codigo' | 'agricultura' | 'normativo'")


class ReviewPRRequest(BaseModel):
    pr_title:   str = Field(..., max_length=500)
    pr_body:    str = Field("", max_length=5000)
    diff:       str = Field("", max_length=20000, description="Diff del PR (opcional)")
    repo:       str = Field("traky12/castuo-system")
    pr_number:  int = Field(0, ge=0)


class ClaudeResponse(BaseModel):
    respuesta:    str
    modelo:       str
    tokens_usados: int
    latencia_ms:  float
    simulado:     bool
    timestamp:    str


# ── Llamada a Anthropic ────────────────────────────────────────────────────────

def _call_anthropic(system: str, prompt: str, max_tokens: int, temperature: float) -> tuple[str, int]:
    """Llama a la API de Anthropic. Retorna (texto, tokens_usados)."""
    client = _anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = message.content[0].text
    tokens = message.usage.input_tokens + message.usage.output_tokens
    return texto, tokens


def _fallback_response(prompt: str, contexto: str | None) -> str:
    """Respuesta local cuando Anthropic no está disponible."""
    if contexto == "codigo":
        return (
            "Análisis de código no disponible (Claude API no configurado). "
            "Configure CLAUDE_API_KEY para activar el análisis automático."
        )
    if contexto == "normativo":
        return (
            "Consulta normativa no disponible offline. "
            "Revisar documentación en docs/DEPLOYMENT.md y docs/API.md."
        )
    # Análisis básico por palabras clave
    prompt_lower = prompt.lower()
    if any(w in prompt_lower for w in ("ph", "ec", "nutrient")):
        return "Parámetros hidropónicos: pH óptimo 5.5-6.5, EC 1.5-3.0 mS/cm según cultivo."
    if any(w in prompt_lower for w in ("temperatura", "co2", "humedad")):
        return "Clima invernadero: temperatura 18-28°C, CO₂ 800-1200 ppm, HR 40-70%."
    if any(w in prompt_lower for w in ("solar", "agrovolt", "panel")):
        return "Sistema agrovoltaico: cobertura sombra <40%, temperatura panel <75°C."
    return "Asistente SABIONDA no disponible en modo offline. Configure CLAUDE_API_KEY."


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=ClaudeResponse,
             summary="Generar respuesta con Claude (Anthropic)")
async def generate(
    req: GenerateRequest,
    _jwt: dict = Depends(_verify_jwt),
) -> ClaudeResponse:
    """
    Proxy hacia la API de Anthropic con circuit breaker y fallback local.
    Si el circuito está OPEN, retorna respuesta local sin llamar a Anthropic.
    """
    t0 = time.time()
    now = datetime.now(timezone.utc).isoformat()
    simulado = False

    if _ANTHROPIC_AVAILABLE and not _circuit.is_open():
        try:
            respuesta, tokens = _call_anthropic(
                req.system, req.prompt, req.max_tokens, req.temperature
            )
            _circuit.call_ok(tokens)

            # Publicar evento en Kafka
            try:
                from services.kafka.kafka_client import get_producer
                get_producer().send_ai_event(
                    model=CLAUDE_MODEL, action="generate",
                    tokens=tokens, latency_ms=round((time.time() - t0) * 1000, 1),
                )
            except Exception:
                pass

            return ClaudeResponse(
                respuesta=respuesta,
                modelo=CLAUDE_MODEL,
                tokens_usados=tokens,
                latencia_ms=round((time.time() - t0) * 1000, 1),
                simulado=False,
                timestamp=now,
            )
        except Exception as exc:
            _circuit.call_fail()
            logger.warning("[claude_proxy] Error llamando a Anthropic: %s", exc)

    # Fallback local
    simulado = True
    respuesta = _fallback_response(req.prompt, req.contexto)
    return ClaudeResponse(
        respuesta=respuesta,
        modelo="local-fallback",
        tokens_usados=0,
        latencia_ms=round((time.time() - t0) * 1000, 1),
        simulado=True,
        timestamp=now,
    )


@router.post("/review-pr", response_model=ClaudeResponse,
             summary="Revisión de Pull Request con Claude")
async def review_pr(
    req: ReviewPRRequest,
    _jwt: dict = Depends(_verify_jwt),
) -> ClaudeResponse:
    """
    Solicita a Claude una revisión técnica del PR con título, descripción y diff.
    Resultado publicado en Kafka (topic: ai_events) para comentario automático en GitHub.
    """
    system = (
        "Eres un revisor senior de código especializado en Python, FastAPI, Kubernetes "
        "y sistemas agrovoltaicos hidropónicos. Revisa el PR y proporciona:\n"
        "1. Resumen del cambio (2-3 frases)\n"
        "2. Problemas críticos (si los hay)\n"
        "3. Sugerencias de mejora (máximo 3)\n"
        "4. Veredicto: APROBAR | CAMBIOS SOLICITADOS | BLOQUEANTE\n"
        "Responde en español, máximo 500 palabras."
    )
    prompt = (
        f"PR #{req.pr_number} en {req.repo}\n"
        f"Título: {req.pr_title}\n"
        f"Descripción: {req.pr_body}\n"
        + (f"\nDiff:\n```\n{req.diff[:15000]}\n```" if req.diff else "")
    )

    t0 = time.time()
    now = datetime.now(timezone.utc).isoformat()

    if _ANTHROPIC_AVAILABLE and not _circuit.is_open():
        try:
            respuesta, tokens = _call_anthropic(system, prompt, min(req.pr_number, CLAUDE_MAX_TOK) or CLAUDE_MAX_TOK, 0.2)
            _circuit.call_ok(tokens)

            # Publicar revisión en Kafka para comentario automático en GitHub
            try:
                from services.kafka.kafka_client import KafkaTopic, get_producer
                get_producer().send(
                    KafkaTopic.AI_EVENTS, "claude.pr_review",
                    {"repo": req.repo, "pr": req.pr_number, "review": respuesta[:500]},
                )
            except Exception:
                pass

            return ClaudeResponse(
                respuesta=respuesta,
                modelo=CLAUDE_MODEL,
                tokens_usados=tokens,
                latencia_ms=round((time.time() - t0) * 1000, 1),
                simulado=False,
                timestamp=now,
            )
        except Exception as exc:
            _circuit.call_fail()
            logger.warning("[claude_proxy] Error en review-pr: %s", exc)

    return ClaudeResponse(
        respuesta=(
            f"Revisión automática no disponible. PR #{req.pr_number}: '{req.pr_title}'. "
            "Configure CLAUDE_API_KEY para análisis automático de PRs."
        ),
        modelo="local-fallback",
        tokens_usados=0,
        latencia_ms=round((time.time() - t0) * 1000, 1),
        simulado=True,
        timestamp=now,
    )


@router.get("/status", summary="Estado del circuit breaker y uso de tokens")
async def get_status(_jwt: dict = Depends(_verify_jwt)) -> dict:
    """Estado del circuit breaker, tokens acumulados y disponibilidad de Anthropic."""
    return {
        "anthropic_configurado": bool(CLAUDE_API_KEY),
        "sdk_disponible":        _SDK_INSTALLED,
        "ia_operativa":          _ANTHROPIC_AVAILABLE,
        "modelo":                CLAUDE_MODEL,
        "circuit_breaker":       _circuit.stats(),
        "timestamp":             datetime.now(timezone.utc).isoformat(),
    }
