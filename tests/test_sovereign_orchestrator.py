"""
Tests unitarios para services/orchestrator/sovereign_orchestrator.py
Cubre: health checks, get_system_summary y route_task (ai_inference, blockchain, iot_alert).
"""
from __future__ import annotations
import pytest
import httpx

from config.global_config import SovereignOrchestrator
from services.orchestrator.sovereign_orchestrator import (
    CastouSovereignOrchestrator,
    OrchestratorTask,
    ServiceStatus,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def config() -> SovereignOrchestrator:
    return SovereignOrchestrator()


def _make_orchestrator(transport: httpx.AsyncBaseTransport) -> CastouSovereignOrchestrator:
    """Crea un orquestador con cliente HTTP mockeado vía MockTransport."""
    orch = CastouSovereignOrchestrator()
    # Inyectamos un cliente con transport de prueba
    orch._http_client = httpx.AsyncClient(transport=transport, base_url="http://test")  # type: ignore[assignment]
    return orch


# ─────────────────────────────────────────────────────────────────────────────
# Health checks
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_check_service_health_healthy() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"}, request=request)

    orch = _make_orchestrator(httpx.MockTransport(handler))
    result = await orch.check_service_health("mistral", "http://mistral-service:8000")
    await orch.close()

    assert result.service == "mistral"
    assert result.status == ServiceStatus.HEALTHY
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_check_service_health_degraded() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"status": "degraded"}, request=request)

    orch = _make_orchestrator(httpx.MockTransport(handler))
    result = await orch.check_service_health("sabionda", "http://sabionda:6000")
    await orch.close()

    assert result.status == ServiceStatus.DEGRADED


@pytest.mark.asyncio
async def test_check_service_health_unavailable_on_exception() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    orch = _make_orchestrator(httpx.MockTransport(handler))
    result = await orch.check_service_health("n8n", "http://n8n:5678")
    await orch.close()

    assert result.status == ServiceStatus.UNAVAILABLE
    assert result.error is not None


@pytest.mark.asyncio
async def test_check_service_health_skips_postgresql() -> None:
    """Los endpoints postgresql:// no se verifican por HTTP → UNKNOWN."""
    orch = CastouSovereignOrchestrator()
    result = await orch.check_service_health("arsys_db", "postgresql://arsys-db:5432")
    await orch.close()

    assert result.status == ServiceStatus.UNKNOWN


# ─────────────────────────────────────────────────────────────────────────────
# get_system_summary (lógica pura, sin HTTP)
# ─────────────────────────────────────────────────────────────────────────────

def test_get_system_summary_all_healthy(config: SovereignOrchestrator) -> None:
    from services.orchestrator.sovereign_orchestrator import ServiceHealthResult

    health = {
        "a": ServiceHealthResult("a", ServiceStatus.HEALTHY, 10.0, "http://a", "2026-01-01T00:00:00Z"),
        "b": ServiceHealthResult("b", ServiceStatus.HEALTHY, 20.0, "http://b", "2026-01-01T00:00:00Z"),
    }
    orch = CastouSovereignOrchestrator(config)
    summary = orch.get_system_summary(health)

    assert summary["overall_status"] == ServiceStatus.HEALTHY
    assert summary["services"]["healthy"] == 2
    assert summary["services"]["unavailable"] == 0


def test_get_system_summary_majority_unavailable(config: SovereignOrchestrator) -> None:
    from services.orchestrator.sovereign_orchestrator import ServiceHealthResult

    health = {
        "a": ServiceHealthResult("a", ServiceStatus.UNAVAILABLE, 0, "http://a", "2026-01-01"),
        "b": ServiceHealthResult("b", ServiceStatus.UNAVAILABLE, 0, "http://b", "2026-01-01"),
        "c": ServiceHealthResult("c", ServiceStatus.HEALTHY, 5, "http://c", "2026-01-01"),
    }
    orch = CastouSovereignOrchestrator(config)
    summary = orch.get_system_summary(health)

    assert summary["overall_status"] == ServiceStatus.UNAVAILABLE


