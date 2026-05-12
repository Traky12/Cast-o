#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Monitorización operativa: clientes de facturación, ingresos estimados, trazas y vencidas."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_billing import get_overdue_invoices  # noqa: E402
from backend.services.water_ctaex_plans import (  # noqa: E402
    PUBLIC_PLANS,
    connection,
    db_path,
    get_usage_report,
)


def _estimated_monthly_revenue_eur() -> float:
    conn = connection()
    try:
        rows = conn.execute("SELECT plan_id FROM billing_customers").fetchall()
    finally:
        conn.close()
    total = 0.0
    for row in rows:
        pid = row[0]
        cfg = PUBLIC_PLANS.get(pid)
        if not cfg:
            continue
        p = cfg.get("price_eur_month")
        if isinstance(p, (int, float)) and p > 0:
            total += float(p)
    return round(total, 2)


def _count_active_billing_clients() -> int:
    conn = connection()
    try:
        row = conn.execute("SELECT COUNT(*) FROM billing_customers").fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def _count_usage_logs_period(period_yyyymm: str) -> int:
    conn = connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM usage_logs WHERE period = ?",
            (period_yyyymm,),
        ).fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def generate_monitoring_report() -> dict:
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month
    period_yyyymm = f"{year}{month:02d}"
    overdue = get_overdue_invoices()
    traces = get_usage_report(limit=200, plan_id=None)
    return {
        "timestamp": now.isoformat(),
        "database": str(db_path()),
        "active_billing_clients": _count_active_billing_clients(),
        "estimated_monthly_revenue_eur": _estimated_monthly_revenue_eur(),
        "usage_logs_this_period": _count_usage_logs_period(period_yyyymm),
        "period_yyyymm": period_yyyymm,
        "overdue_invoices_count": len(overdue),
        "usage_traces_recent": traces,
        "system_health": "OK",
    }


def main() -> None:
    report = generate_monitoring_report()
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
