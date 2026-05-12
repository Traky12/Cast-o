from __future__ import annotations

import httpx
import pytest

from services.http_client import RetryPolicy, build_async_client, request_with_retry


@pytest.mark.asyncio
async def test_request_with_retry_retries_transient_status() -> None:
    attempts = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(503, json={"status": "retry"}, request=request)
        return httpx.Response(200, json={"status": "ok"}, request=request)

    transport = httpx.MockTransport(handler)
    async with build_async_client(timeout=5.0, transport=transport) as client:
        response = await request_with_retry(
            client,
            "GET",
            "https://example.test/health",
            retry_policy=RetryPolicy(attempts=1, base_delay_seconds=0.0),
        )

    assert response.status_code == 200
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_request_with_retry_does_not_retry_non_transient_status() -> None:
    attempts = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(400, json={"status": "bad-request"}, request=request)

    transport = httpx.MockTransport(handler)
    async with build_async_client(timeout=5.0, transport=transport) as client:
        response = await request_with_retry(
            client,
            "GET",
            "https://example.test/health",
            retry_policy=RetryPolicy(attempts=2, base_delay_seconds=0.0),
        )

    assert response.status_code == 400
    assert attempts["count"] == 1