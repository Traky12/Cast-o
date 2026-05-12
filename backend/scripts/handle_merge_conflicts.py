#!/usr/bin/env python3
# backend/scripts/handle_merge_conflicts.py — Detección y resolución de conflictos de merge

from __future__ import annotations

import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def check_for_conflicts() -> bool:
    """Comprueba si hay conflictos de merge sin resolver."""
    try:
        r = subprocess.run(["git", "diff", "--check"], capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except Exception as e:
        logger.error("Error al verificar conflictos: %s", e)
        return False


def resolve_conflicts_automatically() -> bool:
    """Intenta resolver conflictos quedándose con la versión local (antes de =======)."""
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        conflict_files = [f.strip() for f in (r.stdout or "").strip().split("\n") if f.strip()]
        if not conflict_files:
            return True
        for path in conflict_files:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                logger.warning("No se pudo leer %s: %s", path, e)
                continue
            if "<<<<<<<" not in content or "=======" not in content or ">>>>>>>" not in content:
                continue
            parts = content.split("=======", 1)
            if len(parts) != 2:
                continue
            local_part = parts[0].split("<<<<<<<", 1)[-1].strip()
            rest = parts[1].split(">>>>>>>", 1)[-1].strip() if ">>>>>>>" in parts[1] else ""
            resolved = local_part + "\n" + rest
            with open(path, "w", encoding="utf-8") as f:
                f.write(resolved)
            subprocess.run(["git", "add", path], check=False, capture_output=True)
        return check_for_conflicts()
    except Exception as e:
        logger.error("Error al resolver conflictos: %s", e)
        return False


def main() -> int:
    if check_for_conflicts():
        print("No hay conflictos de merge.")
        return 0
    print("Conflictos de merge detectados.")
    if resolve_conflicts_automatically():
        print("Conflictos resueltos automáticamente (versión local).")
        return 0
    print("No se pudieron resolver automáticamente. Resuélvelos manualmente.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
