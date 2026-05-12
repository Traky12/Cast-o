#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registra clientes de facturación desde CSV (api_key, plan_id, customer_name, customer_email)."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_billing import register_billing_customer  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="CSV con cabecera: api_key,plan_id,customer_name,customer_email")
    p.add_argument("--dry-run", action="store_true", help="Solo mostrar filas, sin escribir BD")
    args = p.parse_args()
    path = Path(args.csv)
    if not path.is_file():
        print("No existe:", path, file=sys.stderr)
        sys.exit(1)
    ok = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            api_key = (row.get("api_key") or "").strip()
            plan_id = (row.get("plan_id") or "").strip().lower()
            name = (row.get("customer_name") or "").strip()
            email = (row.get("customer_email") or "").strip()
            if not api_key or not plan_id:
                continue
            if args.dry_run:
                print("dry-run:", plan_id, name, email, "(key len)", len(api_key))
                ok += 1
                continue
            try:
                register_billing_customer(
                    api_key=api_key,
                    plan_id=plan_id,
                    customer_name=name,
                    customer_email=email,
                )
                ok += 1
                print("OK", email, plan_id)
            except ValueError as e:
                print("SKIP", email, e, file=sys.stderr)
    print("Filas procesadas:", ok)


if __name__ == "__main__":
    main()
