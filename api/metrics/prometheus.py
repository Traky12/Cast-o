"""
Métricas de negocio Prometheus para CASTÚO-SYSTEM™.

Expone /metrics con métricas de lotes, IoT, blockchain, documentos y latencia.
"""

import time
from typing import Any, Awaitable, Callable

from fastapi import FastAPI
from fastapi import Request, Response

content_type_latest = "text/plain; version=0.0.4; charset=utf-8"
generate_latest: Callable[[], bytes] | None = None
registry: Any = None
prometheus_counter: Any = None
prometheus_gauge: Any = None
prometheus_histogram: Any = None
prometheus_available = False

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        REGISTRY,
        generate_latest,
    )

    content_type_latest = CONTENT_TYPE_LATEST
    registry = REGISTRY
    prometheus_counter = Counter
    prometheus_gauge = Gauge
    prometheus_histogram = Histogram
    prometheus_available = True
except ImportError:  # pragma: no cover
    pass

# ------------------------------------------------------------------
# Definición de métricas (sólo si prometheus_client está instalado)
# ------------------------------------------------------------------


class _NoopMetric:
    def labels(self, *args: Any, **kwargs: Any) -> "_NoopMetric":
        return self

    def inc(self, *args: Any, **kwargs: Any) -> None:
        return None

    def observe(self, *args: Any, **kwargs: Any) -> None:
        return None

    def set(self, *args: Any, **kwargs: Any) -> None:
        return None


def _get_or_create_metric(
    factory: Callable[..., Any] | None,
    name: str,
    documentation: str,
    labelnames: list[str] | None = None,
) -> Any:
    if not prometheus_available or factory is None or registry is None:
        return _NoopMetric()

    existing = registry._names_to_collectors.get(name)  # type: ignore[attr-defined]
    if existing is not None:
        return existing

    labels = labelnames or []
    return factory(name, documentation, labels)


api_uptime_seconds = _get_or_create_metric(
    prometheus_gauge,
    "castuo_api_uptime_seconds",
    "Uptime de la API en segundos",
)
api_requests_total = _get_or_create_metric(
    prometheus_counter,
    "castuo_api_requests_total",
    "Total de requests HTTP en la API",
    ["method", "path"],
)
lotes_procesados = _get_or_create_metric(
    prometheus_counter,
    "castuo_lotes_procesados_total",
    "Total de lotes procesados",
    ["tenant", "status"],
)
iot_requests = _get_or_create_metric(
    prometheus_counter,
    "castuo_iot_requests_total",
    "Requests IoT recibidos",
    ["tenant", "device_id"],
)
blockchain_tx = _get_or_create_metric(
    prometheus_counter,
    "castuo_blockchain_tx_total",
    "Transacciones en blockchain",
    ["tenant", "chain", "status"],
)
documentos_generados = _get_or_create_metric(
    prometheus_counter,
    "castuo_documentos_generados_total",
    "Documentos generados (PDF/QR)",
    ["tenant", "type", "signed"],
)
latencia_endpoint = _get_or_create_metric(
    prometheus_histogram,
    "castuo_endpoint_latency_seconds",
    "Latencia de endpoints (segundos)",
    ["tenant", "endpoint", "status_code"],
)
system_memory_usage = _get_or_create_metric(
    prometheus_gauge,
    "castuo_system_memory_usage_bytes",
    "Uso de memoria del sistema",
)
lesson_views = _get_or_create_metric(
    prometheus_counter,
    "lesson_views_total",
    "Total de lecciones vistas",
    ["age_group", "topic"],
)
user_logins = _get_or_create_metric(
    prometheus_gauge,
    "active_users",
    "Usuarios activos por region",
    ["region"],
)
holo_renders_total = _get_or_create_metric(
    prometheus_counter,
    "castuo_holo_renders_total",
    "Total de renders holograficos generados",
    ["farm_id", "scene"],
)
holo_tracking_frames_total = _get_or_create_metric(
    prometheus_counter,
    "castuo_holo_tracking_frames_total",
    "Frames de tracking gestual recibidos",
    ["farm_id", "gesture"],
)
holo_haptics_commands_total = _get_or_create_metric(
    prometheus_counter,
    "castuo_holo_haptics_commands_total",
    "Comandos hapticos emitidos",
    ["farm_id", "pattern"],
)
holo_active_sessions = _get_or_create_metric(
    prometheus_gauge,
    "castuo_holo_active_sessions",
    "Numero de sesiones holo activas",
)

# Compatibilidad con imports existentes en otros módulos.
API_UPTIME_SECONDS = api_uptime_seconds
API_REQUESTS_TOTAL = api_requests_total
LOTES_PROCESADOS = lotes_procesados
IOT_REQUESTS = iot_requests
BLOCKCHAIN_TX = blockchain_tx
DOCUMENTOS_GENERADOS = documentos_generados
LATENCIA_ENDPOINT = latencia_endpoint
SYSTEM_MEMORY_USAGE = system_memory_usage
LESSON_VIEWS = lesson_views
USER_LOGINS = user_logins
HOLO_RENDERS_TOTAL = holo_renders_total
HOLO_TRACKING_FRAMES_TOTAL = holo_tracking_frames_total
HOLO_HAPTICS_COMMANDS_TOTAL = holo_haptics_commands_total
HOLO_ACTIVE_SESSIONS = holo_active_sessions


# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------


def setup_metrics(app: FastAPI) -> None:
    """Registra el endpoint /metrics y el middleware de latencia en la app."""

    generate = generate_latest
    if prometheus_available and generate is not None:

        @app.get("/metrics", include_in_schema=False)
        async def _metrics_endpoint() -> Response:  # pyright: ignore[reportUnusedFunction]
            return Response(
                content=generate(),
                media_type=content_type_latest,
            )

        @app.middleware("http")
        # pyright: ignore[reportUnusedFunction]
        async def _monitor_latency(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            start = time.time()
            response = await call_next(request)
            latency = time.time() - start
            tenant = request.headers.get("X-Tenant-Id", "default")
            LATENCIA_ENDPOINT.labels(
                tenant, request.url.path, str(response.status_code)
            ).observe(latency)
            return response


def record_lesson_view(age_group: str, topic: str) -> None:
    LESSON_VIEWS.labels(age_group, topic).inc()


def record_active_users(region: str, count: int) -> None:
    USER_LOGINS.labels(region).set(count)


def set_api_uptime(seconds: float) -> None:
    API_UPTIME_SECONDS.set(seconds)


def increment_api_request(method: str, path: str) -> None:
    API_REQUESTS_TOTAL.labels(method, path).inc()


def record_holo_render(farm_id: str, scene: str) -> None:
    HOLO_RENDERS_TOTAL.labels(farm_id, scene).inc()


def record_holo_tracking_frame(farm_id: str, gesture: str) -> None:
    HOLO_TRACKING_FRAMES_TOTAL.labels(farm_id, gesture).inc()


def record_holo_haptics_command(farm_id: str, pattern: str) -> None:
    HOLO_HAPTICS_COMMANDS_TOTAL.labels(farm_id, pattern).inc()


def set_holo_active_sessions(count: int) -> None:
    HOLO_ACTIVE_SESSIONS.set(count)
