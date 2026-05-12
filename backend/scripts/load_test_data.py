#!/usr/bin/env python3
"""
Carga datos de prueba para demo en vivo y vídeo tutorial ForestOwnershipToken.
Opciones: --demo (parcela XT-DEMO-001 estándar), --mobile (datos para demo desde móvil).
No modifica blockchain; prepara metadatos y opcionalmente llama a mint_certified_forest_property.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

DEMO_PARCELA_ID = "XT-DEMO-001"
DEMO_COORDINATES = "39.4769°N, 6.3706°W"
DEMO_AREA = 10000
DEMO_SPECIES = "Quercus ilex, Pinus pinea"
DEMO_CARBON = 5000
DEMO_CERTIFICATIONS = ["PEFC", "FSC", "Red Natura 2000"]
DEMO_OWNER_PC = "0xTecnicoDemo"
DEMO_OWNER_MOBILE = "0xTecnicoMovil"
SUBSIDY_ESTIMATE_EUR = 650


def load_demo_metadata(mobile: bool = False) -> dict:
    """Genera metadatos de prueba para la parcela de demo."""
    owner = DEMO_OWNER_MOBILE if mobile else DEMO_OWNER_PC
    return {
        "parcela_id": DEMO_PARCELA_ID,
        "owner": owner,
        "coordinates": DEMO_COORDINATES,
        "area_m2": DEMO_AREA,
        "species": DEMO_SPECIES,
        "carbon_sequestered_kg": DEMO_CARBON,
        "certifications": DEMO_CERTIFICATIONS,
        "subsidy_eur_per_ha_year": SUBSIDY_ESTIMATE_EUR,
        "note": "Datos de prueba para demo en vivo / vídeo tutorial. Para mint real usar mint_certified_forest_property.py",
    }


def mint_demo_if_configured(mobile: bool) -> dict | None:
    """Si hay PRIVATE_KEY y FOREST_OWNERSHIP_TOKEN_ADDRESS, ejecuta mint de la parcela de demo."""
    if not os.getenv("PRIVATE_KEY") and not os.getenv("JUNTA_PRIVATE_KEY"):
        return None
    if not os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS"):
        return None
    import subprocess
    owner = DEMO_OWNER_MOBILE if mobile else DEMO_OWNER_PC
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mint_script = os.path.join(script_dir, "mint_certified_forest_property.py")
    if not os.path.isfile(mint_script):
        return None
    try:
        out = subprocess.run(
            [
                sys.executable,
                mint_script,
                owner,
                DEMO_PARCELA_ID,
                "--coordinates", DEMO_COORDINATES,
                "--area", str(DEMO_AREA),
                "--species", DEMO_SPECIES,
                "--carbon", str(DEMO_CARBON),
                "--certifications", *DEMO_CERTIFICATIONS,
                "--no-sigpac",
            ],
            capture_output=True,
            text=True,
            cwd=script_dir,
            timeout=120,
            env={**os.environ},
        )
        if out.returncode != 0:
            print(out.stderr or out.stdout, file=sys.stderr)
            return None
        raw = out.stdout
        start = raw.find("{")
        if start == -1:
            return {"tx_hash": "", "token_id": 0}
        depth = 0
        end = start
        for i, c in enumerate(raw[start:], start=start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if depth == 0:
            return json.loads(raw[start : end + 1])
        return {"tx_hash": "see stdout", "token_id": 0}
    except Exception as e:
        print(f"Advertencia: mint no ejecutado ({e})", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Carga datos de prueba para demo ForestOwnershipToken (demo en vivo / vídeo)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Usar parcela de demo estándar XT-DEMO-001 (1 ha, PEFC/FSC/Red Natura 2000)",
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Preparar datos para demo desde móvil (owner 0xTecnicoMovil)",
    )
    parser.add_argument(
        "--mint",
        action="store_true",
        help="Intentar mint real en GaiaChain si PRIVATE_KEY y contrato están configurados",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Solo imprimir metadatos de prueba en JSON",
    )
    args = parser.parse_args()

    mobile = args.mobile
    if not args.demo and not args.mobile:
        parser.print_help()
        print("\nIndica --demo y/o --mobile para cargar datos de prueba.", file=sys.stderr)
        return 0

    meta = load_demo_metadata(mobile=mobile)
    if args.json:
        print(json.dumps(meta, indent=2))
        return 0

    print("Datos de prueba cargados:")
    print(f"  Parcela: {meta['parcela_id']}")
    print(f"  Propietario: {meta['owner']}")
    print(f"  Área: {meta['area_m2']} m² (1 ha)")
    print(f"  Certificaciones: {', '.join(meta['certifications'])}")
    print(f"  Subvención estimada: €{meta['subsidy_eur_per_ha_year']}/ha/año")
    print(f"  CO₂: {meta['carbon_sequestered_kg']} kg/año (5 t/ha)")

    if args.mint:
        result = mint_demo_if_configured(mobile)
        if result:
            print(f"\nMint ejecutado: token_id={result.get('token_id')}, tx={result.get('tx_hash', '')[:18]}...")
        else:
            print("\nMint no ejecutado (configura PRIVATE_KEY y FOREST_OWNERSHIP_TOKEN_ADDRESS para mint real).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
