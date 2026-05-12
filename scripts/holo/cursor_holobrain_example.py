#!/usr/bin/env python3
"""
Ejemplo mínimo: enviar métricas al webhook n8n Holobrain (stub en repo).

Requiere: pip install requests
Webhook: importar y activar n8n/workflows/castuo-holobrain-webhook-stub.json
  → POST {N8N_BASE}/webhook/holobrain-display

No usa hologramapi ni TTS embebidos: la respuesta JSON puede alimentar un servicio
de render o un front que tú despliegues.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from holobrain_client import HolobrainClient


def post_holobrain(
    base_url: str,
    metrics: dict[str, Any],
    *,
    webhook_path: str = "holobrain-display",
    timeout: float = 30.0,
    basic_user: str | None = None,
    basic_pass: str | None = None,
    hmac_secret: str | None = None,
) -> requests.Response:
    client = HolobrainClient(
        n8n_base_url=base_url,
        webhook_path=webhook_path,
        hmac_secret=hmac_secret,
        basic_user=basic_user,
        basic_pass=basic_pass,
        timeout=timeout,
    )
    return client.send(metrics)


def main() -> int:
    p = argparse.ArgumentParser(description="POST métricas al webhook Holobrain stub (n8n).")
    p.add_argument(
        "--base-url",
        default=os.environ.get("N8N_WEBHOOK_BASE", "http://localhost:5678").strip(),
        help="Origen sin path final (ej. http://localhost:5678)",
    )
    p.add_argument(
        "--basic-user",
        default=os.environ.get("N8N_BASIC_AUTH_USER", "").strip() or None,
    )
    p.add_argument(
        "--basic-pass",
        default=os.environ.get("N8N_BASIC_AUTH_PASSWORD", "").strip() or None,
    )
    p.add_argument(
        "--webhook-path",
        default=os.environ.get("HOLOBRAIN_WEBHOOK_PATH", "holobrain-display").strip(),
        help="Segmento tras /webhook/ (stub por defecto: holobrain-display)",
    )
    p.add_argument(
        "--hmac-secret",
        default=os.environ.get("HOLOBRAIN_HMAC_SECRET", "").strip() or None,
        help="Si se define, envía X-Holobrain-HMAC (HMAC-SHA256 alineado al stub n8n)",
    )
    p.add_argument(
        "--demo-critical",
        action="store_true",
        help="Enviar payload de demo crítica (pH alto, válvula V-102).",
    )
    args = p.parse_args()

    if args.demo_critical:
        metrics: dict[str, Any] = {
            "plant_status": "critical",
            "ph": 8.2,
            "ec": 2.1,
            "temperature": 31.0,
            "sensor_id": "V-102",
        }
    else:
        metrics = {
            "plant_status": "optimal",
            "ph": 5.9,
            "ec": 1.15,
            "temperature": 22.5,
            "sensor_id": "S-001",
        }

    try:
        r = post_holobrain(
            args.base_url,
            metrics,
            webhook_path=args.webhook_path,
            basic_user=args.basic_user,
            basic_pass=args.basic_pass,
            hmac_secret=args.hmac_secret,
        )
    except requests.RequestException as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1

    out: dict[str, Any] = {"ok": r.ok, "status_code": r.status_code}
    try:
        out["body"] = r.json()
    except json.JSONDecodeError:
        out["body"] = r.text[:2000]
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if r.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
