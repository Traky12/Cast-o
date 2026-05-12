#!/usr/bin/env python3
"""
Wrapper para cargar datos de demo ForestOwnershipToken.
Equivalente a: python load_test_data.py --demo [--mobile]
Uso: python load_demo_data.py --mobile  → datos para demo desde móvil (0xTecnicoMovil).
     python load_demo_data.py            → datos para demo en PC (0xTecnicoDemo).
"""
from __future__ import annotations

import os
import sys

# Ejecutar load_test_data.py en el mismo directorio
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_load_test = os.path.join(_SCRIPT_DIR, "load_test_data.py")

if __name__ == "__main__":
    argv = [sys.executable, _load_test, "--demo"]
    if "--mobile" in sys.argv or "-m" in sys.argv:
        argv.append("--mobile")
    if "--mint" in sys.argv:
        argv.append("--mint")
    if "--json" in sys.argv:
        argv.append("--json")
    os.execv(sys.executable, argv)
