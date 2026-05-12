# -*- coding: utf-8 -*-
"""
Router Alertas — Dashboard de alertas IoT 3 cooperativas (últimas 24h).
GET /alertas: lee backend/logs/alertas.log y devuelve alertas activas.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

router = APIRouter(tags=["Alertas IoT"])

_LOG_PATH = Path(__file__).resolve().parents[1] / "logs" / "alertas.log"
_MAX_LINES = 50
_ULTIMAS = 10


@router.get("/alertas")
async def dashboard_alertas():
    """Alertas activas últimas 24h (últimas 50 líneas del log, últimos 10 eventos con 🚨/⚠️)."""
    if not _LOG_PATH.is_file():
        return {"alertas_activas": 0, "ultimas": [], "log_path": str(_LOG_PATH)}
    try:
        text = _LOG_PATH.read_text(encoding="utf-8", errors="replace")
        lines = [l.rstrip() for l in text.strip().splitlines() if l.strip()][-_MAX_LINES:]
    except Exception:
        return {"alertas_activas": 0, "ultimas": []}
    alertas = []
    for line in lines:
        if "🚨" in line or "⚠️" in line:
            # Líneas de _send: "YYYY-MM-DD HH:MM mensaje"
            if len(line) >= 17 and line[:4].isdigit():
                timestamp, mensaje = line[:16], line[17:].strip()
            else:
                timestamp, mensaje = "", line
            alertas.append({"timestamp": timestamp, "mensaje": mensaje})
    ultimas = alertas[-_ULTIMAS:]
    return {"alertas_activas": len(alertas), "ultimas": ultimas}
