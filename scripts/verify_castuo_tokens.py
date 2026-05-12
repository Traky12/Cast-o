#!/usr/bin/env python3
"""Comprueba directorio de tokens y ficheros esperados (pendrive o volumen Docker)."""

from __future__ import annotations

import os
import sys


def _required_names() -> list[str]:
    raw = (os.environ.get("CASTUO_TOKEN_REQUIRED_FILES") or "").strip()
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return ["admin_general.token", "farmer.key", "technician.key"]


def verify_tokens() -> tuple[bool, str]:
    tokens_path = os.getenv("CASTUO_TOKENS_PATH", "/mnt/castuo_secure/tokens").rstrip("/")
    if not os.path.isdir(tokens_path):
        return False, f"Directorio no encontrado: {tokens_path}"

    required_files = _required_names()
    missing = [name for name in required_files if not os.path.isfile(os.path.join(tokens_path, name))]
    if missing:
        return False, f"Faltan tokens: {', '.join(missing)}"

    return True, "Verificación exitosa"


def main() -> int:
    success, message = verify_tokens()
    print(message)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
