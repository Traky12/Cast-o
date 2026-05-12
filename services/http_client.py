"""Utilidades HTTP compartidas para clientes de services/."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Iterable

import httpx


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 2
    base_delay_seconds: float = 0.4
    retryable_statuses: tuple[int, ...] = (408, 429, 500, 502, 503, 504)


def build_async_client(
    *,
    base_url: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | httpx.Timeout = 30.0,
    transport: httpx.AsyncBaseTransport | None = None,
) -> httpx.AsyncClient:
    """Construye un AsyncClient con límites adecuados para pooling y keep-alive."""
    return httpx.AsyncClient(
        base_url=base_url or "",
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
        transport=transport,
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
    )


def _is_retryable_status(status_code: int, retryable_statuses: Iterable[int]) -> bool:
    return status_code in retryable_statuses


async def request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    retry_policy: RetryPolicy | None = None,
    **kwargs: Any,
) -> httpx.Response:
    """Ejecuta una request con retry exponencial sobre códigos y errores transitorios."""
    policy = retry_policy or RetryPolicy()
    request_method = getattr(client, method.lower())
    last_error: httpx.RequestError | None = None

    for attempt in range(policy.attempts + 1):
        try:
            response = await request_method(url, **kwargs)
            if _is_retryable_status(response.status_code, policy.retryable_statuses):
                if attempt < policy.attempts:
                    await asyncio.sleep(policy.base_delay_seconds * (2 ** attempt))
                    continue
            return response
        except httpx.RequestError as exc:
            last_error = exc
            if attempt >= policy.attempts:
                raise
            await asyncio.sleep(policy.base_delay_seconds * (2 ** attempt))

    if last_error is not None:
        raise last_error
    raise RuntimeError("HTTP request retry loop exhausted unexpectedly")