# ─────────────────────────────────────────────────────────────────────────────
# route_task
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_route_task_unknown_type() -> None:
    """Un tipo de tarea desconocido devuelve status=error sin llamadas HTTP."""
    orch = CastouSovereignOrchestrator()
    task = OrchestratorTask(
        task_id="t-001",
        task_type="unknown_type",
        payload={},
    )
    result = await orch.route_task(task)
    await orch.close()

    assert result["status"] == "error"
    assert "unknown_type" in result["error"]


@pytest.mark.asyncio
async def test_route_task_ai_inference_mistral() -> None:
    """Inferencia AI: Mistral responde 200 → status=completed, provider=mistral."""
    mistral_payload = {
        "choices": [{"message": {"content": "respuesta de prueba"}}]
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=mistral_payload, request=request)

    orch = _make_orchestrator(httpx.MockTransport(handler))
    task = OrchestratorTask(
        task_id="t-002",
        task_type="ai_inference",
        payload={"prompt": "¿Cuándo regar el tomate?"},
    )
    result = await orch.route_task(task)
    await orch.close()

    assert result["status"] == "completed"
    assert result["provider"] == "mistral"
    assert result["result"] == "respuesta de prueba"


@pytest.mark.asyncio
async def test_route_task_ai_inference_fallback_sabionda() -> None:
    """Cuando Mistral falla, se usa SABIONDA como fallback."""
    call_count = {"n": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise httpx.ConnectError("mistral unreachable")
        # Segunda llamada → SABIONDA
        return httpx.Response(200, json={"inference": "sabionda result"}, request=request)

    orch = _make_orchestrator(httpx.MockTransport(handler))
    task = OrchestratorTask(
        task_id="t-003",
        task_type="ai_inference",
        payload={"prompt": "Análisis de cultivo"},
    )
    result = await orch.route_task(task)
    await orch.close()

    assert result["status"] == "completed"
    assert result["provider"] == "sabionda_fallback"


@pytest.mark.asyncio
async def test_route_task_blockchain_register() -> None:
    """Registro en blockchain devuelve status=registered con tx_hash."""
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"tx_hash": "0xABCDEF123456"}, request=request)

    orch = _make_orchestrator(httpx.MockTransport(handler))
    task = OrchestratorTask(
        task_id="t-004",
        task_type="blockchain_register",
        payload={"contract": "trazabilidad", "data": {"lote_id": "LOTE-001"}},
    )
    result = await orch.route_task(task)
    await orch.close()

    assert result["status"] == "registered"
    assert result["tx_hash"] == "0xABCDEF123456"


@pytest.mark.asyncio
async def test_route_task_iot_alert_irrigation_required() -> None:
    """Alerta IoT de humedad baja → action_required=True, alert_type=irrigation_required."""
    orch = CastouSovereignOrchestrator()
    task = OrchestratorTask(
        task_id="t-005",
        task_type="iot_alert",
        payload={"sensor_id": "sensor-001", "metric": "humedad_suelo", "value": 20},
    )
    result = await orch.route_task(task)
    await orch.close()

    assert result["status"] == "processed"
    assert result["action_required"] is True
    assert result["alert_type"] == "irrigation_required"


@pytest.mark.asyncio
async def test_route_task_iot_alert_no_action() -> None:
    """Alerta IoT con valores dentro de umbrales → action_required=False."""
    orch = CastouSovereignOrchestrator()
    task = OrchestratorTask(
        task_id="t-006",
        task_type="iot_alert",
        payload={"sensor_id": "sensor-002", "metric": "humedad_suelo", "value": 65},
    )
    result = await orch.route_task(task)
    await orch.close()

    assert result["status"] == "processed"
    assert result["action_required"] is False
