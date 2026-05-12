#!/usr/bin/env python3
"""
Inyección HTTP hacia el gateway CASTÚO (n8n) con cuerpo alineado a castuo_main_orchestrator_gateway.

Contrato: POST {base}/webhook/castuo-orchestrate con JSON
  {"request_type": "sensor-data", "data": { sensor_id, sensor_type, value, cultivo_id, ... }}
y header X-API-KEY si CASTUO_ORCHESTRATOR_API_KEY está definido en el servidor.

No uses /webhook/sensor-data directo salvo que exista un workflow activo en esa ruta; el README
oficial documenta el gateway (n8n/README-AGRI-BRAIN.md).

Modo de carga: ráfagas por segundo (async + httpx), no "N hilos = RPS" (eso satura el SO).

Requisito: pip install httpx (ya en requirements.txt raíz).

Ejemplo (60 s, 50 RPS base + 10 s de pico a 200 RPS):
  set CASTUO_GATEWAY_URL=http://localhost:5678/webhook/castuo-orchestrate
  set CASTUO_ORCHESTRATOR_API_KEY=tu_clave
  python scripts/tests/stress_gateway_injection.py --duration 60 --base-rps 50 --peak-rps 200 --peak-seconds 10
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import statistics
import sys
import time
from typing import Any

try:
    import httpx
except ImportError:
    print("Instalar httpx: pip install httpx", file=sys.stderr)
    raise SystemExit(1)


def _headers(api_key: str) -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if api_key:
        h["X-API-KEY"] = api_key
    return h


def _body() -> dict[str, Any]:
    return {
        "request_type": "sensor-data",
        "data": {
            "sensor_id": f"sensor-{random.randint(1, 1_000_000):06d}",
            "sensor_type": random.choice(["ph", "temp", "humidity", "ec"]),
            "value": round(random.uniform(0, 10), 2),
            "cultivo_id": f"cultivo-{random.randint(1, 1000):03d}",
            "timestamp": int(time.time()),
        },
    }


async def _one(
    client: httpx.AsyncClient,
    url: str,
    hdrs: dict[str, str],
) -> tuple[int | str, float, str | None]:
    payload = _body()
    t0 = time.perf_counter()
    try:
        r = await client.post(url, json=payload, headers=hdrs, timeout=30.0)
        dt = time.perf_counter() - t0
        return r.status_code, dt, None
    except Exception as e:  # noqa: BLE001 — laboratorio: capturar fallos de red
        dt = time.perf_counter() - t0
        return "error", dt, f"{type(e).__name__}: {e}"


async def _burst(
    client: httpx.AsyncClient,
    url: str,
    hdrs: dict[str, str],
    rps: int,
    chunk: int,
) -> list[tuple[int | str, float, str | None]]:
    out: list[tuple[int | str, float, str | None]] = []
    remaining = rps
    while remaining > 0:
        n = min(chunk, remaining)
        batch = await asyncio.gather(*[_one(client, url, hdrs) for _ in range(n)])
        out.extend(batch)
        remaining -= n
    return out


async def _run_seconds_at_rps(
    client: httpx.AsyncClient,
    url: str,
    hdrs: dict[str, str],
    seconds: int,
    rps: int,
    chunk: int,
) -> list[tuple[int | str, float, str | None]]:
    all_rows: list[tuple[int | str, float, str | None]] = []
    for _ in range(seconds):
        t0 = time.perf_counter()
        all_rows.extend(await _burst(client, url, hdrs, rps, chunk))
        elapsed = time.perf_counter() - t0
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
    return all_rows


def _summarize(rows: list[tuple[int | str, float, str | None]]) -> None:
    n = len(rows)
    if n == 0:
        print("Sin resultados.")
        return
    ok = sum(1 for code, _, _ in rows if code == 200)
    errs = [err for _, _, err in rows if err]
    latencies = [dt for code, dt, err in rows if code == 200 and err is None]
    codes: dict[str, int] = {}
    for code, _, _ in rows:
        k = str(code)
        codes[k] = codes.get(k, 0) + 1

    print("--- resumen (medido en este cliente; no es SLA contractual) ---")
    print(f"requests: {n}")
    print(f"http_200: {ok} ({100.0 * ok / n:.2f}%)")
    print(f"status_mix: {json.dumps(codes, sort_keys=True)}")
    if latencies:
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95) - 1] if len(latencies) > 1 else latencies[0]
        print(f"latencia_s: mean={statistics.mean(latencies):.4f} p50={p50:.4f} p95={p95:.4f}")
    if errs:
        uniq = sorted(set(errs))
        preview = uniq[:5]
        print(f"errores_unicos_muestra: {preview}")
    print("-----------------------------------------------------------------")


async def _amain(args: argparse.Namespace) -> int:
    url = (args.url or os.environ.get("CASTUO_GATEWAY_URL", "")).strip()
    if not url:
        print(
            "Definir --url o CASTUO_GATEWAY_URL (p. ej. http://localhost:5678/webhook/castuo-orchestrate).",
            file=sys.stderr,
        )
        return 1
    api_key = (args.api_key or os.environ.get("CASTUO_ORCHESTRATOR_API_KEY", "")).strip()
    hdrs = _headers(api_key)

    base_s = max(0, args.duration - args.peak_seconds)
    limits = httpx.Limits(max_connections=args.max_connections, max_keepalive_connections=args.max_connections)

    print(
        f"Inyección: url={url} | base {args.base_rps} rps × {base_s}s | "
        f"pico {args.peak_rps} rps × {args.peak_seconds}s | chunk={args.chunk}",
    )
    wall0 = time.perf_counter()
    rows: list[tuple[int | str, float, str | None]] = []

    async with httpx.AsyncClient(limits=limits) as client:
        if base_s > 0:
            print(f"Fase 1: {args.base_rps} req/s durante {base_s} s")
            rows.extend(await _run_seconds_at_rps(client, url, hdrs, base_s, args.base_rps, args.chunk))
        if args.peak_seconds > 0:
            print(f"Fase 2: {args.peak_rps} req/s durante {args.peak_seconds} s")
            rows.extend(await _run_seconds_at_rps(client, url, hdrs, args.peak_seconds, args.peak_rps, args.chunk))

    wall = time.perf_counter() - wall0
    print(f"Tiempo muro: {wall:.2f}s")
    _summarize(rows)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Stress HTTP al gateway castuo-orchestrate (async httpx).")
    p.add_argument("--url", default="", help="Webhook completo del gateway (o env CASTUO_GATEWAY_URL).")
    p.add_argument("--api-key", default="", help="X-API-KEY (o env CASTUO_ORCHESTRATOR_API_KEY).")
    p.add_argument("--duration", type=int, default=60, help="Duración total aproximada (s).")
    p.add_argument("--peak-seconds", type=int, default=10, help="Segundos finales a pico (s).")
    p.add_argument("--base-rps", type=int, default=20, help="RPS en la fase base.")
    p.add_argument("--peak-rps", type=int, default=100, help="RPS en la fase pico.")
    p.add_argument("--chunk", type=int, default=500, help="Concurrencia máxima por sub-ráfaga (evita picos de memoria).")
    p.add_argument(
        "--max-connections",
        type=int,
        default=512,
        help="Límite de conexiones concurrentes del pool httpx.",
    )
    args = p.parse_args()
    if args.duration < args.peak_seconds:
        print("--duration debe ser >= --peak-seconds", file=sys.stderr)
        return 1
    if args.base_rps < 0 or args.peak_rps < 0 or args.chunk < 1:
        print("RPS >= 0 y --chunk >= 1", file=sys.stderr)
        return 1
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
