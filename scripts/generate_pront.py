#!/usr/bin/env python3
"""Alias de `scripts/docs/pront_new_skeleton.py` para generar PRONT-CASTUO-<M>-v<V>-AAAA.md."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    target = Path(__file__).resolve().parent / "docs" / "pront_new_skeleton.py"
    if not target.is_file():
        raise SystemExit(f"No se encuentra {target}")
    r = subprocess.run([sys.executable, str(target)] + sys.argv[1:])
    raise SystemExit(r.returncode)


if __name__ == "__main__":
    main()
