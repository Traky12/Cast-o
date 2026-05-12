# -*- coding: utf-8 -*-
"""
Riego manual (modo abuelo): simulación de riego soberano por sector.
Uso:
  python scripts/educacion/riego_manual.py Norte
  python scripts/educacion/riego_manual.py "Sector 3"
"""
from __future__ import annotations

import sys
import time


def regar(sector: str) -> None:
    print(f"Regando sector {sector} con agua de pozo... (low-tech, soberano)")
    time.sleep(2)
    print("Sector hidratado. La tierra agradece.")


def main(argv: list[str]) -> int:
    sector = argv[1] if len(argv) > 1 else "Norte"
    regar(sector)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

