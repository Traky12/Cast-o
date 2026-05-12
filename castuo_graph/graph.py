"""
CASTÚO-SYSTEM™ v3.1 — Grafo LangGraph Maestro
Invernadero → Campo → Procesado → Cliente → Reporte

Flujo normal:
  START → invernadero → ethical_guard → campo → procesado → cliente → reporte → END

Flujos condicionales:
  - ethical_guard detecta GDPR/AI Act violation → human_review → END
  - invernadero status CRITICO              → human_review (vía ethical_guard)
  - cualquier nodo falla                   → error_handler → compensación → END

Rollback garantizado:
  Cada nodo downstream registra CompensatingAction en rollback_stack.
  error_handler ejecuta compensaciones en orden LIFO.
"""

from __future__ import annotations

import traceback
from datetime import datetime, timezone
from typing import Literal

from langgraph.graph import END, START, StateGraph

from ethical_guard import ethical_guard_node
from nodes.campo_node import campo_node
from nodes.cliente_node import cliente_node
from nodes.invernadero_node import invernadero_node
from nodes.procesado_node import procesado_node
from nodes.reporte_node import reporte_node
from state import AgroState
from tools import execute_compensations, tool_log_elk


# ─────────────────────────────────────────────────────────────────────────────
# Nodo de error con compensación LIFO
# ─────────────────────────────────────────────────────────────────────────────

async def error_handler_node(state: AgroState) -> AgroState:
    """
    Ejecuta compensaciones LIFO cuando un nodo falla.
    Garantiza que no quedan recursos en estado inconsistente.
    """
    lote_id = state.get("lote_id", "unknown")
    rollback_stack = state.get("rollback_stack", [])

    await tool_log_elk(
        lote_id=lote_id,
        event_type="ROLLBACK_STARTED",
        node="error_handler",
        data={
            "failed_node": state.get("error_node"),
            "error": state.get("error"),
            "compensations_pending": len(rollback_stack),
        },
    )

    compensated = []
    if rollback_stack:
        compensated = await execute_compensations(rollback_stack, lote_id)

    await tool_log_elk(
        lote_id=lote_id,
        event_type="ROLLBACK_COMPLETED",
        node="error_handler",
        data={"compensated_resources": compensated},
    )

    return {
        **state,
        "compensations_executed": compensated,
        "status": "failed",
        "current_node": "error_handler",
    }


