#!/usr/bin/env python3
"""
POST concurrentes a /webhook/audit-trigger con el mismo cuerpo canónico y HMAC que n8n.

Requisitos:
  - Trillizo activo con workflow 01-trillizo-auditoria-basica (webhook audit-trigger).
  - Si el contenedor tiene CASTUO_AUDIT_WEBHOOK_SECRET, define la misma variable al ejecutar este script.

Staging típico (host → contenedor publicado):
  set CASTUO_AUDIT_WEBHOOK_SECRET=tu_secreto
  python scripts/tests/castuo_trillizo_audit_http_stress.py --url http://127.0.0.1:5682/webhook/audit-trigger

Sin HMAC en Trillizo (solo laboratorio):
  python scripts/tests/castuo_trillizo_audit_http_stress.py --url http://127.0.0.1:5682/webhook/audit-trigger --no-hmac
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from castuo_audit_stress_common import build_audit_like_body, sign_body_hmac_sha256


def one_post(
    url: str,
    core_index: int,
    secret: bytes | None,
    timeout_s: float,
) -> tuple[int, int, float, str]:
    body = build_audit_like_body(core_index)
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if secret is not None:
        sig = sign_body_hmac_sha256(secret, body)
        headers["X-Castuo-Signature"] = sig
    req = urllib.request.Request(url, data=raw, method="POST", headers=headers)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            code = resp.getcode()
            err = ""
    except urllib.error.HTTPError as e:
        code = e.code
        err = (e.read() or b"").decode("utf-8", errors="replace")[:500]
    except urllib.error.URLError as e:
        code = -1
        err = str(e.reason) if getattr(e, "reason", None) else str(e)
    dt = time.perf_counter() - t0
    return core_index, code, dt, err


def main() -> int:
    p = argparse.ArgumentParser(description="HTTP stress PoC → Trillizo audit-trigger")
    p.add_argument(
        "--url",
        default="http://127.0.0.1:5682/webhook/audit-trigger",
        help="URL completa del webhook (default puerto Trillizo en .env.n8n-multi.example)",
    )
    p.add_argument("--requests", type=int, default=50, help="Número de POST (default 50)")
    p.add_argument("--workers", type=int, default=16, help="Concurrencia (default 16)")
    p.add_argument("--timeout", type=float, default=60.0, help="Timeout por petición en s")
    p.add_argument(
        "--no-hmac",
        action="store_true",
        help="No enviar X-Castuo-Signature (Trillizo debe ir sin CASTUO_AUDIT_WEBHOOK_SECRET)",
    )
    args = p.parse_args()

    secret: bytes | None = None
    if not args.no_hmac:
        s = os.environ.get("CASTUO_AUDIT_WEBHOOK_SECRET", "").strip()
        if not s:
            print("Definir CASTUO_AUDIT_WEBHOOK_SECRET o usar --no-hmac.", file=sys.stderr)
            return 1
        secret = s.encode("utf-8")

    if args.requests < 1 or args.workers < 1:
        print("--requests y --workers deben ser >= 1", file=sys.stderr)
        return 1

    mode = "sin HMAC" if args.no_hmac else "HMAC"
    print(f"CASTUO HTTP stress → {args.url} | n={args.requests} workers={args.workers} ({mode})")
    wall0 = time.perf_counter()
    results: list[tuple[int, int, float, str]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [
            ex.submit(one_post, args.url, i, secret, args.timeout) for i in range(args.requests)
        ]
        for fut in as_completed(futs):
            results.append(fut.result())
    wall = time.perf_counter() - wall0

    by_code: dict[int, int] = {}
    latencies: list[float] = []
    errors_sample: list[str] = []
    for _, code, dt, err in results:
        by_code[code] = by_code.get(code, 0) + 1
        if code >= 0:
            latencies.append(dt)
        if err and len(errors_sample) < 3:
            errors_sample.append(err)

    ok_200 = by_code.get(200, 0)
    print("--- informe HTTP (staging / laboratorio) ---")
    print(f"respuestas_por_codigo: {dict(sorted(by_code.items(), key=lambda x: str(x[0])))}")
    print(f"http_200: {ok_200}/{args.requests}")
    if latencies:
        print(f"tiempo_muro_total_s: {wall:.4f}")
        print(f"rps_aprox: {args.requests / wall:.2f}")
        print(f"latencia_media_s: {sum(latencies) / len(latencies):.4f}")
        print(f"latencia_p95_s: {sorted(latencies)[int(0.95 * (len(latencies) - 1))]:.4f}")
    if errors_sample:
        print("muestra_errores:")
        for e in errors_sample:
            print(f"  {e[:200]}")
    print("nota: I/O disco y ejecución n8n dominan; no es benchmark aislado de firma.")
    print("--------------------------------------------")

    return 0 if ok_200 == args.requests else 2


if __name__ == "__main__":
    raise SystemExit(main())
