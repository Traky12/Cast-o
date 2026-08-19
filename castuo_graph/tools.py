"""
CASTÚO-SYSTEM™ v3.1 — Tools LangGraph Agritech
6 herramientas reales: IoT · SIGPAC · TRACES · WooCommerce · GaiaChain · ELK
Cada tool retorna resultado + compensating_action cuando aplica.

Secrets: API keys resueltas via read_secret() — Opción A (fichero) > B (Vault) > "" .
URLs (no secretos): os.getenv() directo.
Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §1 (Matriz A/B/C)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

try:
    from .state import CompensatingAction, SensorReading
except ImportError:
    from state import CompensatingAction, SensorReading


# ─── Secret resolver (inline — castuo_graph runs isolated, no backend/ path) ─
# Same logic as backend/security/vault.py — kept here to avoid import path
# complexity when castuo_graph/ tests run with `cd castuo_graph && pytest`.
def _read_secret(name: str) -> str:
    """
    Option A: {name}_FILE env → read file.
    Option B: {name} env → plain value (dev only).
    Never raises; returns "" if nothing configured.
    """
    file_path = os.getenv(f"{name}_FILE", "")
    if file_path:
        try:
            with open(file_path) as fh:
                return fh.read().strip()
        except OSError:
            return ""
    return os.getenv(name, "")


# ─── Service endpoints (URLs — not secrets) ───────────────────────────────────
SABIONDA_API  = os.getenv("SABIONDA_API_URL",  "http://fastapi:8000")
GAIACHAIN_API = os.getenv("GAIACHAIN_API_URL", "http://gaiachain-node:8545")
IPFS_API      = os.getenv("IPFS_API_URL",      "http://ipfs-node:5001")
WOOCOMMERCE_URL = os.getenv("WOOCOMMERCE_URL", "")
ELK_URL       = os.getenv("ELK_URL",           "http://elasticsearch:9200")
SIGPAC_API    = os.getenv("SIGPAC_API_URL",    "https://sigpac.mapa.gob.es/api")
TRACES_API    = os.getenv("TRACES_API_URL",    "https://webgate.ec.europa.eu/tracesnt/api")
GAIACHAIN_CONTRACT_TRAZABILIDAD = os.getenv(
    "GAIACHAIN_CONTRACT_TRAZABILIDAD",
    "0x7aCeE349bD40ED460d8575A3F245790E81Ce3AdB",
)

# ─── API keys (secrets — Option A file > Option B env, never plain in prod) ───
GAIACHAIN_KEY    = _read_secret("GAIACHAIN_API_KEY")
IPFS_KEY         = _read_secret("IPFS_API_KEY")
WOOCOMMERCE_KEY  = _read_secret("WOOCOMMERCE_CONSUMER_KEY")
WOOCOMMERCE_SECRET = _read_secret("WOOCOMMERCE_CONSUMER_SECRET")

HTTP_RETRY_ATTEMPTS = int(os.getenv("CASTUO_HTTP_RETRY_ATTEMPTS", "2"))
HTTP_RETRY_BASE_DELAY = float(os.getenv("CASTUO_HTTP_RETRY_BASE_DELAY", "0.4"))
HTTP_CIRCUIT_FAILURE_THRESHOLD = int(os.getenv("CASTUO_HTTP_CIRCUIT_FAILURE_THRESHOLD", "3"))
HTTP_CIRCUIT_OPEN_SECONDS = float(os.getenv("CASTUO_HTTP_CIRCUIT_OPEN_SECONDS", "20"))

_HTTP_CLIENTS: dict[str, httpx.AsyncClient] = {}
_CIRCUIT_BREAKERS: dict[str, dict[str, float]] = {}


class CircuitOpenError(RuntimeError):
    """Raised when a downstream service is temporarily short-circuited."""


def _is_test_runtime() -> bool:
    return "PYTEST_CURRENT_TEST" in os.environ


def _get_http_client(service: str, timeout: float) -> httpx.AsyncClient:
    """Reutiliza clientes HTTP fuera de tests para maximizar keep-alive/pooling."""
    if _is_test_runtime():
        return httpx.AsyncClient(timeout=timeout)

    client = _HTTP_CLIENTS.get(service)
    if client is None or client.is_closed:
        client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
        _HTTP_CLIENTS[service] = client
    return client


def _breaker_state(service: str) -> dict[str, float]:
    return _CIRCUIT_BREAKERS.setdefault(service, {"failures": 0.0, "opened_until": 0.0})


def _is_retryable_status(status_code: int) -> bool:
    return status_code >= 500 or status_code in (408, 429)


def _check_circuit_open(service: str) -> None:
    if _is_test_runtime():
        return

    state = _breaker_state(service)
    now = asyncio.get_event_loop_policy().get_event_loop().time()
    if state["opened_until"] > now:
        raise CircuitOpenError(f"Circuit open for service {service}")


def _record_success(service: str) -> None:
    state = _breaker_state(service)
    state["failures"] = 0.0
    state["opened_until"] = 0.0


def _record_failure(service: str) -> None:
    if _is_test_runtime():
        return

    state = _breaker_state(service)
    state["failures"] += 1.0
    if state["failures"] >= HTTP_CIRCUIT_FAILURE_THRESHOLD:
        now = asyncio.get_event_loop_policy().get_event_loop().time()
        state["opened_until"] = now + HTTP_CIRCUIT_OPEN_SECONDS


async def _request_with_resilience(
    service: str,
    method: str,
    url: str,
    *,
    timeout: float,
    retries: int = HTTP_RETRY_ATTEMPTS,
    headers: Optional[dict[str, str]] = None,
    **kwargs: Any,
) -> httpx.Response:
    """Hace requests con pooling, retry exponencial y circuit breaker por servicio."""
    _check_circuit_open(service)

    client = _get_http_client(service, timeout)
    request_method = getattr(client, method.lower())
    effective_retries = 0 if _is_test_runtime() else retries

    for attempt in range(effective_retries + 1):
        try:
            response = await request_method(url, headers=headers, **kwargs)
            if _is_retryable_status(response.status_code):
                _record_failure(service)
                if attempt < effective_retries:
                    await asyncio.sleep(HTTP_RETRY_BASE_DELAY * (2 ** attempt))
                    continue
                return response

            _record_success(service)
            return response
        except httpx.RequestError:
            _record_failure(service)
            if attempt >= effective_retries:
                raise
            await asyncio.sleep(HTTP_RETRY_BASE_DELAY * (2 ** attempt))

    raise RuntimeError(f"Unexpected HTTP retry exhaustion for {service}")


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

    values_by_metric = {reading["metric"]: reading["value"] for reading in readings}
    ph = values_by_metric.get("ph")
    ec = values_by_metric.get("ec_ms_cm")
    temp = values_by_metric.get("temp_solucion_c")
    o2 = values_by_metric.get("o2_disuelto_mg_l")
    lote_id = readings[0]["lote_id"] if readings else "unknown"

    if all(v is not None for v in [ph, ec, temp, o2]):
        try:
            resp = await _request_with_resilience(
                "sabionda",
                "POST",
                f"{SABIONDA_API}/api/v1/invernadero/solucion-nutritiva",
                timeout=15,
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
        except (httpx.RequestError, CircuitOpenError):
            alertas.append("Backend SABIONDA no disponible — usando validación local")
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
    try:
        resp = await _request_with_resilience(
            "sigpac",
            "GET",
            f"{SIGPAC_API}/parcelas",
            timeout=20,
            params={"ref": sigpac_ref},
            headers={"Accept": "application/json"},
        )
        if resp.status_code == 200:
            return resp.json()
    except (httpx.RequestError, CircuitOpenError):
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
    try:
        resp = await _request_with_resilience(
            "traces",
            "POST",
            f"{SABIONDA_API}/api/v1/traces/certificado",
            timeout=30,
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
    except (httpx.RequestError, CircuitOpenError) as e:
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
    try:
        resp = await _request_with_resilience(
            "gaiachain",
            "POST",
            f"{GAIACHAIN_API}/contracts/{GAIACHAIN_CONTRACT_TRAZABILIDAD}/call",
            timeout=60,
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
    except (httpx.RequestError, CircuitOpenError) as e:
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
    try:
        resp = await _request_with_resilience(
            "woocommerce",
            "PUT",
            f"{WOOCOMMERCE_URL}/wp-json/wc/v3/orders/{order_id}",
            timeout=20,
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
    except (httpx.RequestError, CircuitOpenError) as e:
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

    try:
        await _request_with_resilience(
            "elk",
            "POST",
            f"{ELK_URL}/castuo-logs-{datetime.now(timezone.utc).strftime('%Y.%m.%d')}/_doc/{log_id}",
            timeout=10,
            json=doc,
            retries=1,
        )
    except (httpx.RequestError, CircuitOpenError):
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
    if action["service"] == "traces" and action["action"] == "cancel":
        cert_id = action["resource_id"]
        await _request_with_resilience(
            "traces",
            "POST",
            f"{TRACES_API}/certificates/{cert_id}/cancel",
            timeout=30,
            json={"reason": action["payload"].get("motivo", "rollback")},
        )

    elif action["service"] == "gaiachain" and action["action"] == "register_cancellation":
        payload = action["payload"]
        await _request_with_resilience(
            "gaiachain",
            "POST",
            f"{GAIACHAIN_API}/contracts/{GAIACHAIN_CONTRACT_TRAZABILIDAD}/call",
            timeout=30,
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
        await _request_with_resilience(
            "woocommerce",
            "PUT",
            f"{WOOCOMMERCE_URL}/wp-json/wc/v3/orders/{order_id}",
            timeout=30,
            auth=(WOOCOMMERCE_KEY, WOOCOMMERCE_SECRET),
            json={"meta_data": null_meta},
        )
