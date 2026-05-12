"""
API Gateway (plantilla): valida JWT Keycloak y reenvía a backend CASTÚO.
MQTT no es HTTP: conexión directa al broker desde dispositivos.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, Response

from auth_jwt import GatewayUser, require_any_role

app = FastAPI(title="CASTÚO API Gateway", version="0.1.0")

BACKEND = os.getenv("CASTUO_BACKEND_URL", "http://backend:8000").rstrip("/")
LORA_UP = os.getenv("LORA_UPSTREAM", "").rstrip("/")

HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _filter_request_headers(raw: Dict[str, str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in raw.items():
        lk = k.lower()
        if lk in HOP_BY_HOP:
            continue
        out[k] = v
    return out


async def _proxy_httpx(
    method: str,
    url: str,
    headers: Dict[str, str],
    content: bytes,
    params: List[Tuple[str, str]],
) -> Response:
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=content if content else None,
                params=params,
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e

    rh = {k: v for k, v in r.headers.items() if k.lower() not in HOP_BY_HOP}
    return Response(content=r.content, status_code=r.status_code, headers=rh)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "backend": BACKEND,
        "lora_upstream_configured": bool(LORA_UP),
        "note": "MQTT: conexión directa al broker; no se proxifica como HTTP.",
    }


@app.get("/api/iot/broker-info")
async def broker_info(user: GatewayUser = Depends(require_any_role("technician", "admin", "viewer", "owner", "dpo"))):
    host = os.getenv("MQTT_PUBLIC_HOST", "localhost")
    return {
        "mqtt_host": host,
        "mqtt_ports": {
            "plain": int(os.getenv("MQTT_PLAIN_PORT", "1883")),
            "tls": int(os.getenv("MQTT_TLS_PORT", "8883")),
        },
        "tls_required_production": True,
    }


@app.api_route(
    "/api/lora/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_lora(
    path: str,
    request: Request,
    user: GatewayUser = Depends(require_any_role("technician", "admin")),
):
    del user  # dependencia solo para RBAC
    if not LORA_UP:
        raise HTTPException(
            status_code=503,
            detail="LORA_UPSTREAM no definido. Levantar uvicorn en scripts/ai/mistral_lora/app.py o definir LORA_UPSTREAM.",
        )
    target = f"{LORA_UP}/{path}" if path else LORA_UP
    body = await request.body()
    headers = _filter_request_headers(dict(request.headers))
    return await _proxy_httpx(
        request.method,
        target,
        headers,
        body,
        list(request.query_params.multi_items()),
    )


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def proxy_api(
    path: str,
    request: Request,
    user: GatewayUser = Depends(require_any_role("technician", "admin", "viewer", "owner", "dpo")),
):
    del user
    target = f"{BACKEND}/api/{path}"
    body = await request.body()
    headers = _filter_request_headers(dict(request.headers))
    return await _proxy_httpx(
        request.method,
        target,
        headers,
        body,
        list(request.query_params.multi_items()),
    )
