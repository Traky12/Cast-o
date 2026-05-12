"""
Grafo lineal: ingestar payload → Mistral (si hay clave) → hash trazabilidad → GaiaChain/Slack opcionales.

Los endpoints externos solo se llaman si existen variables de entorno; no se inventan URLs de producción.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from typing import Any, TypedDict

import httpx

try:
    from langgraph.graph import END, START, StateGraph
except ImportError as exc:  # pragma: no cover - entorno sin langgraph
    raise ImportError(
        "Instala langgraph y langchain-core: pip install langgraph langchain-core"
    ) from exc


class CastuoGraphState(TypedDict, total=False):
    payload: dict[str, Any]
    analysis: str
    trace_hash: str
    gaia_http_status: int | None
    gaia_body: str
    slack_http_status: int | None
    errors: list[str]


async def _node_ingest(state: CastuoGraphState) -> CastuoGraphState:
    raw = state.get("payload")
    if not isinstance(raw, dict):
        return {"payload": {}, "errors": ["payload debe ser un objeto JSON"]}
    return {"payload": raw, "errors": []}


def _svg_excerpt_from_payload(payload: dict[str, Any], max_chars: int = 6000) -> str:
    b64 = payload.get("svg_base64")
    if not isinstance(b64, str) or not b64.strip():
        return ""
    try:
        raw = base64.b64decode(b64, validate=False)[:18000]
        return raw.decode("utf-8", errors="replace")[:max_chars]
    except Exception:
        return b64.strip()[:max_chars]


def _mistral_messages_agri(payload: dict[str, Any]) -> tuple[str, str]:
    system = (
        "Eres agrónomo UE. Respuestas breves y técnicas. "
        "Sin diagnóstico médico. Sin cifras inventadas."
    )
    user = f"Analiza estos datos de cultivo / finca (JSON): {json.dumps(payload, ensure_ascii=False)}"
    return system, user


def _mistral_messages_qelectrotech_svg(payload: dict[str, Any]) -> tuple[str, str]:
    meta = {k: v for k, v in payload.items() if k not in ("svg_base64", "dxf_base64")}
    svg = _svg_excerpt_from_payload(payload)
    system = (
        "Eres ingeniero eléctrico/automatización UE (IEC 61131-3 ST). "
        "No afirmes certificaciones CTAEX/DIN/UNE sin evidencia en el propio esquema. "
        "Responde con un único objeto JSON válido (sin bloques markdown)."
    )
    user = (
        "Metadatos del proyecto (JSON): "
        f"{json.dumps(meta, ensure_ascii=False)}\n"
        f"Fragmento de diagrama (SVG truncado por tamaño):\n{svg or '(sin SVG)'}\n"
        "Devuelve JSON con claves: "
        '"plc_code" (string Structured Text esquemático), '
        '"energy_analysis" (objeto con al menos summary:string y notes:array de strings), '
        '"svg_notes" (string con mejoras sugeridas al diagrama).'
    )
    return system, user


def _mistral_messages_iot_sensor(payload: dict[str, Any]) -> tuple[str, str]:
    body = {k: v for k, v in payload.items() if k != "kind"}
    system = (
        "Eres ingeniero agrícola / IoT en contexto UE. "
        "Responde con un único JSON válido (sin markdown): "
        'summary (string), alerts (array de strings), recommended_actions (array de strings). '
        "No inventes lecturas no presentes en el JSON."
    )
    user = f"Telemetría y metadatos del sensor (JSON): {json.dumps(body, ensure_ascii=False)}"
    return system, user


def _mistral_messages_plc_generate(payload: dict[str, Any]) -> tuple[str, str]:
    standards = payload.get("standards")
    if not isinstance(standards, list):
        standards = ["IEC 61131-3"]
    system = (
        "Eres ingeniero PLC UE. Salida: un único JSON válido, sin markdown. "
        "Sin garantizar conformidad normativa sin revisión humana."
    )
    user = (
        f"Requisitos: {payload.get('requirements', '')}\n"
        f"Hardware objetivo: {payload.get('hardware', 'no especificado')}\n"
        f"Estándares: {json.dumps(standards, ensure_ascii=False)}\n"
        'Devuelve JSON con "plc_code" (string ST), '
        '"validation": {"status": "OK"|"REVIEW", "messages": [string, ...]}.'
    )
    return system, user


def _mistral_messages_for_payload(payload: dict[str, Any]) -> tuple[str, str]:
    kind = payload.get("kind")
    if kind in ("qelectrotech_svg", "qelectrotech") or (
        isinstance(payload.get("svg_base64"), str) and payload.get("svg_base64", "").strip()
    ):
        return _mistral_messages_qelectrotech_svg(payload)
    if kind in ("plc_generate", "cursor_plc"):
        return _mistral_messages_plc_generate(payload)
    if kind in ("iot_sensor", "iot_ingest"):
        return _mistral_messages_iot_sensor(payload)
    return _mistral_messages_agri(payload)


async def _node_mistral(state: CastuoGraphState) -> CastuoGraphState:
    errs = list(state.get("errors") or [])
    key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not key:
        return {
            "analysis": "",
            "errors": errs + ["MISTRAL_API_KEY vacío: nodo Mistral omitido"],
        }
    model = os.getenv("MISTRAL_LANGGRAPH_MODEL", "mistral-small-latest").strip()
    payload = state["payload"]
    system, user = _mistral_messages_for_payload(payload)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            text = r.text
            if r.status_code >= 400:
                return {"analysis": "", "errors": errs + [f"Mistral HTTP {r.status_code}: {text[:500]}"]}
            data = json.loads(text)
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            return {"analysis": str(content), "errors": errs}
    except Exception as e:  # noqa: BLE001
        return {"analysis": "", "errors": errs + [f"Mistral error: {e!s}"]}


async def _node_seal(state: CastuoGraphState) -> CastuoGraphState:
    blob = json.dumps(
        {"payload": state.get("payload"), "analysis": state.get("analysis", "")},
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    h = hashlib.sha256(blob).hexdigest()
    return {"trace_hash": h}


async def _node_gaia_hook(state: CastuoGraphState) -> CastuoGraphState:
    url = os.getenv("GAIACHAIN_REGISTER_URL", "").strip()
    token = os.getenv("N8N_GAIACHAIN_API_KEY", os.getenv("GAIACHAIN_API_KEY", "")).strip()
    if not url:
        return {"gaia_http_status": None, "gaia_body": "skipped_no_GAIACHAIN_REGISTER_URL"}
    body = {
        "trace_hash": state.get("trace_hash"),
        "payload": state.get("payload"),
        "analysis_preview": (state.get("analysis") or "")[:2000],
    }
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, headers=headers, json=body)
            return {"gaia_http_status": r.status_code, "gaia_body": r.text[:4000]}
    except Exception as e:  # noqa: BLE001
        return {"gaia_http_status": None, "gaia_body": f"error:{e!s}"}


async def _node_slack_hook(state: CastuoGraphState) -> CastuoGraphState:
    wh = os.getenv("SLACK_WEBHOOK", "").strip()
    if not wh:
        return {"slack_http_status": None}
    msg = {
        "text": (
            f"LangGraph CASTÚO · hash={state.get('trace_hash', '')[:16]}… "
            f"errores={len(state.get('errors') or [])}"
        )
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(wh, json=msg)
            return {"slack_http_status": r.status_code}
    except Exception:
        return {"slack_http_status": None}


def _build_graph():
    g = StateGraph(CastuoGraphState)
    g.add_node("ingest", _node_ingest)
    g.add_node("mistral", _node_mistral)
    g.add_node("seal", _node_seal)
    g.add_node("gaia_hook", _node_gaia_hook)
    g.add_node("slack_hook", _node_slack_hook)
    g.add_edge(START, "ingest")
    g.add_edge("ingest", "mistral")
    g.add_edge("mistral", "seal")
    g.add_edge("seal", "gaia_hook")
    g.add_edge("gaia_hook", "slack_hook")
    g.add_edge("slack_hook", END)
    return g.compile()


_compiled = None


def get_compiled_graph():
    global _compiled
    if _compiled is None:
        _compiled = _build_graph()
    return _compiled


async def run_castuo_langgraph(payload: dict[str, Any]) -> dict[str, Any]:
    graph = get_compiled_graph()
    out: CastuoGraphState = await graph.ainvoke({"payload": payload})
    return {
        "analysis": out.get("analysis", ""),
        "trace_hash": out.get("trace_hash", ""),
        "errors": out.get("errors") or [],
        "gaia_http_status": out.get("gaia_http_status"),
        "gaia_body": out.get("gaia_body"),
        "slack_http_status": out.get("slack_http_status"),
    }
