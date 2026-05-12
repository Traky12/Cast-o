#!/usr/bin/env python3
"""NDVI worker for Sentinel-style imagery.

Input raster must include red and NIR bands. Defaults map to Sentinel-2:
- Red: band 4
- NIR: band 8
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio


def calculate_ndvi(red_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    denominator = nir_band.astype(np.float32) + red_band.astype(np.float32)
    ndvi = (nir_band.astype(np.float32) - red_band.astype(np.float32)) / np.where(
        denominator == 0,
        np.nan,
        denominator,
    )
    return np.nan_to_num(ndvi, nan=-9999.0)


def process_image(input_path: str, output_path: str, red_idx: int = 4, nir_idx: int = 8) -> Path:
    in_path = Path(input_path)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(in_path) as src:
        red = src.read(red_idx)
        nir = src.read(nir_idx)
        ndvi = calculate_ndvi(red, nir)

        profile = src.profile.copy()
        profile.update(dtype=rasterio.float32, count=1, nodata=-9999.0)

        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(ndvi.astype(rasterio.float32), 1)

    return out_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute NDVI from multiband imagery")
    parser.add_argument("input", help="Input raster path")
    parser.add_argument("output", help="Output NDVI raster path")
    parser.add_argument("--red", type=int, default=4, help="Red band index")
    parser.add_argument("--nir", type=int, default=8, help="NIR band index")
    args = parser.parse_args()

    result = process_image(args.input, args.output, red_idx=args.red, nir_idx=args.nir)
    print(f"[OK] NDVI written: {result}")
