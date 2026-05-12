"""
Métricas Prometheus opt-in para el lab stub (CASTUO_PROMETHEUS_METRICS=1).
Sin dependencia dura: si falta prometheus_client, no-op silencioso salvo warning al montar /metrics.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, Response

logger = logging.getLogger(__name__)

_hydro_latency: Any = None
_riego_ml_hist: Any = None


def _metrics_enabled() -> bool:
    return os.getenv("CASTUO_PROMETHEUS_METRICS", "").strip() == "1"


def _lazy_histograms() -> tuple[Any, Any]:
    global _hydro_latency, _riego_ml_hist
    if _hydro_latency is not None and _riego_ml_hist is not None:
        return _hydro_latency, _riego_ml_hist
    from prometheus_client import Histogram

    _hydro_latency = Histogram(
        "castuo_neuro_hydro_infer_seconds",
        "Latencia inferencia hidropónica lab",
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0),
    )
    _riego_ml_hist = Histogram(
        "castuo_neuro_riego_ml",
        "riego_ml devuelto por inferencia lab",
        buckets=(0, 50, 100, 200, 400, 600, 800, 1000),
    )
    return _hydro_latency, _riego_ml_hist


def record_neuro_infer_seconds(latency_s: float, riego_ml: int) -> None:
    if not _metrics_enabled():
        return
    try:
        lat, riego = _lazy_histograms()
        lat.observe(max(0.0, float(latency_s)))
        riego.observe(float(riego_ml))
    except Exception as exc:
        logger.debug("prometheus record_neuro: %s", exc)


def attach_lab_prometheus(app: FastAPI) -> None:
    if not _metrics_enabled():
        return
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    except ImportError:
        logger.warning("prometheus_client no instalado; /metrics no disponible")
        return

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
