#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test HTTP para /water/ctaex (health, registro, analyze, facturación, uso).

Requiere API levantada y .env coherente:
- WATER_CTAEX_ENFORCE_QUOTA=1
- WATER_API_KEY_TO_PLAN incluye la clave SMOKE_TEST_API_KEY (default: smoke-test-key)
- WATER_BILLING_REGISTER_KEY, WATER_USAGE_REPORT_KEY

Uso:
  set PYTHONPATH=backend o ejecutar desde raíz del repo:
  python scripts/smoke_test.py
  SMOKE_TEST_BASE_URL=http://127.0.0.1:8000 python scripts/smoke_test.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import httpx  # noqa: E402


def _fail(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_smoke_test() -> bool:
    base = os.getenv("SMOKE_TEST_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    billing_key = os.getenv("WATER_BILLING_REGISTER_KEY", "").strip()
    report_key = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    api_key = os.getenv("SMOKE_TEST_API_KEY", "smoke-test-key").strip()

    if not billing_key or not report_key:
        _fail(
            "Defina WATER_BILLING_REGISTER_KEY y WATER_USAGE_REPORT_KEY en el entorno "
            "(o cargue .env antes de ejecutar).",
            2,
        )

    now = datetime.now(timezone.utc)
    year, month = now.year, now.month
    period_yyyymm = f"{year}{month:02d}"

    print("Smoke test CASTÚO /water/ctaex →", base)

    with httpx.Client(timeout=60.0) as client:
        r = client.get(f"{base}/water/ctaex/health")
        r.raise_for_status()
        health = r.json()
        assert health.get("status") == "healthy", health
        assert health.get("version") == "1.7", f"version inesperada: {health.get('version')}"
        if not health.get("water_quota_enforcement"):
            _fail(
                "water_quota_enforcement es false: ponga WATER_CTAEX_ENFORCE_QUOTA=1 "
                "para registrar uso en usage_logs.",
                3,
            )
        print("OK health (version 1.7, cuota activa)")

        body = {
            "api_key": api_key,
            "plan_id": "basic",
            "customer_name": "Smoke Test Client",
            "customer_email": "smoke@test.com",
        }
        r = client.post(
            f"{base}/water/ctaex/subscription/register",
            json=body,
            headers={"X-BILLING-REGISTER-KEY": billing_key},
        )
        if r.status_code != 200:
            _fail(f"register: {r.status_code} {r.text}", 4)
        reg = r.json()
        assert reg.get("status") == "success", reg
        hfull = reg.get("api_key_hash") or reg.get("key_hash")
        assert hfull, reg
        print("OK register")

        r = client.post(
            f"{base}/water/ctaex/analyze",
            json={"sensor_type": "orp", "sensor_value": 620.0},
            headers={"X-API-KEY": api_key},
        )
        if r.status_code != 200:
            _fail(
                f"analyze: {r.status_code} {r.text}\n"
                f"Asegúrese de que WATER_API_KEY_TO_PLAN incluye \"{api_key}\":\"basic\".",
                5,
            )
        analysis = r.json()
        assert analysis.get("status") == "success", analysis
        assert analysis.get("plan_used") == "basic", analysis
        print("OK analyze (plan basic)")

        r = client.post(
            f"{base}/water/ctaex/subscription/generate-invoices",
            params={"year": year, "month": month},
            headers={"X-USAGE-REPORT-KEY": report_key},
        )
        if r.status_code != 200:
            _fail(f"generate-invoices: {r.status_code} {r.text}", 6)
        gen = r.json()
        assert gen.get("status") == "success", gen
        n_new = int(gen.get("invoices_generated") or gen.get("generated") or 0)
        print(f"OK generate-invoices (nuevas: {n_new})")

        r = client.get(
            f"{base}/water/ctaex/subscription/billing-summary",
            params={"year": year, "month": month},
            headers={"X-USAGE-REPORT-KEY": report_key},
        )
        if r.status_code != 200:
            _fail(f"billing-summary: {r.status_code} {r.text}", 7)
        summary = r.json()
        assert summary.get("period") == f"{year}-{month:02d}", summary
        inv_block = summary.get("invoices") or {}
        cnt = int(inv_block.get("count") or 0)
        if n_new == 0 and cnt < 1:
            _fail(
                "No hay facturas para el período (¿primera ejecución sin billing_customers?).",
                8,
            )
        print(f"OK billing-summary (facturas en BD para período: {cnt})")

        inv_no = f"INV-{period_yyyymm}-{str(hfull)[:8]}"
        r = client.post(
            f"{base}/water/ctaex/subscription/send-invoice",
            params={"invoice_number": inv_no},
            headers={"X-USAGE-REPORT-KEY": report_key},
        )
        if r.status_code != 200:
            _fail(f"send-invoice: {r.status_code} {r.text}", 9)
        send = r.json()
        assert send.get("status") == "success", send
        smtp_ok = bool(os.getenv("SMTP_USERNAME", "").strip() and os.getenv("SMTP_PASSWORD", "").strip())
        if smtp_ok and not send.get("sent"):
            print("WARN send-invoice: SMTP configurado pero envío devolvió sent=false")
        elif not smtp_ok:
            print("OK send-invoice (sent=false esperado sin SMTP_USERNAME/SMTP_PASSWORD)")
        else:
            print("OK send-invoice (sent=true)")

        r = client.get(
            f"{base}/water/ctaex/subscription/usage-report",
            params={"limit": 50},
            headers={"X-USAGE-REPORT-KEY": report_key},
        )
        if r.status_code != 200:
            _fail(f"usage-report: {r.status_code} {r.text}", 10)
        usage = r.json()
        rows = usage.get("report") or usage.get("items") or []
        assert isinstance(rows, list) and len(rows) >= 1, usage
        print(f"OK usage-report ({len(rows)} fila(s))")

    print("Smoke test completado.")
    return True


if __name__ == "__main__":
    run_smoke_test()
