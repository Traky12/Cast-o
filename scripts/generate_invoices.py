#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera borradores de factura en SQLite para un año/mes (CLI)."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_billing import generate_invoices_for_month  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--year", type=int, default=None)
    p.add_argument("--month", type=int, default=None)
    args = p.parse_args()
    now = datetime.now(timezone.utc)
    year = args.year if args.year is not None else now.year
    month = args.month if args.month is not None else now.month
    rows = generate_invoices_for_month(year, month)
    print(f"Generadas {len(rows)} factura(s) nuevas para {year}-{month:02d}")
    for r in rows:
        print(r.get("invoice_number"), r.get("customer_email"), r.get("total_eur"))


if __name__ == "__main__":
    main()
