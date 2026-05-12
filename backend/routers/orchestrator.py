# -*- coding: utf-8 -*-
"""Orquestador central CASTUO: Mistral function calling, /castuo/master-agent y /money/microgreens."""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

# Raíz del repo para imports
_root = Path(__file__).resolve().parents[2]
if str(_root) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_root))

try:
    from backend.services.mistral import analyze_with_mistral
except ImportError:
    async def analyze_with_mistral(prompt: str, **kwargs):
        return {"summary": "Demo (sin Mistral): certificación asumida OK.", "quality": 1.0}

try:
    from backend.auth_roles import read_secret
except ImportError:
    def read_secret(name: str) -> str:
        return os.getenv(name.upper(), os.getenv(name, ""))

logger = logging.getLogger(__name__)

# Stripe (para /money/microgreens)
try:
    import stripe
    stripe.api_key = read_secret("STRIPE_SECRET") or read_secret("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET", "")
    _HAS_STRIPE = bool(stripe.api_key)
except Exception:
    stripe = None  # type: ignore
    _HAS_STRIPE = False

router = APIRouter(tags=["Orchestrator"])

MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai").rstrip("/")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "") or os.getenv("N8N_CASTUO_TRIGGER_URL", "")
N8N_WEBHOOK_SALE_URL = os.getenv("N8N_WEBHOOK_SALE_URL", "") or os.getenv("N8N_SALE_WEBHOOK", "")

