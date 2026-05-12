"""Pruebas: raster inexistente; con rasterio, GeoTIFF mínimo."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "sigpac"))
import geotiff_stats  # noqa: E402


def test_missing_file(tmp_path: Path) -> None:
    r = geotiff_stats.summarize_geotiff(tmp_path / "no.tif")
    assert "error" in r


def test_summarize_small_raster(tmp_path: Path) -> None:
    rasterio = pytest.importorskip("rasterio")
    import numpy as np

    tif = tmp_path / "one.tif"
    data = np.ones((4, 4), dtype=np.float32)
    with rasterio.open(
        tif,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:25830",
        transform=rasterio.transform.from_origin(0, 4, 1, 1),
    ) as dst:
        dst.write(data, 1)

    r = geotiff_stats.summarize_geotiff(tif)
    assert "error" not in r
    assert r["mean"] == pytest.approx(1.0)
    assert "hash_sha256_band1" in r
    assert len(r["hash_sha256_band1"]) == 64
