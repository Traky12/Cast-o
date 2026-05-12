"""
SABIONDA — Webhook de GitHub con validación HMAC-SHA256

Endpoint:
  - POST /api/v1/github/webhook → Recibe eventos de GitHub y los procesa
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/github", tags=["github"])


def _max_webhook_bytes() -> int:
    return int(os.getenv("GITHUB_WEBHOOK_MAX_BYTES", "1048576"))


# ─── Verificación de firma ────────────────────────────────────────────────────

def _verify_signature(body: bytes, sig_header: str | None, secret: str) -> None:
    """
    Valida la firma HMAC-SHA256 del webhook de GitHub.

    Eleva HTTPException 401 si la firma falta o no coincide.
    Usa hmac.compare_digest para prevenir timing attacks.
    """
    if not sig_header or not sig_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Firma de webhook ausente o malformada")

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    # compare_digest es constante en tiempo → seguro contra timing attacks
    if not hmac.compare_digest(sig_header, expected):
        raise HTTPException(status_code=401, detail="Firma de webhook inválida")


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    x_github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
) -> dict[str, str]:
    """
    Recibe eventos de GitHub. Valida la firma antes de procesar.

    Requiere la variable de entorno GITHUB_WEBHOOK_SECRET.
    Devuelve 401 si la firma es inválida o está ausente.
    """
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        logger.warning("GITHUB_WEBHOOK_SECRET no configurada — webhook rechazado")
        raise HTTPException(
            status_code=503,
            detail="GITHUB_WEBHOOK_SECRET no configurada en el servidor",
        )

    body = await request.body()
    if len(body) > _max_webhook_bytes():
        raise HTTPException(status_code=413, detail="Payload de webhook demasiado grande")

    _verify_signature(body, x_hub_signature_256, secret)

    event = x_github_event or "unknown"
    logger.info("GitHub webhook recibido: event=%s bytes=%d", event, len(body))

    if event == "push":
        await _handle_push(request)
    elif event == "pull_request":
        await _handle_pull_request(request)
    elif event == "issue_comment":
        await _handle_issue_comment(request)
    else:
        logger.debug("Evento GitHub no manejado: %s — ignorado", event)
        return {"status": "ignored", "event": event}

    return {"status": "ok", "event": event}


# ─── Handlers internos ────────────────────────────────────────────────────────

async def _handle_push(request: Request) -> None:
    """Procesa evento push: registra rama y commit."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return
    ref = payload.get("ref", "unknown")
    repo = payload.get("repository", {}).get("full_name", "unknown")
    commits = payload.get("commits", [])
    logger.info(
        "Push en %s ref=%s commits=%d", repo, ref, len(commits)
    )


async def _handle_pull_request(request: Request) -> None:
    """Procesa evento pull_request: registra acción y número de PR."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return
    action = payload.get("action", "unknown")
    pr_number = payload.get("pull_request", {}).get("number", 0)
    title = payload.get("pull_request", {}).get("title", "")
    logger.info("PR #%d action=%s title=%s", pr_number, action, title)


async def _handle_issue_comment(request: Request) -> None:
    """Procesa evento issue_comment."""
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return
    body_text = payload.get("comment", {}).get("body", "")
    issue_number = payload.get("issue", {}).get("number", 0)
    logger.info("Issue comment en #%d: %s", issue_number, body_text[:80])
