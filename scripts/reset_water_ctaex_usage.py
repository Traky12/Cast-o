#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vacía contadores de cuota mensual /water/ctaex (SQLite). Uso: pruebas o mantenimiento."""

from __future__ import annotations

import os
import sys

# Raíz del repo en PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.water_ctaex_plans import clear_usage_records  # noqa: E402


def main() -> None:
    nu, nl = clear_usage_records()
    print(f"Filas eliminadas: monthly_usage={nu}, usage_logs={nl}")


if __name__ == "__main__":
    main()
