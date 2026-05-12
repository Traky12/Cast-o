#!/usr/bin/env python3
"""
Script de demo para Taller 1: mintado de una parcela ForestOwnershipToken.
Datos fijos para demostración en vivo; configurar FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY.
"""
from __future__ import annotations

import os
import sys
import subprocess

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MINT_SCRIPT = os.path.join(_SCRIPT_DIR, "mint_forest_property.py")

# Parcela de demostración (Dehesa La Encina)
DEMO_OWNER = os.getenv("DEMO_OWNER", "0x0000000000000000000000000000000000000001")
DEMO_PARCELA = "XT-DEMO-001"
DEMO_COORDINATES = "39.4769°N, 6.3706°W"
DEMO_AREA_M2 = 10000
DEMO_SPECIES = "Quercus ilex, Pinus pinea"
DEMO_CARBON = 5000
DEMO_IPFS = "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco"


def main() -> int:
    if not os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS") or not os.getenv("PRIVATE_KEY"):
        print("Configurar FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY (o JUNTA_PRIVATE_KEY).", file=sys.stderr)
        return 1
    print("Mintando parcela de demo:", DEMO_PARCELA, "->", DEMO_OWNER)
    cmd = [
        sys.executable,
        MINT_SCRIPT,
        DEMO_OWNER,
        DEMO_PARCELA,
        DEMO_COORDINATES,
        str(DEMO_AREA_M2),
        DEMO_SPECIES,
        str(DEMO_CARBON),
        "false",
        DEMO_IPFS,
        "-c", "PEFC", "FSC",
    ]
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(_SCRIPT_DIR)))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
