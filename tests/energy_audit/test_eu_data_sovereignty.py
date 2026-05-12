"""Soberania UE: catalogo satelital y endpoints Copernicus."""

from __future__ import annotations

import os

import pytest

from backend.energy_audit.eu_data_sovereignty import (
    assert_eu_copernicus_host,
    build_copernicus_product_download_url,
    copernicus_dhus_base,
    eu_data_sovereignty_strict,
    filter_band_catalog_for_eu,
)


def test_filter_removes_landsat_when_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASTUO_EU_DATA_SOVEREIGNTY", "1")
    bands = {
        "Sentinel-2": {"B04": "red"},
        "Landsat-8": {"B4": "red"},
    }
    out = filter_band_catalog_for_eu(bands)
    assert "Sentinel-2" in out
    assert "Landsat-8" not in out


def test_filter_keeps_landsat_when_loose(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CASTUO_EU_DATA_SOVEREIGNTY", "0")
    bands = {"Sentinel-2": {"B04": "red"}, "Landsat-8": {"B4": "red"}}
    out = filter_band_catalog_for_eu(bands)
    assert "Landsat-8" in out


def test_assert_host_rejects_non_copernicus() -> None:
    with pytest.raises(ValueError):
        assert_eu_copernicus_host("https://evil.example.com/dhus/")


def test_build_url_default_scihub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COPERNICUS_DHUS_BASE", raising=False)
    url = build_copernicus_product_download_url("S2A_MSIL2A_20200101")
    assert "scihub.copernicus.eu" in url
    assert "S2A_MSIL2A_20200101" in url


def test_custom_dhus_must_remain_copernicus_eu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COPERNICUS_DHUS_BASE", "https://catalogue.dataspace.copernicus.eu")
    base = copernicus_dhus_base()
    assert "dataspace.copernicus.eu" in base
    url = build_copernicus_product_download_url("X")
    assert "dataspace.copernicus.eu" in url


def test_strict_reads_env_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CASTUO_EU_DATA_SOVEREIGNTY", raising=False)
    assert eu_data_sovereignty_strict() is True
