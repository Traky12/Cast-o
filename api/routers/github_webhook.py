"""
CASTÚO-SYSTEM™ v3.1 — GitHub Webhook Handler
Recibe eventos de GitHub (push, pull_request, issue_comment, workflow_run)
con validación HMAC-SHA256, publica en Kafka y registra en GaiaChain.

Endpoints:
  POST /api/v1/github/webhook         — Receptor principal de webhooks
  GET  /api/v1/github/events          — Historial de eventos recibidos
  GET  /api/v1/github/status          — Estado de la integración GitHub

Variables de entorno:
    GITHUB_WEBHOOK_SECRET_FILE / GITHUB_WEBHOOK_SECRET  Secreto del webhook
    GITHUB_TOKEN_FILE / GITHUB_TOKEN                    Token de API GitHub
    GITHUB_REPO                                         Repo por defecto (owner/repo)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

logger = logging.getLogger("castuo.github_webhook")

router = APIRouter(prefix="/api/v1/github", tags=["github"])

# ── Secrets ────────────────────────────────────────────────────────────────────

def _read_secret(name: str) -> str:
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            pass
    return os.getenv(name, "")


WEBHOOK_SECRET = _read_secret("GITHUB_WEBHOOK_SECRET")
GITHUB_REPO    = os.getenv("GITHUB_REPO", "traky12/castuo-system")

# En-memoria: últimos 200 eventos recibidos
_event_log: list[dict] = []


# ── Auth admin para /events y /status ─────────────────────────────────────────

_bearer = HTTPBearer(auto_error=False)


def _verify_jwt(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    import jwt as pyjwt
    secret = _read_secret("JWT_SECRET")
    if not secret:
        return {"sub": "dev-mode", "role": "admin"}
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        return pyjwt.decode(credentials.credentials, secret, algorithms=["HS256"])
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


# ── Validación HMAC-SHA256 ─────────────────────────────────────────────────────

def _verify_github_signature(body: bytes, signature_header: str | None) -> bool:
    """
    Verifica la firma X-Hub-Signature-256 del webhook de GitHub.
    Si no hay secreto configurado, acepta todos los eventos (dev-mode).
    """
    if not WEBHOOK_SECRET:
        logger.warning("[github_webhook] Sin GITHUB_WEBHOOK_SECRET — aceptando sin verificación (dev-mode)")
        return True
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature_header, expected)


# ── Handlers por evento ────────────────────────────────────────────────────────

async def _handle_push(payload: dict) -> dict:
    """Procesamiento de evento push: publica en Kafka, registra en blockchain."""
    repo    = payload.get("repository", {}).get("full_name", "unknown")
    commit  = payload.get("after", "")[:8]
    actor   = payload.get("pusher", {}).get("name", "unknown")
    branch  = payload.get("ref", "").replace("refs/heads/", "")
    files_changed = [
        fname
        for c in payload.get("commits", [])
        for fname in (c.get("added", []) + c.get("modified", []) + c.get("removed", []))
        if isinstance(fname, str)
    ]

    result = {
        "action": "push_processed",
        "repo": repo, "commit": commit, "actor": actor,
        "branch": branch, "files_changed": len(files_changed),
    }

    # Publicar en Kafka
    try:
        from services.kafka.kafka_client import get_producer
        get_producer().send_code_update(repo=repo, commit=commit, actor=actor, event="push")
    except Exception as exc:
        logger.warning("[github_webhook] Kafka no disponible: %s", exc)

    # Registrar en blockchain
    try:
        from castuo_graph.skills import registrar_en_blockchain
        tx_hash = registrar_en_blockchain(
            f"GH:push:{repo}:{commit}",
            {"repo": repo, "commit": commit, "actor": actor,
             "branch": branch, "files": files_changed[:10]},
        )
        result["tx_hash"] = tx_hash
    except Exception as exc:
        logger.warning("[github_webhook] GaiaChain no disponible: %s", exc)

    # Registrar en auditoría
    try:
        from services.audit.audit_logger import AuditAction, get_audit_logger
        get_audit_logger().log(
            AuditAction.ACCESO_API, f"push:{commit}", actor, f"github/{repo}",
            {"branch": branch, "files_changed": len(files_changed)},
        )
    except Exception:
        pass

    return result


async def _handle_pull_request(payload: dict) -> dict:
    """Procesamiento de PR: solicita análisis con Claude."""
    action  = payload.get("action", "")
    pr      = payload.get("pull_request", {})
    pr_num  = pr.get("number", 0)
    title   = pr.get("title", "")
    actor   = pr.get("user", {}).get("login", "unknown")
    repo    = payload.get("repository", {}).get("full_name", "unknown")

    result = {
        "action": f"pr_{action}",
        "pr_number": pr_num, "title": title, "actor": actor,
    }

    if action in ("opened", "synchronize"):
        # Publicar evento para análisis asíncrono con Claude/Mistral
        try:
            from services.kafka.kafka_client import KafkaTopic, get_producer
            get_producer().send(
                KafkaTopic.CODE_UPDATES, "github.pull_request",
                {"repo": repo, "pr": pr_num, "title": title, "actor": actor, "action": action},
                key=repo,
            )
        except Exception as exc:
            logger.warning("[github_webhook] Kafka no disponible: %s", exc)

        result["analysis_queued"] = True

    return result


async def _handle_issue_comment(payload: dict) -> dict:
    """Procesamiento de comentarios en issues/PRs."""
    action  = payload.get("action", "")
    comment = payload.get("comment", {}).get("body", "")
    actor   = payload.get("sender", {}).get("login", "unknown")
    issue   = payload.get("issue", {}).get("number", 0)

    # Si el comentario menciona @castuo o /analyze → encolar análisis IA
    analysis_triggered = any(kw in comment.lower() for kw in ("@castuo", "/analyze", "/sabionda"))

    try:
        from services.kafka.kafka_client import KafkaTopic, get_producer
        get_producer().send(
            KafkaTopic.AI_EVENTS, "github.issue_comment",
            {"actor": actor, "issue": issue, "analysis_triggered": analysis_triggered},
        )
    except Exception:
        pass

    return {"action": f"comment_{action}", "issue": issue, "analysis_triggered": analysis_triggered}


async def _handle_workflow_run(payload: dict) -> dict:
    """Registra el resultado de un workflow de GitHub Actions."""
    run    = payload.get("workflow_run", {})
    status = run.get("conclusion", run.get("status", ""))
    name   = run.get("name", "")
    repo   = payload.get("repository", {}).get("full_name", "unknown")

    try:
        from services.kafka.kafka_client import KafkaTopic, get_producer
        get_producer().send(
            KafkaTopic.CODE_UPDATES, "github.workflow_run",
            {"name": name, "status": status, "repo": repo},
        )
    except Exception:
        pass

    return {"workflow": name, "status": status}


_EVENT_HANDLERS = {
    "push":          _handle_push,
    "pull_request":  _handle_pull_request,
    "issue_comment": _handle_issue_comment,
    "workflow_run":  _handle_workflow_run,
}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/webhook", summary="Receptor de webhooks de GitHub")
async def github_webhook(request: Request) -> dict:
    """
    Recibe eventos de GitHub con validación HMAC-SHA256.
    Configura en GitHub: Settings → Webhooks → Add webhook.
    Content type: application/json
    Secret: valor de GITHUB_WEBHOOK_SECRET
    Eventos: push, pull_request, issue_comment, workflow_run
    """
    body = await request.body()

    # Validar firma
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not _verify_github_signature(body, signature or None):
        logger.warning("[github_webhook] Firma inválida — rechazando petición")
        raise HTTPException(status_code=401, detail="Firma del webhook inválida")

    # Parsear payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload no es JSON válido")

    event_type = request.headers.get("X-GitHub-Event", "ping")
    delivery   = request.headers.get("X-GitHub-Delivery", "")
    repo       = payload.get("repository", {}).get("full_name", "unknown")

    now = datetime.now(timezone.utc).isoformat()
    event_record: dict = {
        "event_type":  event_type,
        "delivery_id": delivery,
        "repo":        repo,
        "timestamp":   now,
        "processed":   False,
        "resultado":   {},
    }

    # Ping (verificación de webhook)
    if event_type == "ping":
        event_record["processed"] = True
        event_record["resultado"] = {"zen": payload.get("zen", ""), "hook_id": payload.get("hook_id")}
        _log_event(event_record)
        return {"status": "pong", "zen": payload.get("zen", ""), "hook_id": payload.get("hook_id")}

    # Dispatch al handler
    handler = _EVENT_HANDLERS.get(event_type)
    if handler:
        try:
            resultado = await handler(payload)
            event_record["processed"] = True
            event_record["resultado"] = resultado
            logger.info("[github_webhook] %s procesado desde %s", event_type, repo)
        except Exception as exc:
            logger.error("[github_webhook] Error procesando %s: %s", event_type, exc)
            event_record["resultado"] = {"error": str(exc)}
    else:
        logger.debug("[github_webhook] Evento '%s' ignorado (no hay handler)", event_type)
        event_record["processed"] = False
        event_record["resultado"] = {"note": f"Evento '{event_type}' no procesado"}

    _log_event(event_record)
    return {"status": "ok", "event": event_type, "repo": repo, "processed": event_record["processed"]}


@router.get("/events", summary="Historial de eventos de webhook recibidos")
async def get_events(
    limit: int = 50,
    event_type: str | None = None,
    _jwt: dict = Depends(_verify_jwt),
) -> dict:
    """Retorna los últimos N eventos de webhook recibidos."""
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=422, detail="limit debe estar entre 1 y 200")
    events = _event_log
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    return {
        "total":  len(events),
        "eventos": events[-limit:],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/status", summary="Estado de la integración GitHub")
async def get_status(_jwt: dict = Depends(_verify_jwt)) -> dict:
    """Retorna el estado de la integración: secreto configurado, eventos recibidos, Kafka."""
    try:
        from services.kafka.kafka_client import get_producer
        kafka_ok = get_producer().is_connected
    except Exception:
        kafka_ok = False

    return {
        "webhook_secret_configurado": bool(WEBHOOK_SECRET),
        "repo_configurado":           GITHUB_REPO,
        "eventos_recibidos":          len(_event_log),
        "ultimo_evento":              _event_log[-1] if _event_log else None,
        "kafka_conectado":            kafka_ok,
        "timestamp":                  datetime.now(timezone.utc).isoformat(),
    }


def _log_event(record: dict) -> None:
    _event_log.append(record)
    if len(_event_log) > 200:
        _event_log.pop(0)
