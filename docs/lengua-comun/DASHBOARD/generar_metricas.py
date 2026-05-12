from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """
    Wrapper para ejecutar el generador offline-first real:
    - scripts/dashboard/generar_metricas.py

    Motivo: facilitar a facilitadores que trabajan solo en docs/.
    """
    root = Path(__file__).resolve().parents[3]
    impl = root / "scripts" / "dashboard" / "generar_metricas.py"
    if not impl.exists():
        print("ERROR: falta scripts/dashboard/generar_metricas.py")
        return 2
    return subprocess.call([sys.executable, str(impl)])


if __name__ == "__main__":
    raise SystemExit(main())

