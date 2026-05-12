"""
Nodo 2: CAMPO — SIGPAC + TRACES
Consulta parcelas oficiales y emite certificado TRACES si procede.
TRACES es la primera escritura externa → genera compensating action.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from state import AgroState
from tools import tool_query_sigpac, tool_emit_traces_cert, tool_log_elk


async def campo_node(state: AgroState) -> AgroState:
    lote_id = state.get("lote_id", "unknown")
    operador_nif_hash = state.get("operador_nif", "")  # ya es hash post ethical_guard
    rollback_stack = list(state.get("rollback_stack", []))

    # 1. SIGPAC — read-only, sin compensación
    sigpac_data = await tool_query_sigpac(
        titular_nif=operador_nif_hash,
        sigpac_ref=state.get("sigpac_ref", ""),
    )

    # 2. TRACES — escritura → compensating action en rollback_stack
    traces_data, traces_compensation = await tool_emit_traces_cert(
        explotacion_rega=lote_id.split("-")[1] if "-" in lote_id else lote_id,
        lote_id=lote_id,
        cultivo="tomate",
        kg=state.get("kg_cosechados", 0.0),
        destino_pais=state.get("destino_pais", "ES"),
    )
    rollback_stack.append(traces_compensation)

    cert_id = traces_data.get("payload", {}).get("certificado", {}).get("numero")

    await tool_log_elk(
        lote_id=lote_id,
        event_type="CAMPO_PROCESSED",
        node="campo",
        data={"sigpac_ok": bool(sigpac_data), "traces_cert_id": cert_id},
    )

    return {
        **state,
        "sigpac_parcelas": sigpac_data,
        "traces_cert_id": cert_id,
        "traces_cert_payload": traces_data,
        "rollback_stack": rollback_stack,
        "current_node": "campo",
    }
