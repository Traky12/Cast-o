#!/usr/bin/env python3
"""SHA-256 del ZIP expediente CASTUO360 (ancla legal / GaiaChain)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: python hash_expediente_zip.py <archivo.zip>", file=sys.stderr)
        return 2
    p = Path(sys.argv[1])
    if not p.is_file():
        print(f"No existe: {p}", file=sys.stderr)
        return 1
    digest = sha256_file(p)
    print(f"SHA256_EXPEDIENTE={digest}")
    print(f"0x{digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
