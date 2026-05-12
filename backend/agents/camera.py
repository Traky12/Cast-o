"""
MotionEye ↔ CASTÚO: métricas por SSE (solo JSON); vídeo/snapshot vía proxy HTTP.
Mezclar chunks MJPEG binarios dentro de text/event-stream corrompe el canal y el navegador.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse

router = APIRouter(prefix="/agents/camera", tags=["camera"])

_DEFAULT_BASE = "http://127.0.0.1:8765"
_SSE_INTERVAL = float(os.getenv("CASTUO_CAMERA_SSE_INTERVAL", "3"))


def _base_url() -> str:
    return os.getenv("CASTUO_MOTIONEYE_BASE", _DEFAULT_BASE).rstrip("/")


def _auth() -> tuple[str, str] | None:
    u = os.getenv("CASTUO_MOTIONEYE_USER", "").strip()
    p = os.getenv("CASTUO_MOTIONEYE_PASSWORD", "").strip()
    if u and p:
        return (u, p)
    return None


async def _probe_motioneye(client: httpx.AsyncClient) -> tuple[bool, int | None, str]:
    t0 = time.perf_counter()
    try:
        r = await client.get(f"{_base_url()}/", timeout=3.0)
        ms = int((time.perf_counter() - t0) * 1000)
        ok = r.status_code < 500
        return ok, ms, "reachable" if ok else f"http_{r.status_code}"
    except httpx.RequestError as e:
        ms = int((time.perf_counter() - t0) * 1000)
        return False, ms, type(e).__name__


async def _snapshot_bytes(camera_id: int) -> tuple[bytes, str]:
    url = f"{_base_url()}/picture/{camera_id}/current/"
    async with httpx.AsyncClient(auth=_auth(), timeout=10.0, follow_redirects=True) as client:
        r = await client.get(url)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"motioneye snapshot {r.status_code}")
        ct = r.headers.get("content-type", "image/jpeg")
        return r.content, ct


def _sse_camera_frame(payload: dict) -> bytes:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return f"event: camera_update\ndata: {body}\n\n".encode("utf-8")


async def camera_metrics_stream() -> AsyncIterator[bytes]:
    while True:
        async with httpx.AsyncClient(auth=_auth(), timeout=5.0) as client:
            online, latency_ms, reason = await _probe_motioneye(client)
        metric = {
            "camera": "motioneye",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "online": online,
            "latency_ms": latency_ms,
            "reason": reason,
            "motioneye_base": _base_url(),
            "health": "streaming" if online else "offline",
        }
        yield _sse_camera_frame(metric)
        await asyncio.sleep(_SSE_INTERVAL)


@router.get("/stream")
async def camera_sse() -> StreamingResponse:
    return StreamingResponse(
        camera_metrics_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/snapshot/{camera_id}")
async def camera_snapshot(camera_id: int) -> Response:
    """Proxy JPEG: el navegador no envía Basic Auth a MotionEye; el backend sí."""
    data, ctype = await _snapshot_bytes(camera_id)
    return Response(content=data, media_type=ctype)


@router.get("/frame/latest")
async def camera_frame_latest(camera_id: int = 1) -> Response:
    """Alias para plantillas que esperan /frame/latest (cámara 1 por defecto)."""
    data, ctype = await _snapshot_bytes(camera_id)
    return Response(content=data, media_type=ctype)
