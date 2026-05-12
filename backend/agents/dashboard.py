"""
Dashboard SSE: chunks pequeños + cabeceras estándar; sin Content-Length (el cuerpo es indefinido).
CORS: delegar en CORSMiddleware; no forzar * en esta respuesta (duplica y puede confundir proxies).
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/agents/dashboard", tags=["dashboard"])

metrics_history: deque[dict] = deque(maxlen=100)


def _sse_metric_frame(metric: dict) -> bytes:
    payload = json.dumps(metric, separators=(",", ":"), ensure_ascii=False)
    return f"event: metric_update\ndata: {payload}\n\n".encode("utf-8")


async def dashboard_stream() -> AsyncIterator[bytes]:
    while True:
        t = time.time()
        jitter = abs(hash(str(int(t)))) % 20
        metric = {
            "cpu": round(min(99.0, 23.4 + jitter), 1),
            "memory": 67.2,
            "health": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        metrics_history.append(metric)
        yield _sse_metric_frame(metric)
        await asyncio.sleep(3)


@router.get("/stream")
async def stream_dashboard() -> StreamingResponse:
    return StreamingResponse(
        dashboard_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
