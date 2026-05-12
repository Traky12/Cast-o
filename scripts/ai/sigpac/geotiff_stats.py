#!/usr/bin/env python3
"""
Estadísticas y hash de una banda raster (GeoTIFF u otro leíble por rasterio).
Complementario a PEI-001 (shapefile/recinto) y a `backend/integrations/sigpac_validator.py` (GeoJSON).
No sustituye la validación oficial SIGPAC ni la superposición parcela–capa.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Union

Json = Dict[str, Any]


def summarize_geotiff(path: Path) -> Json:
    """Devuelve estadísticas de la banda 1 y sha256 del buffer raw (puede ser pesado en rasters grandes)."""
    try:
        import numpy as np
        import rasterio
    except ImportError as e:
        return {"error": f"Dependencias opcionales: pip install -r scripts/ai/sigpac/requirements_sigpac.txt ({e})"}

    path = path.resolve()
    if not path.is_file():
        return {"error": f"Archivo no encontrado: {path}"}

    out: Json = {"path": str(path)}
    try:
        with rasterio.open(path) as src:
            data = src.read(1, masked=True)
            valid = data.compressed() if hasattr(data, "compressed") else data.ravel()
            arr = np.asarray(valid, dtype=np.float64)
            if arr.size == 0:
                return {**out, "error": "Raster sin datos válidos"}
            raw = data.filled().astype(np.float64).tobytes()
            tr = src.transform
            pixel_w, pixel_h = abs(tr[0]), abs(tr[4])
            h, w = data.shape
            area_m2 = float(w * h * pixel_w * pixel_h)
            out.update(
                {
                    "crs": str(src.crs) if src.crs else None,
                    "shape": [int(h), int(w)],
                    "dtype": str(data.dtype),
                    "mean": float(np.mean(arr)),
                    "std": float(np.std(arr)),
                    "min": float(np.min(arr)),
                    "max": float(np.max(arr)),
                    "area_m2_approx": area_m2,
                    "hash_sha256_band1": hashlib.sha256(raw).hexdigest(),
                }
            )
    except Exception as e:
        out["error"] = str(e)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Resumen GeoTIFF (band 1) + hash para trazabilidad técnica.")
    p.add_argument("tif", type=Path, help="Ruta al .tif / .tiff")
    p.add_argument("--json-log", type=Path, default=None, help="Append de una línea JSON al log de auditoría")
    args = p.parse_args()
    result = summarize_geotiff(args.tif)
    print(json.dumps(result, indent=2))
    if args.json_log and "error" not in result:
        args.json_log.parent.mkdir(parents=True, exist_ok=True)
        with args.json_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
