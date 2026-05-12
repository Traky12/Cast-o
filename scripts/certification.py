#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exporta informe certificable (JSON) para un mes — usa generate_certification_report en backend."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_billing import generate_certification_report  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Informe certificable water/ctaex (JSON)")
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--month", type=int, required=True)
    p.add_argument("--output", "-o", default="certification_report.json")
    args = p.parse_args()
    report = generate_certification_report(args.year, args.month)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print("Escrito:", os.path.abspath(args.output))


if __name__ == "__main__":
    main()
