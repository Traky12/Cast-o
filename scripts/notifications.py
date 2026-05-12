#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Alertas por umbral de cuota (≥80 % del límite del plan) para clientes en billing_customers."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_ctaex_plans import (  # noqa: E402
    PUBLIC_PLANS,
    connection,
    current_period_yyyymm,
    get_usage_count,
)

THRESHOLD = float(os.getenv("WATER_QUOTA_ALERT_THRESHOLD", "0.8"))


def main() -> None:
    period = current_period_yyyymm()
    conn = connection()
    try:
        rows = conn.execute(
            "SELECT key_hash, plan_id, customer_name, customer_email FROM billing_customers"
        ).fetchall()
    finally:
        conn.close()

    alerts: list[str] = []
    for row in rows:
        kh, pid, name, email = row[0], row[1], row[2], row[3]
        cfg = PUBLIC_PLANS.get(pid, {})
        max_r = int(cfg.get("max_requests") or 0)
        if max_r <= 0:
            continue
        used = get_usage_count(kh, period)
        limit = THRESHOLD * max_r
        if used >= limit:
            pct = (100.0 * used / max_r) if max_r else 0.0
            alerts.append(
                f"{name} <{email}> plan={pid} uso={used}/{max_r} ({pct:.0f}%) period={period}"
            )

    if not alerts:
        print("No notifications to send (no clients over threshold)")
        return
    for line in alerts:
        print("ALERT:", line)


if __name__ == "__main__":
    main()
