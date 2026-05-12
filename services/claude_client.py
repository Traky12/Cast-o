"""
CASTÚO-SYSTEM™ v3.1 — Claude Client Service
Cliente oficial Anthropic SDK con circuit breaker, reintentos y logging.
Uso: from services.claude_client import ClaudeClient
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

logger = logging.getLogger("castuo.claude_client")


def _read_secret(name: str) -> str:
    path = os.getenv(f"{name}_FILE", "")
    if path:
        try:
            with open(path) as f:
                return f.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


# ── Configuración ────────────────────────────────────────────────────────────
CLAUDE_API_KEY   = _read_secret("CLAUDE_API_KEY")
CLAUDE_MODEL     = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "2048"))
CLAUDE_TIMEOUT   = int(os.getenv("CLAUDE_TIMEOUT_S", "30"))
CLAUDE_MAX_RETRIES = int(os.getenv("CLAUDE_MAX_RETRIES", "3"))
CIRCUIT_THRESHOLD = int(os.getenv("CLAUDE_CIRCUIT_THRESHOLD", "5"))
CIRCUIT_RESET_S  = 60.0

try:
    import anthropic as _anthropic
    _SDK_OK = True
except ImportError:
    _SDK_OK = False
    logger.warning("[claude_client] anthropic SDK no instalado. pip install anthropic>=0.40.0")


# ── Circuit Breaker simple ────────────────────────────────────────────────────
class _Circuit:
    def __init__(self) -> None:
        self._failures = 0
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> str:
        if self._opened_at is None:
            return "CLOSED"
        if time.time() - self._opened_at > CIRCUIT_RESET_S:
            return "HALF-OPEN"
        return "OPEN"

    def is_open(self) -> bool:
        return self.state == "OPEN"

    def ok(self) -> None:
        self._failures = 0
        self._opened_at = None

    def fail(self) -> None:
        self._failures += 1
        if self._failures >= CIRCUIT_THRESHOLD:
            self._opened_at = time.time()
            logger.warning("[claude_client] Circuito ABIERTO tras %d fallos", self._failures)

    def stats(self) -> dict:
        return {"state": self.state, "failures": self._failures}


_circuit = _Circuit()


class ClaudeClient:
    """
    Cliente para la API de Anthropic Claude.
    Usa el SDK oficial, con circuit breaker y reintentos con backoff exponencial.

    Ejemplo rápido:
        client = ClaudeClient()
        resp = client.generate("pH óptimo para lechuga hidropónica")
        print(resp["respuesta"])
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._key = api_key or CLAUDE_API_KEY
        self._available = bool(self._key) and _SDK_OK

    # ── generate ─────────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        *,
        system: str = (
            "Eres SABIONDA, el asistente técnico del sistema agrovoltaico hidropónico "
            "CASTÚO-SYSTEM™. Responde en español, de forma precisa y concisa."
        ),
        max_tokens: int = CLAUDE_MAX_TOKENS,
        temperature: float = 0.3,
        contexto: Optional[str] = None,
    ) -> dict:
        """
        Genera una respuesta de Claude.

        Returns dict with keys: respuesta, modelo, tokens_usados, simulado, latencia_ms
        """
        if not self._available:
            return self._fallback(prompt, contexto)

        if _circuit.is_open():
            logger.warning("[claude_client] Circuito abierto — usando fallback")
            return self._fallback(prompt, contexto)

        delay = 1.0
        for attempt in range(1, CLAUDE_MAX_RETRIES + 1):
            t0 = time.time()
            try:
                client = _anthropic.Anthropic(api_key=self._key, timeout=CLAUDE_TIMEOUT)
                msg = client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )
                texto = msg.content[0].text
                tokens = msg.usage.input_tokens + msg.usage.output_tokens
                _circuit.ok()
                return {
                    "respuesta":     texto,
                    "modelo":        msg.model,
                    "tokens_usados": tokens,
                    "latencia_ms":   round((time.time() - t0) * 1000, 1),
                    "simulado":      False,
                }
            except Exception as exc:
                _circuit.fail()
                logger.warning(
                    "[claude_client] Intento %d/%d falló: %s", attempt, CLAUDE_MAX_RETRIES, exc
                )
                if attempt < CLAUDE_MAX_RETRIES:
                    import random
                    time.sleep(delay + random.uniform(0, 0.5))
                    delay *= 2
                else:
                    logger.error("[claude_client] Agotados reintentos — usando fallback")
                    return self._fallback(prompt, contexto)

        return self._fallback(prompt, contexto)

    # ── review_pr ────────────────────────────────────────────────────────────

    def review_pr(
        self,
        pr_title: str,
        pr_body: str = "",
        diff: str = "",
        repo: str = "traky12/castuo-system",
        pr_number: int = 0,
    ) -> dict:
        """Revisión de Pull Request con Claude."""
        prompt = (
            f"Revisa el siguiente Pull Request del repositorio {repo} #{pr_number}:\n\n"
            f"Título: {pr_title}\n"
            f"Descripción: {pr_body[:3000]}\n\n"
            f"Diff:\n{diff[:15000]}\n\n"
            "Proporciona:\n"
            "1. Resumen de cambios (2-3 frases).\n"
            "2. Problemas detectados (si los hay).\n"
            "3. Sugerencias de mejora.\n"
            "4. Veredicto: APROBADO / REQUIERE CAMBIOS / RECHAZADO."
        )
        system = (
            "Eres un senior engineer revisando código de CASTÚO-SYSTEM™, "
            "un sistema agrovoltaico hidropónico. Sé preciso, técnico y constructivo."
        )
        return self.generate(prompt, system=system, max_tokens=2048, temperature=0.2)

    # ── analyze_sensors ──────────────────────────────────────────────────────

    def analyze_sensors(self, sensor_data: dict) -> dict:
        """Analiza datos de sensores y recomienda acciones."""
        lines = [f"- {k}: {v}" for k, v in sensor_data.items()]
        prompt = (
            "Analiza estos datos de sensores del invernadero hidropónico:\n"
            + "\n".join(lines)
            + "\n\nProporciona recomendaciones de ajuste inmediatas en formato:\n"
            "1. Estado general (OK/ALERTA/CRÍTICO)\n"
            "2. Parámetros fuera de rango\n"
            "3. Acciones recomendadas\n"
            "4. Predicción próximas 2 horas"
        )
        return self.generate(prompt, contexto="agricultura", temperature=0.2)

    # ── status ───────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "sdk_instalado":      _SDK_OK,
            "api_key_configurada": bool(self._key),
            "ia_operativa":       self._available and not _circuit.is_open(),
            "modelo":             CLAUDE_MODEL,
            "circuit_breaker":   _circuit.stats(),
        }

    # ── fallback ─────────────────────────────────────────────────────────────

    @staticmethod
    def _fallback(prompt: str, contexto: Optional[str]) -> dict:
        respuestas = {
            "agricultura": (
                "Parámetros hidropónicos óptimos: pH 5.5-6.5, EC 1.5-3.0 mS/cm, "
                "Tª agua 18-22°C, O₂ disuelto >6 mg/L. Configure CLAUDE_API_KEY para "
                "análisis personalizado en tiempo real."
            ),
            "codigo": (
                "Análisis de código no disponible (CLAUDE_API_KEY no configurada). "
                "Configure la clave en .env para activar revisión automática de PRs."
            ),
            "normativo": (
                "Consulta normativa no disponible en modo offline. "
                "Configure CLAUDE_API_KEY para acceder a SABIONDA IA completa."
            ),
        }
        texto = respuestas.get(
            contexto or "",
            "SABIONDA IA en modo local. Configure CLAUDE_API_KEY en .env para activar "
            f"la IA completa. Consulta recibida: {prompt[:120]}…",
        )
        return {
            "respuesta":     texto,
            "modelo":        "local-fallback",
            "tokens_usados": 0,
            "latencia_ms":   0.0,
            "simulado":      True,
        }


# ── Instancia global ──────────────────────────────────────────────────────────
_default_client: Optional[ClaudeClient] = None


def get_client() -> ClaudeClient:
    """Devuelve el cliente singleton (útil para FastAPI Depends)."""
    global _default_client
    if _default_client is None:
        _default_client = ClaudeClient()
    return _default_client