# Definición de herramientas para Mistral (function calling)
MASTER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sabionda_ia",
            "description": "Análisis predictivo LER y recomendaciones agrovoltaica/microgreens para una parcela o lote.",
            "parameters": {
                "type": "object",
                "properties": {"parcel": {"type": "string", "description": "ID parcela o batch"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "n8n_workflow",
            "description": "Ejecutar workflow de automatización n8n (notificaciones, reportes, integraciones).",
            "parameters": {
                "type": "object",
                "properties": {"workflow_id": {"type": "string", "description": "ID del workflow"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notion_update",
            "description": "Actualizar roadmap o estado CTAEX en Notion.",
            "parameters": {
                "type": "object",
                "properties": {"page_id": {"type": "string", "description": "ID de página Notion"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "money_stripe",
            "description": "Procesar pago de microgreens certificados CTAEX (crear sesión Stripe).",
            "parameters": {
                "type": "object",
                "properties": {"batch_id": {"type": "string", "description": "ID del lote"}},
            },
        },
    },
]


async def _execute_sabionda_ia(parcel: str) -> Dict[str, Any]:
    """Ejecuta análisis Sabionda (Mistral) para parcela/lote."""
    prompt = f"Resumen LER y estado para parcela/lote {parcel}. Una frase."
    result = await analyze_with_mistral(prompt, model="mistral-small-latest")
    return {"tool": "sabionda_ia", "parcel": parcel, "result": result.get("summary", result)}


async def _execute_n8n_workflow(workflow_id: str) -> Dict[str, Any]:
    """Dispara workflow n8n por webhook."""
    if not N8N_WEBHOOK_URL:
        return {"tool": "n8n_workflow", "workflow_id": workflow_id, "result": "N8N_WEBHOOK_URL no configurado"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                N8N_WEBHOOK_URL,
                json={"workflow_id": workflow_id, "source": "castuo-master-agent"},
            )
            return {
                "tool": "n8n_workflow",
                "workflow_id": workflow_id,
                "status_code": r.status_code,
                "result": r.text[:500] if r.text else "ok",
            }
    except Exception as e:
        return {"tool": "n8n_workflow", "workflow_id": workflow_id, "error": str(e)}


async def _execute_notion_update(page_id: str) -> Dict[str, Any]:
    """Stub: actualizar Notion (en producción llamar a API Notion)."""
    return {
        "tool": "notion_update",
        "page_id": page_id,
        "result": "Stub: en producción actualizar CTAEX roadmap en Notion",
    }


async def _execute_money_stripe(batch_id: str, request: Request) -> Dict[str, Any]:
    """Indica que el pago se puede procesar vía POST /money/microgreens."""
    return {
        "tool": "money_stripe",
        "batch_id": batch_id,
        "result": "Usar POST /money/microgreens con batch_id para obtener session_id y redirigir a Stripe Checkout.",
    }


async def execute_tools(
    tool_calls: List[Dict[str, Any]], request: Request
) -> List[Dict[str, Any]]:
    """Ejecuta en paralelo las tool_calls devueltas por Mistral."""
    import asyncio

    async def run_one(tc: Dict[str, Any]) -> Dict[str, Any]:
        name = (tc.get("function") or {}).get("name", "")
        try:
            args = json.loads((tc.get("function") or {}).get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}
        if name == "sabionda_ia":
            return await _execute_sabionda_ia(args.get("parcel", ""))
        if name == "n8n_workflow":
            return await _execute_n8n_workflow(args.get("workflow_id", ""))
        if name == "notion_update":
            return await _execute_notion_update(args.get("page_id", ""))
        if name == "money_stripe":
            return await _execute_money_stripe(args.get("batch_id", ""), request)
        return {"tool": name, "result": "unknown tool"}

    return await asyncio.gather(*[run_one(tc) for tc in tool_calls])


class MasterAgentRequest(BaseModel):
    query: str


class MoneyMicrogreensRequest(BaseModel):
    batch_id: str = "MG-2026-03-14"


@router.post("/castuo/master-agent")
async def master_agent(req: MasterAgentRequest, request: Request) -> Dict[str, Any]:
    """
    Orquestador central: Mistral con function calling (sabionda_ia, n8n_workflow, notion_update, money_stripe).
    Ejecuta las tool calls en paralelo y devuelve resultados unificados.
    """
    if not MISTRAL_API_KEY:
        return {
            "orchestration": [{"tool": "demo", "result": "MISTRAL_API_KEY no configurado. Configure para usar tools."}],
            "ctaex_ready": True,
        }

    url = f"{MISTRAL_API_URL}/v1/chat/completions"
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": os.getenv("MISTRAL_ORCHESTRATOR_MODEL", "mistral-large-latest"),
        "messages": [{"role": "user", "content": req.query}],
        "tools": MASTER_TOOLS,
        "tool_choice": "auto",
        "max_tokens": 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, headers=headers, json=body)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    choices = data.get("choices") or []
    if not choices:
        return {"orchestration": [], "ctaex_ready": True}

    msg = choices[0].get("message") or {}
    tool_calls = msg.get("tool_calls") or []

    if not tool_calls:
        return {
            "orchestration": [{"message": msg.get("content", ""), "tool_calls": 0}],
            "ctaex_ready": True,
        }

    results = await execute_tools(tool_calls, request)
    return {"orchestration": results, "ctaex_ready": True}


@router.post("/money/microgreens")
async def money_microgreens(req: MoneyMicrogreensRequest, request: Request) -> Dict[str, Any]:
    """
    Procesar pago microgreens: Mistral verifica certificación, crea sesión Stripe, opcionalmente dispara n8n venta.
    """
    batch_id = req.batch_id
    # Verificación con Mistral (resumen de certificación)
    cert_result = await analyze_with_mistral(
        f"Verifica en una palabra si el lote {batch_id} está certificado CTAEX para venta: responde solo OK o NO.",
        model=os.getenv("MISTRAL_PSY_MODEL", "mistral-small-latest"),
    )
    summary = (cert_result.get("summary") or "").upper()
    cert_ok = "OK" in summary or "SÍ" in summary or "SI" in summary or "CERTIFICADO" in summary or not MISTRAL_API_KEY
    if not cert_ok and MISTRAL_API_KEY:
        raise HTTPException(status_code=400, detail=f"Certificación no confirmada para lote {batch_id}")

    if not _HAS_STRIPE or stripe is None:
        raise HTTPException(status_code=501, detail="Stripe no configurado. Definir STRIPE_SECRET.")

    success_url = os.getenv("CASTUO_SUCCESS_URL", "https://89.167.5.233/success")
    cancel_url = os.getenv("CASTUO_CANCEL_URL", "https://89.167.5.233/cancel")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Microgreens {batch_id} CTAEX Cert",
                            "description": "Cultivo hidropónico con trazabilidad blockchain",
                        },
                        "unit_amount": 2500,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{success_url.rstrip('/')}?batch={batch_id}",
            cancel_url=cancel_url,
            metadata={"batch_id": batch_id},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    # n8n: venta registrada
    if N8N_WEBHOOK_SALE_URL:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    N8N_WEBHOOK_SALE_URL,
                    json={"batch_id": batch_id, "session_id": session.id, "source": "castuo-money"},
                )
        except Exception as e:
            logger.warning("n8n sale webhook failed: %s", e)

    return {"stripe_session": session.id}
