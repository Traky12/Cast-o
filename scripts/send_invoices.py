#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Envía por email las facturas de un mes (period_yyyymm) usando SMTP de .env."""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.billing_utils import send_invoice_email  # noqa: E402
from backend.services.water_billing import list_invoices_for_period_yyyymm  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Enviar facturas HTML por SMTP")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    args = p.parse_args()
    yyyymm = f"{args.year}{args.month:02d}"
    rows = list_invoices_for_period_yyyymm(yyyymm)
    if not rows:
        print(f"Sin facturas para period_yyyymm={yyyymm}")
        return
    ok = 0
    for inv in rows:
        if send_invoice_email(inv):
            ok += 1
            print("Enviado:", inv.get("invoice_number"), inv.get("customer_email"))
        else:
            print("Fallo:", inv.get("invoice_number"))
    print(f"Enviados {ok}/{len(rows)}")


if __name__ == "__main__":
    main()
