from __future__ import annotations

"""
Alias operativo para generar el manifiesto de integridad.

Salida:
- docs/lengua-comun/DASHBOARD/integridad.sha256.json
"""

import sys
from pathlib import Path

try:
    from scripts.seguridad.validar_integridad import main as _main
except ModuleNotFoundError:
    # Permite ejecución directa sin depender de paquetes.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validar_integridad import main as _main


if __name__ == "__main__":
    raise SystemExit(_main())

