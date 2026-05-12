#!/usr/bin/env python3
"""
API por parcela_id sobre GeoTIFF en un directorio; delega en geotiff_stats (misma evidencia/hash).
Útil para PRONT, scripts y alertas sin duplicar lectura raster.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from geotiff_stats import summarize_geotiff
from sigpac_features import federated_feature_bundle

Json = Dict[str, Any]


class SigpacValidator:
    """Valida un raster `{parcel_id}.tif` bajo data_dir y acumula trazas legibles para auditoría."""

    def __init__(self, data_dir: str | Path = "data/sigpac") -> None:
        self.data_dir = Path(data_dir)
        self.logs: List[str] = []

    def validate_parcel(self, parcel_id: str) -> Json:
        tif_path = self.data_dir / f"{parcel_id}.tif"
        r = summarize_geotiff(tif_path)
        if "error" in r:
            self.logs.append(f"Error parcela {parcel_id}: {r['error']}")
            return {"error": r["error"]}
        h = r.get("hash_sha256_band1", "")
        self.logs.append(f"Parcela {parcel_id} validada OK (hash {h[:16]}…)")
        out = dict(r)
        out["hash"] = r.get("hash_sha256_band1")
        out["area"] = r.get("area_m2_approx")
        out["features"] = federated_feature_bundle(r)
        return out

    def save_logs(self, log_path: str | Path = "logs/sigpac_validation.json") -> None:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(self.logs, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Validar GeoTIFF SIGPAC por ID de parcela (data_dir/ID.tif).")
    p.add_argument("parcel_id", help="Nombre sin extensión (ej. 12345 → 12345.tif)")
    p.add_argument("--data-dir", type=Path, default=Path("data/sigpac"))
    p.add_argument("--log", type=Path, default=Path("logs/sigpac_validation.json"))
    args = p.parse_args()
    v = SigpacValidator(data_dir=args.data_dir)
    stats = v.validate_parcel(args.parcel_id)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    v.save_logs(args.log)
    if "error" in stats:
        sys.exit(1)


if __name__ == "__main__":
    main()
