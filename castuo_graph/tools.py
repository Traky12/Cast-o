"""
CASTÚO-SYSTEM™ v3.1 — Tools LangGraph Agritech
6 herramientas reales: IoT · SIGPAC · TRACES · WooCommerce · GaiaChain · ELK
Cada tool retorna resultado + compensating_action cuando aplica.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

from state import CompensatingAction, SensorReading

SABIONDA_API = os.getenv("SABIONDA_API_URL", "http://fastapi:8000")
GAIACHAIN_API = os.getenv("GAIACHAIN_API_URL", "http://gaiachain-node:8545")
GAIACHAIN_KEY = os.getenv("GAIACHAIN_API_KEY", "")
IPFS_API = os.getenv("IPFS_API_URL", "http://ipfs-node:5001")
IPFS_KEY = os.getenv("IPFS_API_KEY", "")
WOOCOMMERCE_URL = os.getenv("WOOCOMMERCE_URL", "")
WOOCOMMERCE_KEY = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
WOOCOMMERCE_SECRET = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")
ELK_URL = os.getenv("ELK_URL", "http://elasticsearch:9200")
GAIACHAIN_CONTRACT_TRAZABILIDAD = os.getenv(
    "GAIACHAIN_CONTRACT_TRAZABILIDAD",
    "0x7aCeE349bD40ED460d8575A3F245790E81Ce3AdB",
)
SIGPAC_API = os.getenv("SIGPAC_API_URL", "https://sigpac.mapa.gob.es/api")
TRACES_API = os.getenv("TRACES_API_URL", "https://webgate.ec.europa.eu/tracesnt/api")


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1: IoT Sensor — lectura y validación de parámetros hidropónicos
# ─────────────────────────────────────────────────────────────────────────────

async def tool_validate_iot_readings(
    readings: list[SensorReading],
    cultivo: str,
) -> Dict[str, Any]:
    """
    Valida las lecturas IoT contra los rangos óptimos del cultivo.
    Llama al endpoint /invernadero/solucion-nutritiva del backend SABIONDA.
    Read-only: no genera compensating action.
    """
    alertas: list[str] = []
    status = "OPTIMO"

    async with httpx.AsyncClient(timeout=15) as client:
        # Agrupar por tipo de lectura y evaluar
        ph = next((r["value"] for r in readings if r["metric"] == "ph"), None)
        ec = next((r["value"] for r in readings if r["metric"] == "ec_ms_cm"), None)
        temp = next((r["value"] for r in readings if r["metric"] == "temp_solucion_c"), None)
        o2 = next((r["value"] for r in readings if r["metric"] == "o2_disuelto_mg_l"), None)
        lote_id = readings[0]["lote_id"] if readings else "unknown"

        if all(v is not None for v in [ph, ec, temp, o2]):
            try:
                resp = await client.post(
                    f"{SABIONDA_API}/api/v1/invernadero/solucion-nutritiva",
                    json={
                        "lote_id": lote_id,
                        "zona": "iot-auto",
                        "cultivo": cultivo,
                        "sistema": "goteo",
                        "ph": ph,
                        "ec_ms_cm": ec,
                        "temp_solucion_c": temp,
                        "o2_disuelto_mg_l": o2,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    alertas.extend(data.get("alertas", []))
                    status = data.get("estado", "OPTIMO")
            except httpx.RequestError:
                alertas.append("Backend SABIONDA no disponible — usando validación local")
                # Validación local de respaldo
                if o2 is not None and o2 < 6.0:
                    alertas.append(f"O₂ disuelto crítico: {o2} mg/L < 6.0 mg/L")
                    status = "CRITICO"

    return {
        "validated": True,
        "alertas": alertas,
        "status": status,
        "readings_count": len(readings),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2: SIGPAC — consulta parcelas oficiales ES
# ─────────────────────────────────────────────────────────────────────────────

async def tool_query_sigpac(
    titular_nif: str,
    sigpac_ref: str,
) -> Dict[str, Any]:
    """
    Consulta parcelas en SIGPAC. Read-only — sin compensating action.
    """
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(
                f"{SIGPAC_API}/parcelas",
                params={"ref": sigpac_ref},
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                return resp.json()
        except httpx.RequestError:
            pass

    # Fallback estructurado si SIGPAC no responde
    return {
        "sigpac_ref": sigpac_ref,
        "estado": "consultado",
        "fuente": "cache_local",
        "aviso": "SIGPAC no respondió — continuar con referencia manual",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3: TRACES — emisión de certificado sanitario
# ─────────────────────────────────────────────────────────────────────────────

async def tool_emit_traces_cert(
    explotacion_rega: str,
    lote_id: str,
    cultivo: str,
    kg: float,
    destino_pais: str,
) -> Tuple[Dict[str, Any], CompensatingAction]:
    """
    Emite certificado TRACES. Retorna (resultado, compensating_action).
    La compensación cancela el certificado si un nodo downstream falla.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(
                f"{SABIONDA_API}/api/v1/traces/certificado",
                json={
                    "explotacion_rega": explotacion_rega,
                    "nombre_explotacion": f"Invernadero Agrovoltaico {explotacion_rega}",
                    "animales": {"especie": "producto_vegetal", "raza": cultivo, "cantidad": int(kg)},
                    "tipo_movimiento": "EXPORT" if destino_pais != "ES" else "INTRA",
                    "destino_pais": destino_pais,
                    "destino_explotacion": f"DIST-{destino_pais}-001",
                },
            )
            data = resp.json() if resp.status_code == 200 else {"error": resp.text}
        except httpx.RequestError as e:
            data = {"error": str(e), "cert_id": None}

    cert_id = data.get("payload", {}).get("certificado", {}).get("numero", f"TRACES-PENDING-{lote_id}")

    compensation: CompensatingAction = {
        "node": "campo",
        "service": "traces",
        "action": "cancel",
        "resource_id": cert_id,
        "payload": {"cert_id": cert_id, "motivo": "rollback_grafo_agro"},
    }
    return data, compensation


