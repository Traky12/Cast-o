#!/usr/bin/env python3
"""
PoC de concurrencia: firmar N payloads como el webhook audit-trigger (stableStringify + HMAC-SHA256).

Qué mide: capacidad de tu máquina para calcular firmas idénticas al pipeline n8n (ver scripts/n8n/sign_audit_webhook_body.py).
Qué NO mide: latencia HTTP del Trillizo, Postgres, disco, failover Docker ni carga real de instancias n8n.

HTTP contra Trillizo: scripts/tests/castuo_trillizo_audit_http_stress.py

Uso (desde la raíz del repo):
  set CASTUO_AUDIT_WEBHOOK_SECRET=una_clave_de_prueba
  python scripts/tests/stress_test_313_cores.py
  python scripts/tests/stress_test_313_cores.py --cores 1000 --workers 64
"""
from __future__ import annotations

import argparse
import hmac
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from castuo_audit_stress_common import build_audit_like_body, sign_body_hmac_sha256


def sign_and_verify(secret: bytes, core_index: int) -> tuple[int, bool, float]:
    body = build_audit_like_body(core_index)
    t0 = time.perf_counter()
    sig = sign_body_hmac_sha256(secret, body)
    ok = hmac.compare_digest(sig, sign_body_hmac_sha256(secret, body))
    dt = time.perf_counter() - t0
    return core_index, ok, dt


def main() -> int:
    parser = argparse.ArgumentParser(description="PoC HMAC concurrente alineado a Trillizo (local).")
    parser.add_argument("--cores", type=int, default=313, help="Número de cuerpos firmados (default 313)")
    parser.add_argument("--workers", type=int, default=50, help="Hilos en el pool (default 50)")
    args = parser.parse_args()

    secret_str = os.environ.get("CASTUO_AUDIT_WEBHOOK_SECRET", "").strip()
    if not secret_str:
        print("Definir CASTUO_AUDIT_WEBHOOK_SECRET en el entorno.", file=sys.stderr)
        return 1
    secret = secret_str.encode("utf-8")

    if args.cores < 1 or args.workers < 1:
        print("--cores y --workers deben ser >= 1", file=sys.stderr)
        return 1

    print(f"CASTUO stress PoC: {args.cores} firmas HMAC (stable_stringify), workers={args.workers}")
    t_wall0 = time.perf_counter()
    results: list[tuple[int, bool, float]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(sign_and_verify, secret, i) for i in range(args.cores)]
        for fut in as_completed(futs):
            results.append(fut.result())
    wall = time.perf_counter() - t_wall0

    oks = sum(1 for _, ok, _ in results if ok)
    times = [dt for _, _, dt in results]
    avg_ms = (sum(times) / len(times)) * 1000 if times else 0.0
    tps = args.cores / wall if wall > 0 else 0.0

    print("--- informe (local, no es SLA de producción) ---")
    print(f"nucleos_firmados: {len(results)}")
    print(f"verificaciones_hmac_compare_digest_ok: {oks}/{len(results)}")
    print(f"tiempo_muro_s: {wall:.4f}")
    print(f"firmas_por_segundo: {tps:.1f}")
    print(f"tiempo_medio_firma_por_nucleo_ms: {avg_ms:.4f}")
    print("nota: no se ha llamado a n8n ni a Docker; failover HA no cubierto por este script.")
    print("-----------------------------------------------")

    return 0 if oks == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
