"""SigpacValidator: delegación a geotiff_stats + alias hash/area."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_ROOT / "scripts" / "ai" / "sigpac"))
import validator as sigpac_validator  # noqa: E402


def test_validate_parcel_ok(tmp_path: Path) -> None:
    rasterio = pytest.importorskip("rasterio")
    import numpy as np

    tif = tmp_path / "p1.tif"
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

    v = sigpac_validator.SigpacValidator(data_dir=tmp_path)
    stats = v.validate_parcel("p1")
    assert "error" not in stats
    assert stats["mean"] == pytest.approx(1.0)
    assert stats["hash"] == stats["hash_sha256_band1"]
    assert stats["area"] == stats["area_m2_approx"]
    assert "features" in stats
    assert stats["features"]["ndvi"] is None
    assert stats["features"]["vector_dim"] == 8


def test_validate_missing_parcel(tmp_path: Path) -> None:
    v = sigpac_validator.SigpacValidator(data_dir=tmp_path)
    stats = v.validate_parcel("missing")
    assert "error" in stats
