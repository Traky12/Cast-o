#!/usr/bin/env python3
"""
Puente documentado hacia validación SIGPAC **local** (GeoJSON / GDAL).
No implementa API REST oficial SIGPAC: el visor institucional no expone un endpoint único
documentado en este repositorio; usar capas locales y `SIGPACValidator`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validar Feature GeoJSON local con SIGPACValidator")
    parser.add_argument("geojson_path", type=Path, help="Ruta a un archivo GeoJSON Feature")
    parser.add_argument(
        "--parcel-id",
        default="LOCAL-DEMO",
        help="Identificador de referencia (no sustituye expediente oficial)",
    )
    args = parser.parse_args()

    raw = args.geojson_path.read_text(encoding="utf-8")
    data = json.loads(raw)

    from backend.integrations.sigpac_validator import SIGPACValidator

    v = SIGPACValidator()
    result = v.validate_geojson(data, args.parcel_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
