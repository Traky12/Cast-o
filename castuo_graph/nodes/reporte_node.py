"""
Nodo 5: REPORTES — ELK audit trail + resumen final
Cierre del grafo: registra el evento final y produce el resumen del ciclo.
Read-only: no hay compensating action (el audit trail nunca se borra).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timezone
from state import AgroState
from tools import tool_log_elk


async def reporte_node(state: AgroState) -> AgroState:
    lote_id = state.get("lote_id", "unknown")

    summary = {
        "lote_id": lote_id,
        "invernadero_status": state.get("invernadero_status"),
        "alertas_count": len(state.get("readings_alertas", [])),
        "traces_cert_id": state.get("traces_cert_id"),
        "blockchain_tx": state.get("gaiachain_tx_hash"),
        "ipfs_cid": state.get("ipfs_cid"),
        "qr_url": state.get("qr_url"),
        "order_updated": state.get("order_updated"),
        "gdpr_violations": len(state.get("gdpr_violations", [])),
        "human_review_required": state.get("ai_act_human_review_required"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    log_result = await tool_log_elk(
        lote_id=lote_id,
        event_type="FLOW_COMPLETED",
        node="reporte",
        data=summary,
    )

    return {
        **state,
        "elk_log_id": log_result.get("log_id"),
        "status": "completed",
        "current_node": "reporte",
    }
