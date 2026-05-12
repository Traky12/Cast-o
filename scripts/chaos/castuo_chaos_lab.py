#!/usr/bin/env python3
"""
Laboratorio de chaos / resiliencia: sondas HTTP, muestra aleatoria de núcleos, medición de RTO observado.

No pausa contenedores ni corta red. El operador inyecta el fallo; este script mide y documenta.

Uso:
  python scripts/chaos/castuo_chaos_lab.py probe --targets-file targets.json --out probe.json
  python scripts/chaos/castuo_chaos_lab.py drill-sample --targets-file targets.json --count 50 --seed 1
  python scripts/chaos/castuo_chaos_lab.py recovery --targets-file targets.json --interval 2 --max-wait 600 --out recovery.json
  python scripts/chaos/castuo_chaos_lab.py report --probe probe.json --recovery recovery.json --out resilience.md
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class Target:
    id: str
    url: str
    method: str = "GET"
    expect_status: int = 200


def _load_targets(path: Path) -> list[Target]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("El JSON debe ser una lista de objetivos.")
    out: list[Target] = []
    for i, row in enumerate(raw):
        if not isinstance(row, dict) or "id" not in row or "url" not in row:
            raise ValueError(f"Objetivo inválido en índice {i}: falta id o url.")
        out.append(
            Target(
                id=str(row["id"]),
                url=str(row["url"]),
                method=str(row.get("method", "GET")).upper(),
                expect_status=int(row.get("expect_status", 200)),
            )
        )
    return out


def _probe_one(t: Target, timeout: float) -> dict[str, Any]:
    t0 = time.perf_counter()
    err: str | None = None
    status: int | None = None
    try:
        req = Request(t.url, method=t.method, headers={"User-Agent": "castuo-chaos-lab/1"})
        with urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
    except HTTPError as e:
        status = e.code
    except (URLError, TimeoutError, OSError) as e:
        err = f"{type(e).__name__}: {e}"
    dt = time.perf_counter() - t0
    ok = status == t.expect_status
    return {
        "id": t.id,
        "url": t.url,
        "method": t.method,
        "expect_status": t.expect_status,
        "observed_status": status,
        "ok": ok,
        "latency_s": round(dt, 4),
        "error": err,
    }


def cmd_probe(args: argparse.Namespace) -> int:
    targets = _load_targets(Path(args.targets_file))
    timeout = float(args.timeout)
    results = [_probe_one(t, timeout) for t in targets]
    payload = {
        "kind": "chaos_probe",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "targets": results,
        "summary": {
            "total": len(results),
            "ok": sum(1 for r in results if r["ok"]),
            "fail": sum(1 for r in results if not r["ok"]),
        },
    }
    out_path = Path(args.out) if args.out else None
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if payload["summary"]["fail"] == 0 else 2


def cmd_drill_sample(args: argparse.Namespace) -> int:
    targets = _load_targets(Path(args.targets_file))
    if not targets:
        print("Lista de objetivos vacía.", file=sys.stderr)
        return 1
    rng = random.Random(int(args.seed))
    n = min(int(args.count), len(targets))
    picked = rng.sample([t.id for t in targets], n)
    payload = {
        "kind": "chaos_drill_sample",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "count_requested": int(args.count),
        "count_applied": n,
        "seed": int(args.seed),
        "selected_ids": sorted(picked),
        "note": "Inyectar fallo en estos ids manualmente (docker pause, iptables, etc.); el script no modifica la infra.",
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_recovery(args: argparse.Namespace) -> int:
    targets = _load_targets(Path(args.targets_file))
    interval = float(args.interval)
    max_wait = float(args.max_wait)
    probe_timeout = float(args.probe_timeout)
    timeout_wall = time.perf_counter() + max_wait
    t_start = time.perf_counter()
    iso_start = datetime.now(timezone.utc).isoformat()
    iterations: list[dict[str, Any]] = []
    rto_s: float | None = None

    while time.perf_counter() < timeout_wall:
        iter_t0 = time.perf_counter()
        results = [_probe_one(t, probe_timeout) for t in targets]
        all_ok = all(r["ok"] for r in results)
        iterations.append(
            {
                "ts_utc": datetime.now(timezone.utc).isoformat(),
                "all_ok": all_ok,
                "results": results,
            }
        )
        if all_ok:
            rto_s = time.perf_counter() - t_start
            break
        sleep_for = interval - (time.perf_counter() - iter_t0)
        if sleep_for > 0:
            time.sleep(sleep_for)

    payload = {
        "kind": "chaos_recovery",
        "started_at_utc": iso_start,
        "interval_s": interval,
        "max_wait_s": max_wait,
        "rto_s_observed": round(rto_s, 3) if rto_s is not None else None,
        "recovered": rto_s is not None,
        "iterations": iterations,
        "disclaimer": "RTO = tiempo hasta que todas las sondas devolvieron expect_status; no implica failover automático sin diseño explícito.",
    }
    out_path = Path(args.out) if args.out else None
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0 if rto_s is not None else 3


def cmd_report(args: argparse.Namespace) -> int:
    probe_path = Path(args.probe)
    recovery_path = Path(args.recovery)
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    recovery = json.loads(recovery_path.read_text(encoding="utf-8"))
    lines = [
        "# Informe de resiliencia (laboratorio CASTÚO)",
        "",
        f"Generado (UTC): {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Línea base (probe)",
        "",
        f"- Total objetivos: {probe.get('summary', {}).get('total', 'n/d')}",
        f"- OK: {probe.get('summary', {}).get('ok', 'n/d')} · Fallos: {probe.get('summary', {}).get('fail', 'n/d')}",
        f"- Marca temporal: {probe.get('ts_utc', 'n/d')}",
        "",
        "## Recuperación observada",
        "",
        f"- RTO observado (s): {recovery.get('rto_s_observed', 'n/d')}",
        f"- Recuperado antes del timeout: {recovery.get('recovered', 'n/d')}",
        f"- Inicio: {recovery.get('started_at_utc', 'n/d')}",
        "",
        f"> {recovery.get('disclaimer', '')}",
        "",
        "## Iteraciones",
        "",
        f"- Número de rondas de sonda: {len(recovery.get('iterations', []))}",
        "",
        "## Fuentes",
        "",
        f"- Probe: `{probe_path.as_posix()}`",
        f"- Recovery: `{recovery_path.as_posix()}`",
        "",
    ]
    text = "\n".join(lines)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="CASTÚO chaos lab — sondas HTTP y RTO observado.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="Una ronda de sonda a todos los objetivos.")
    p_probe.add_argument("--targets-file", required=True)
    p_probe.add_argument("--timeout", type=float, default=10.0)
    p_probe.add_argument("--out", default="", help="JSON de salida (opcional).")
    p_probe.set_defaults(func=cmd_probe)

    p_drill = sub.add_parser("drill-sample", help="Elige N ids aleatorios para el ensayo manual.")
    p_drill.add_argument("--targets-file", required=True)
    p_drill.add_argument("--count", type=int, default=50)
    p_drill.add_argument("--seed", type=int, default=1)
    p_drill.set_defaults(func=cmd_drill_sample)

    p_rec = sub.add_parser("recovery", help="Repite sondas hasta todo OK o timeout (estima RTO).")
    p_rec.add_argument("--targets-file", required=True)
    p_rec.add_argument("--interval", type=float, default=2.0)
    p_rec.add_argument(
        "--max-wait",
        type=float,
        default=600.0,
        help="Tiempo máximo de espera total (s).",
    )
    p_rec.add_argument("--probe-timeout", type=float, default=10.0, help="Timeout por petición HTTP (s).")
    p_rec.add_argument("--out", default="", help="JSON de salida.")
    p_rec.set_defaults(func=cmd_recovery)

    p_rep = sub.add_parser("report", help="Markdown desde probe + recovery JSON.")
    p_rep.add_argument("--probe", required=True)
    p_rep.add_argument("--recovery", required=True)
    p_rep.add_argument("--out", required=True)
    p_rep.set_defaults(func=cmd_report)

    args = p.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
