#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resetea contadores mensuales (tabla monthly_usage). No borra usage_logs."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_ctaex_plans import reset_all_quotas  # noqa: E402


def main() -> None:
    n = reset_all_quotas()
    print(f"Filas eliminadas en monthly_usage: {n}")


if __name__ == "__main__":
    main()
