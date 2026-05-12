"""
Nodo 4: CLIENTE — QR + WooCommerce
Genera QR verificable y actualiza la orden WooCommerce del cliente.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
from state import AgroState
from tools import tool_update_woocommerce_order, tool_log_elk, SABIONDA_API


async def cliente_node(state: AgroState) -> AgroState:
    lote_id = state.get("lote_id", "unknown")
    rollback_stack = list(state.get("rollback_stack", []))

    # 1. Generar QR de trazabilidad via SABIONDA API
    qr_result = await _generate_qr(state)
    qr_url = qr_result.get("verify_url", f"https://verify.castuo360.eu/lote/{lote_id}")
    qr_hash = qr_result.get("hash_cadena", state.get("content_hash", ""))

    # 2. Actualizar WooCommerce si hay orden — compensating action
    order_updated = False
    order_id = state.get("woocommerce_order_id")
    if order_id:
        woo_data, woo_compensation = await tool_update_woocommerce_order(
            order_id=order_id,
            lote_id=lote_id,
            qr_url=qr_url,
            qr_hash=qr_hash,
        )
        rollback_stack.append(woo_compensation)
        order_updated = not bool(woo_data.get("error"))

    await tool_log_elk(
        lote_id=lote_id,
        event_type="CLIENT_QR_DELIVERED",
        node="cliente",
        data={
            "qr_url": qr_url,
            "order_id": order_id,
            "order_updated": order_updated,
        },
    )

    return {
        **state,
        "qr_url": qr_url,
        "qr_hash_cadena": qr_hash,
        "order_updated": order_updated,
        "rollback_stack": rollback_stack,
        "current_node": "cliente",
    }


async def _generate_qr(state: AgroState) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{SABIONDA_API}/api/v1/trazabilidad/qr/generar",
                json={
                    "lote_id": state.get("lote_id"),
                    "hash_cierre": state.get("content_hash", "a" * 64),
                    "cultivo": state.get("cultivo", "tomate"),
                    "variedad": state.get("variedad", "desconocida"),
                    "fecha_cosecha": state.get("fecha_cosecha", ""),
                    "kg_cosechados": state.get("kg_cosechados", 0.0),
                    "eco_certificado": state.get("eco_certificado", False),
                    "sin_pesticidas_sinteticos": state.get("sin_pesticidas_sinteticos", False),
                    "explotacion_rea": state.get("explotacion_rea", ""),
                    "operador_nif": state.get("operador_nif", ""),
                    "destino": state.get("destino", "mercado_local"),
                    "eventos": [],
                },
            )
            if resp.status_code == 200:
                return resp.json()
    except httpx.RequestError:
        pass
    lote_id = state.get("lote_id", "unknown")
    content_hash = state.get("content_hash", "0" * 64)
    return {
        "verify_url": f"https://verify.castuo360.eu/lote/{lote_id}/{content_hash}",
        "hash_cadena": content_hash,
    }
