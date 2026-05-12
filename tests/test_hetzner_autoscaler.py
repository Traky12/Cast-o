"""
Tests unitarios para services/hetzner/autoscaler.py
Cubre: list_servers, create_server, delete_server, evaluate_scaling y get_cluster_health.
"""
from __future__ import annotations
import pytest
import httpx

from config.global_config import HetznerConfig
from services.hetzner.autoscaler import (
    HetznerAutoscaler,
    HetznerServer,
    ScalingDecision,
    ServerSpec,
)
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_autoscaler(transport: httpx.AsyncBaseTransport) -> HetznerAutoscaler:
    """Crea un autoscaler con cliente HTTP mockeado."""
    config = HetznerConfig(api_key="test-key")
    scaler = HetznerAutoscaler(config)
    # Inyectamos transport directamente
    scaler._client = httpx.AsyncClient(  # type: ignore[assignment]
        transport=transport,
        base_url=HetznerAutoscaler.API_BASE,
        headers={"Authorization": "Bearer test-key"},
    )
    return scaler


def _hetzner_server_payload(
    server_id: int = 1,
    name: str = "castuo-fsn1-001",
    status: str = "running",
    location: str = "fsn1",
) -> dict[str, Any]:
    return {
        "id": server_id,
        "name": name,
        "status": status,
        "server_type": {"name": "cx21", "cores": 2, "memory": 4.0},
        "datacenter": {"location": {"name": location}},
        "public_net": {
            "ipv4": {"ip": "1.2.3.4"},
            "ipv6": {"ip": "::1"},
        },
        "created": "2026-01-01T00:00:00Z",
    }


# ─────────────────────────────────────────────────────────────────────────────
# list_servers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_servers_empty() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"servers": []}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))
    servers = await scaler.list_servers()
    await scaler.close()

    assert servers == []


@pytest.mark.asyncio
async def test_list_servers_returns_hetzner_server_objects() -> None:
    payload = {"servers": [_hetzner_server_payload(1, "castuo-fsn1-001", "running", "fsn1")]}

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))
    servers = await scaler.list_servers()
    await scaler.close()

    assert len(servers) == 1
    s = servers[0]
    assert isinstance(s, HetznerServer)
    assert s.id == 1
    assert s.name == "castuo-fsn1-001"
    assert s.status == "running"
    assert s.ipv4 == "1.2.3.4"
    assert s.cpu_cores == 2
    assert s.ram_gb == 4.0


@pytest.mark.asyncio
async def test_list_servers_with_label_selector() -> None:
    """Verifica que se pasa el parámetro label_selector en la query."""
    received: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        received["url"] = str(request.url)
        return httpx.Response(200, json={"servers": []}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))
    await scaler.list_servers(label_selector="system=castuo-system")
    await scaler.close()

    assert "label_selector=system%3Dcastuo-system" in received["url"]


# ─────────────────────────────────────────────────────────────────────────────
# create_server
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_server_returns_hetzner_server() -> None:
    server_data = _hetzner_server_payload(42, "castuo-fsn1-auto-000", "initializing", "fsn1")

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"server": server_data}, request=request)

    spec = ServerSpec(
        name="castuo-fsn1-auto-000",
        server_type="cx21",
        image="ubuntu-22.04",
        location="fsn1",
    )
    scaler = _make_autoscaler(httpx.MockTransport(handler))
    created = await scaler.create_server(spec)
    await scaler.close()

    assert isinstance(created, HetznerServer)
    assert created.id == 42
    assert created.server_type == "cx21"
    assert created.location == "fsn1"


# ─────────────────────────────────────────────────────────────────────────────
# delete_server
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_server_succeeds() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))
    await scaler.delete_server(42)  # no debe lanzar excepción
    await scaler.close()


# ─────────────────────────────────────────────────────────────────────────────
# evaluate_scaling (lógica de hysteresis, no necesita HTTP real)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluate_scaling_maintain() -> None:
    """CPU dentro del rango normal → acción=maintain."""
    server_list = [_hetzner_server_payload(i, f"castuo-fsn1-{i:03d}") for i in range(2)]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"servers": server_list}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))
    decision = await scaler.evaluate_scaling("fsn1", current_cpu_avg=50.0)
    await scaler.close()

    assert decision.action == "maintain"


@pytest.mark.asyncio
async def test_evaluate_scaling_scale_up_after_three_cycles() -> None:
    """CPU > 80% durante 3 ciclos consecutivos → acción=scale_up."""
    server_list = [_hetzner_server_payload(i, f"castuo-fsn1-{i:03d}") for i in range(2)]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"servers": server_list}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))

    decision: ScalingDecision | None = None
    for _ in range(3):
        decision = await scaler.evaluate_scaling("fsn1", current_cpu_avg=85.0)

    await scaler.close()

    assert decision is not None
    assert decision.action == "scale_up"
    assert decision.target_servers > decision.current_servers


@pytest.mark.asyncio
async def test_evaluate_scaling_scale_down_after_five_cycles() -> None:
    """CPU < 30% durante 5 ciclos consecutivos → acción=scale_down."""
    # Necesitamos 4 servidores para poder bajar (mínimo=2)
    server_list = [_hetzner_server_payload(i, f"castuo-fsn1-{i:03d}") for i in range(4)]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"servers": server_list}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))

    decision: ScalingDecision | None = None
    for _ in range(5):
        decision = await scaler.evaluate_scaling("fsn1", current_cpu_avg=20.0)

    await scaler.close()

    assert decision is not None
    assert decision.action == "scale_down"
    assert decision.target_servers < decision.current_servers


@pytest.mark.asyncio
async def test_evaluate_scaling_respects_min_servers() -> None:
    """No baja de auto_scale_min_servers aunque la CPU sea baja."""
    # Exactamente 2 servidores (el mínimo configurado)
    server_list = [_hetzner_server_payload(i, f"castuo-fsn1-{i:03d}") for i in range(2)]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"servers": server_list}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))

    decision: ScalingDecision | None = None
    for _ in range(5):
        decision = await scaler.evaluate_scaling("fsn1", current_cpu_avg=10.0)

    await scaler.close()

    assert decision is not None
    assert decision.action == "maintain"


# ─────────────────────────────────────────────────────────────────────────────
# get_cluster_health
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_cluster_health_aggregates_by_region() -> None:
    server_list = [
        _hetzner_server_payload(1, "castuo-fsn1-001", "running", "fsn1"),
        _hetzner_server_payload(2, "castuo-fsn1-002", "off", "fsn1"),
        _hetzner_server_payload(3, "castuo-nbg1-001", "running", "nbg1"),
    ]

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"servers": server_list}, request=request)

    scaler = _make_autoscaler(httpx.MockTransport(handler))
    health = await scaler.get_cluster_health()
    await scaler.close()

    assert health["total_servers"] == 3
    assert health["running"] == 2
    assert "fsn1" in health["regions"]
    assert health["regions"]["fsn1"]["count"] == 2
    assert health["regions"]["nbg1"]["count"] == 1
    assert health["sovereignty"] == "EU"
