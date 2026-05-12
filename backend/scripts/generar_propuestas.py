#!/usr/bin/env python3
"""Wrapper: genera propuestas PDF para todas las cooperativas. Ver generar_propuestas_3_coops.py."""
from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    gen_script = script_dir / "generar_propuestas_3_coops.py"
    if not gen_script.is_file():
        print("generar_propuestas_3_coops.py no encontrado", file=sys.stderr)
        sys.exit(1)
    # Ejecutar el script de las 3 coops (--all-coops es opcional, siempre genera las 3)
    import subprocess
    rc = subprocess.run([sys.executable, str(gen_script)] + sys.argv[1:], cwd=script_dir.parent)
    sys.exit(rc.returncode)
