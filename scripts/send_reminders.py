#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Envía recordatorios por email para facturas vencidas (SMTP en .env)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.billing_utils import send_invoice_email  # noqa: E402
from backend.services.water_billing import get_overdue_invoices  # noqa: E402


def main() -> None:
    min_days = int(os.getenv("WATER_OVERDUE_MIN_DAYS") or "0")
    overdue = get_overdue_invoices(min_days_overdue=min_days)
    if not overdue:
        print("No hay facturas vencidas pendientes.")
        return
    ok = 0
    for inv in overdue:
        if send_invoice_email(inv):
            ok += 1
            print("Enviado:", inv.get("invoice_number"), inv.get("customer_email"))
        else:
            print("Fallo:", inv.get("invoice_number"))
    print(f"Enviados {ok}/{len(overdue)}")


if __name__ == "__main__":
    main()