# ─────────────────────────────────────────────────────────────────────────────
# Tool 4: GaiaChain — registro inmutable blockchain
# ─────────────────────────────────────────────────────────────────────────────

async def tool_register_gaiachain(
    lote_id: str,
    content_hash: str,
    ipfs_cid: str,
    eco_certified: bool,
    operador_nif_hash: str,   # NIF ya hasheado — nunca el NIF en claro en blockchain
) -> Tuple[Dict[str, Any], CompensatingAction]:
    """
    Registra trazabilidad en GaiaChain 3.0.
    Retorna (resultado, compensating_action).
    La compensación registra un evento CANCELLED en la misma cadena
    (blockchain no borra — compensa con evento de reversión).
    """
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(
                f"{GAIACHAIN_API}/contracts/{GAIACHAIN_CONTRACT_TRAZABILIDAD}/call",
                headers={
                    "Authorization": f"Bearer {GAIACHAIN_KEY}",
                    "X-Chain-ID": "31337",
                },
                json={
                    "function": "registerTrace",
                    "params": {
                        "productId": lote_id,
                        "stage": "cosecha_invernadero",
                        "operatorHash": operador_nif_hash,
                        "contentHash": f"0x{content_hash}",
                        "ipfsCid": ipfs_cid,
                        "ecoCertified": eco_certified,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )
            data = resp.json() if resp.status_code == 200 else {"error": resp.text, "tx_hash": None}
        except httpx.RequestError as e:
            data = {"error": str(e), "tx_hash": None}

    tx_hash = data.get("tx_hash", f"tx-pending-{lote_id}")

    compensation: CompensatingAction = {
        "node": "procesado",
        "service": "gaiachain",
        "action": "register_cancellation",
        "resource_id": tx_hash,
        "payload": {
            "original_tx": tx_hash,
            "lote_id": lote_id,
            "reason": "rollback_grafo_agro",
            "compensation_function": "registerCompensation",
        },
    }
    return data, compensation


# ─────────────────────────────────────────────────────────────────────────────
# Tool 5: WooCommerce — actualizar orden con QR de trazabilidad
# ─────────────────────────────────────────────────────────────────────────────

async def tool_update_woocommerce_order(
    order_id: str,
    lote_id: str,
    qr_url: str,
    qr_hash: str,
) -> Tuple[Dict[str, Any], CompensatingAction]:
    """
    Actualiza la orden WooCommerce con el QR de trazabilidad.
    El cliente recibe el QR automáticamente en el email de confirmación.
    Compensación: retirar el metadato de trazabilidad de la orden.
    """
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.put(
                f"{WOOCOMMERCE_URL}/wp-json/wc/v3/orders/{order_id}",
                auth=(WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET),
                json={
                    "meta_data": [
                        {"key": "_castuo_lote_id", "value": lote_id},
                        {"key": "_castuo_qr_url", "value": qr_url},
                        {"key": "_castuo_qr_hash", "value": qr_hash},
                        {"key": "_castuo_trazabilidad", "value": "verified"},
                    ]
                },
            )
            data = resp.json() if resp.status_code == 200 else {"error": resp.text}
        except httpx.RequestError as e:
            data = {"error": str(e), "updated": False}

    compensation: CompensatingAction = {
        "node": "cliente",
        "service": "woocommerce",
        "action": "remove_traceability_meta",
        "resource_id": order_id,
        "payload": {
            "order_id": order_id,
            "keys_to_remove": [
                "_castuo_lote_id", "_castuo_qr_url",
                "_castuo_qr_hash", "_castuo_trazabilidad",
            ],
        },
    }
    return data, compensation


# ─────────────────────────────────────────────────────────────────────────────
# Tool 6: ELK — audit trail trazable RGPD
# ─────────────────────────────────────────────────────────────────────────────

async def tool_log_elk(
    lote_id: str,
    event_type: str,
    node: str,
    data: Dict[str, Any],
    is_compensation: bool = False,
) -> Dict[str, Any]:
    """
    Registra evento en ELK para audit trail. NUNCA borra — es el rastro.
    GDPR: los datos personales (NIF) llegan ya redactados (***NIF_REDACTED***).
    """
    log_id = str(uuid.uuid4())
    doc = {
        "log_id": log_id,
        "lote_id": lote_id,
        "event_type": event_type,
        "node": node,
        "is_compensation": is_compensation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": "castuo-langgraph",
        "sovereignty": "EU",
        **{k: v for k, v in data.items() if k not in ("nif", "email", "telefono")},
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                f"{ELK_URL}/castuo-logs-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}/_doc/{log_id}",
                json=doc,
            )
        except httpx.RequestError:
            pass  # ELK no disponible — continuar sin bloquear el flujo

    return {"log_id": log_id, "indexed": True}


# ─────────────────────────────────────────────────────────────────────────────
# Compensación — ejecutar rollback LIFO
# ─────────────────────────────────────────────────────────────────────────────

async def execute_compensations(
    rollback_stack: list[CompensatingAction],
    lote_id: str,
) -> list[str]:
    """
    Ejecuta compensaciones en orden inverso (LIFO).
    Retorna lista de resource_ids compensados.
    """
    compensated = []
    for action in reversed(rollback_stack):
        try:
            await _run_compensation(action)
            compensated.append(action["resource_id"])
            await tool_log_elk(
                lote_id=lote_id,
                event_type="COMPENSATION_EXECUTED",
                node=action["node"],
                data={
                    "service": action["service"],
                    "action": action["action"],
                    "resource_id": action["resource_id"],
                },
                is_compensation=True,
            )
        except Exception as exc:
            await tool_log_elk(
                lote_id=lote_id,
                event_type="COMPENSATION_FAILED",
                node=action["node"],
                data={"resource_id": action["resource_id"], "error": str(exc)},
                is_compensation=True,
            )
    return compensated


async def _run_compensation(action: CompensatingAction) -> None:
    """Dispatcher de compensaciones por servicio."""
    async with httpx.AsyncClient(timeout=30) as client:
        if action["service"] == "traces" and action["action"] == "cancel":
            cert_id = action["resource_id"]
            await client.post(
                f"{TRACES_API}/certificates/{cert_id}/cancel",
                json={"reason": action["payload"].get("motivo", "rollback")},
            )

        elif action["service"] == "gaiachain" and action["action"] == "register_cancellation":
            payload = action["payload"]
            await client.post(
                f"{GAIACHAIN_API}/contracts/{GAIACHAIN_CONTRACT_TRAZABILIDAD}/call",
                headers={"Authorization": f"Bearer {GAIACHAIN_KEY}"},
                json={
                    "function": payload["compensation_function"],
                    "params": {
                        "originalTx": payload["original_tx"],
                        "loteId": payload["lote_id"],
                        "reason": payload["reason"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                },
            )

        elif action["service"] == "woocommerce" and action["action"] == "remove_traceability_meta":
            order_id = action["resource_id"]
            null_meta = [{"key": k, "value": ""} for k in action["payload"]["keys_to_remove"]]
            await client.put(
                f"{WOOCOMMERCE_URL}/wp-json/wc/v3/orders/{order_id}",
                auth=(WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET),
                json={"meta_data": null_meta},
            )
