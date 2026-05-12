#!/usr/bin/env python3
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false
"""NDMI worker for Sentinel-style imagery.

Input raster must include NIR and SWIR bands. Defaults map to Sentinel-2:
- NIR: band 8
- SWIR: band 11
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio


def calculate_ndmi(nir_band: Any, swir_band: Any) -> Any:
    denominator = nir_band.astype(np.float32) + swir_band.astype(np.float32)
    ndmi = (nir_band.astype(np.float32) - swir_band.astype(np.float32)) / np.where(
        denominator == 0,
        np.nan,
        denominator,
    )
    return np.nan_to_num(ndmi, nan=-9999.0)


def process_image(input_path: str, output_path: str, nir_idx: int = 8, swir_idx: int = 11) -> Path:
    in_path = Path(input_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(in_path) as src:
        nir = src.read(nir_idx)
        swir = src.read(swir_idx)
        ndmi = calculate_ndmi(nir, swir)

        profile = src.profile.copy()
        profile.update(dtype=rasterio.float32, count=1, nodata=-9999.0)

        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(ndmi.astype(rasterio.float32), 1)

    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute NDMI from multiband imagery")
    parser.add_argument("input", help="Input raster path")
    parser.add_argument("output", help="Output NDMI raster path")
    parser.add_argument("--nir", type=int, default=8, help="NIR band index")
    parser.add_argument("--swir", type=int, default=11, help="SWIR band index")
    args = parser.parse_args()

    result = process_image(args.input, args.output, nir_idx=args.nir, swir_idx=args.swir)
    print(f"[OK] NDMI written: {result}")