async def human_review_node(state: AgroState) -> AgroState:
    """
    Parada obligatoria para revisión humana (AI Act art. 14).
    En producción: envía notificación al operador y espera confirmación.
    El grafo se detiene aquí hasta que el humano reanude.
    """
    lote_id = state.get("lote_id", "unknown")
    reason = state.get("next_action", "Revisión humana requerida")

    await tool_log_elk(
        lote_id=lote_id,
        event_type="HUMAN_REVIEW_REQUIRED",
        node="human_review",
        data={
            "reason": reason,
            "invernadero_status": state.get("invernadero_status"),
            "gdpr_violations": state.get("gdpr_violations", []),
        },
    )

    return {
        **state,
        "status": "human_review",
        "current_node": "human_review",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Wrappers con captura de errores → error_handler
# ─────────────────────────────────────────────────────────────────────────────

def _wrap_node(node_fn, node_name: str):
    """Envuelve un nodo para capturar excepciones y enrutar al error_handler."""
    async def wrapped(state: AgroState) -> AgroState:
        try:
            return await node_fn(state)
        except Exception as exc:
            await tool_log_elk(
                lote_id=state.get("lote_id", "unknown"),
                event_type="NODE_ERROR",
                node=node_name,
                data={"error": str(exc), "traceback": traceback.format_exc()[-500:]},
            )
            return {
                **state,
                "error": str(exc),
                "error_node": node_name,
                "status": "failed",
                "current_node": node_name,
            }
    wrapped.__name__ = node_name
    return wrapped


# ─────────────────────────────────────────────────────────────────────────────
# Aristas condicionales
# ─────────────────────────────────────────────────────────────────────────────

def route_after_invernadero(state: AgroState) -> Literal["ethical_guard", "error_handler"]:
    if state.get("status") == "failed":
        return "error_handler"
    return "ethical_guard"


def route_after_ethical_guard(
    state: AgroState,
) -> Literal["campo", "human_review", "error_handler"]:
    if state.get("status") == "failed":
        return "error_handler"
    if state.get("ai_act_human_review_required"):
        return "human_review"
    return "campo"


def route_after_campo(state: AgroState) -> Literal["procesado", "error_handler"]:
    if state.get("status") == "failed":
        return "error_handler"
    return "procesado"


def route_after_procesado(state: AgroState) -> Literal["cliente", "error_handler"]:
    if state.get("status") == "failed":
        return "error_handler"
    return "cliente"


def route_after_cliente(state: AgroState) -> Literal["reporte", "error_handler"]:
    if state.get("status") == "failed":
        return "error_handler"
    return "reporte"


# ─────────────────────────────────────────────────────────────────────────────
# Construcción del grafo
# ─────────────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgroState)

    # Nodos con captura de errores
    graph.add_node("invernadero",    _wrap_node(invernadero_node,   "invernadero"))
    graph.add_node("ethical_guard",  ethical_guard_node)   # Síncrono — sin I/O
    graph.add_node("campo",          _wrap_node(campo_node,         "campo"))
    graph.add_node("procesado",      _wrap_node(procesado_node,     "procesado"))
    graph.add_node("cliente",        _wrap_node(cliente_node,       "cliente"))
    graph.add_node("reporte",        _wrap_node(reporte_node,       "reporte"))
    graph.add_node("error_handler",  _wrap_node(error_handler_node, "error_handler"))
    graph.add_node("human_review",   _wrap_node(human_review_node,  "human_review"))

    # Aristas
    graph.add_edge(START, "invernadero")
    graph.add_conditional_edges("invernadero",   route_after_invernadero)
    graph.add_conditional_edges("ethical_guard", route_after_ethical_guard)
    graph.add_conditional_edges("campo",         route_after_campo)
    graph.add_conditional_edges("procesado",     route_after_procesado)
    graph.add_conditional_edges("cliente",       route_after_cliente)
    graph.add_edge("reporte",       END)
    graph.add_edge("error_handler", END)
    graph.add_edge("human_review",  END)

    return graph.compile()


# Instancia global
agro_graph = build_graph()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI health endpoint para docker-compose healthcheck
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI

app = FastAPI(title="CASTÚO LangGraph", version="3.1.0")


@app.get("/langgraph/health")
async def health():
    return {
        "status": "ok",
        "service": "castuo-langgraph",
        "version": "3.1.0",
        "nodes": ["invernadero", "ethical_guard", "campo", "procesado", "cliente", "reporte"],
        "sovereignty": "EU",
    }


@app.post("/langgraph/run")
async def run_graph(initial_state: dict):
    """
    Ejecuta el grafo completo con el estado inicial proporcionado.
    Usado por n8n, sensores IoT y la CLI de SABIONDA.
    """
    defaults: AgroState = {
        "lote_id": initial_state.get("lote_id", ""),
        "operador_nif": initial_state.get("operador_nif", ""),
        "sensor_readings": initial_state.get("sensor_readings", []),
        "woocommerce_order_id": initial_state.get("woocommerce_order_id"),
        "validated_readings": [],
        "readings_alertas": [],
        "invernadero_status": None,
        "gdpr_consent_verified": False,
        "pii_redacted": False,
        "ai_act_human_review_required": False,
        "gdpr_violations": [],
        "sigpac_parcelas": None,
        "traces_cert_id": None,
        "traces_cert_payload": None,
        "gaiachain_tx_hash": None,
        "ipfs_cid": None,
        "content_hash": None,
        "qr_url": None,
        "qr_hash_cadena": None,
        "order_updated": False,
        "elk_log_id": None,
        "pdf_report_url": None,
        "rollback_stack": [],
        "compensations_executed": [],
        "current_node": "start",
        "error": None,
        "error_node": None,
        "status": "running",
        "next_action": None,
        # Campos adicionales del contexto de negocio
        "sigpac_ref": initial_state.get("sigpac_ref", ""),
        "cultivo": initial_state.get("cultivo", "tomate"),
        "variedad": initial_state.get("variedad", ""),
        "fecha_cosecha": initial_state.get("fecha_cosecha", ""),
        "kg_cosechados": initial_state.get("kg_cosechados", 0.0),
        "eco_certificado": initial_state.get("eco_certificado", False),
        "sin_pesticidas_sinteticos": initial_state.get("sin_pesticidas_sinteticos", False),
        "explotacion_rea": initial_state.get("explotacion_rea", ""),
        "destino": initial_state.get("destino", "mercado_local"),
        "destino_pais": initial_state.get("destino_pais", "ES"),
    }
    final_state = await agro_graph.ainvoke(defaults)
    return {
        "status": final_state.get("status"),
        "lote_id": final_state.get("lote_id"),
        "qr_url": final_state.get("qr_url"),
        "blockchain_tx": final_state.get("gaiachain_tx_hash"),
        "human_review_required": final_state.get("ai_act_human_review_required"),
        "error": final_state.get("error"),
        "compensations_executed": final_state.get("compensations_executed", []),
    }
