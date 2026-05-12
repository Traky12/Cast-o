#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Informe mensual administrativo: JSON + CSV (clientes de billing + facturas del período)."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_billing import (  # noqa: E402
    get_invoices_by_period,
    monthly_billing_summary,
)


def generate_monthly_report(year: int, month: int) -> dict:
    summary = monthly_billing_summary(year, month)
    invoices = get_invoices_by_period(year, month)
    return {
        "report": {
            "period": summary["period"],
            "period_yyyymm": summary["period_yyyymm"],
            "generated_ref": summary,
            "invoice_rows": invoices,
        },
        "certification": {
            "system": "CASTÚO-SYSTEM water/ctaex",
            "version": "1.7",
            "generated_by": "monthly_report.py",
        },
    }


def _save_csv_fixed(report: dict, filename: str) -> None:
    ref = report["report"]["generated_ref"]
    invoices = report["report"]["invoice_rows"]
    by_hash = {inv["key_hash"]: inv for inv in invoices}
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "key_hash",
                "customer_name",
                "plan_name",
                "requests_in_period",
                "customer_email",
                "invoice_number",
                "total_eur",
                "status",
            ]
        )
        for c in ref.get("customers") or []:
            kh = c.get("key_hash")
            inv = by_hash.get(kh) if kh else None
            w.writerow(
                [
                    kh or "",
                    c.get("customer_name", ""),
                    c.get("plan_name", ""),
                    c.get("requests_in_period", 0),
                    c.get("customer_email", ""),
                    inv.get("invoice_number") if inv else "N/A",
                    round(int(inv.get("total_cents", 0)) / 100.0, 2) if inv else 0,
                    inv.get("status") if inv else "N/A",
                ]
            )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--json", default="monthly_report.json")
    p.add_argument("--csv", default="monthly_report.csv")
    args = p.parse_args()
    report = generate_monthly_report(args.year, args.month)
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    _save_csv_fixed(report, args.csv)
    print("JSON:", os.path.abspath(args.json))
    print("CSV:", os.path.abspath(args.csv))


if __name__ == "__main__":
    main()
