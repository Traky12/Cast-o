"""
Tests para el módulo Satélite EU: NDVI worker, Copernicus client, API router.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.satellite.ndvi_worker import (
    BandArrays,
    IndicesResult,
    calculate_evi,
    calculate_ndmi,
    calculate_ndvi,
    compute_stats,
    detect_anomalies,
    process_bands,
    simulate_parcela_indices,
)

# ── Suite: cálculo NDVI ───────────────────────────────────────────────────────

class TestNDVICalculations:

    def _bands(self, red_val: float = 0.08, nir_val: float = 0.45) -> tuple:
        red = np.full((10, 10), red_val, dtype=np.float32)
        nir = np.full((10, 10), nir_val, dtype=np.float32)
        return red, nir

    def test_ndvi_formula_correctness(self):
        red, nir = self._bands(0.1, 0.5)
        ndvi = calculate_ndvi(red, nir)
        expected = (0.5 - 0.1) / (0.5 + 0.1)
        assert abs(ndvi.mean() - expected) < 1e-4

    def test_ndvi_range(self):
        red = np.random.uniform(0, 1, (50, 50)).astype(np.float32)
        nir = np.random.uniform(0, 1, (50, 50)).astype(np.float32)
        ndvi = calculate_ndvi(red, nir)
        valid = ndvi[ndvi != -9999.0]
        assert valid.min() >= -1.0
        assert valid.max() <= 1.0

    def test_ndvi_zero_denominator(self):
        # red == nir → denominador 0 → debe devolver nodata, no dividir
        arr = np.ones((5, 5), dtype=np.float32) * 0.3
        ndvi = calculate_ndvi(arr, arr)
        assert np.all(ndvi == 0.0) or np.all(ndvi == -9999.0)  # ambas son aceptables

    def test_ndmi_range(self):
        nir  = np.random.uniform(0.1, 0.8, (30, 30)).astype(np.float32)
        swir = np.random.uniform(0.05, 0.3, (30, 30)).astype(np.float32)
        ndmi = calculate_ndmi(nir, swir)
        valid = ndmi[ndmi != -9999.0]
        assert valid.min() >= -1.0
        assert valid.max() <= 1.0

    def test_evi_clipped(self):
        red  = np.full((10, 10), 0.1, dtype=np.float32)
        nir  = np.full((10, 10), 0.5, dtype=np.float32)
        blue = np.full((10, 10), 0.05, dtype=np.float32)
        evi  = calculate_evi(red, nir, blue)
        assert evi.min() >= -1.0
        assert evi.max() <= 1.0

    def test_compute_stats_keys(self):
        arr   = np.array([0.3, 0.5, 0.6, 0.4, -9999.0], dtype=np.float32)
        stats = compute_stats(arr)
        assert "min" in stats and "max" in stats
        assert "mean" in stats and "std" in stats
        assert "valid_pct" in stats

    def test_compute_stats_excludes_nodata(self):
        arr   = np.array([0.5, 0.6, -9999.0, -9999.0], dtype=np.float32)
        stats = compute_stats(arr)
        assert stats["valid_pct"] == pytest.approx(50.0)
        assert stats["mean"] == pytest.approx(0.55, abs=1e-3)

    def test_compute_stats_all_nodata(self):
        arr   = np.full((5,), -9999.0, dtype=np.float32)
        stats = compute_stats(arr)
        assert stats["mean"] is None
        assert stats["valid_pct"] == 0.0


# ── Suite: process_bands ──────────────────────────────────────────────────────

class TestProcessBands:

    def _healthy_bands(self) -> BandArrays:
        size = 20
        red  = np.full((size, size), 0.06, dtype=np.float32)
        nir  = np.full((size, size), 0.55, dtype=np.float32)
        swir = np.full((size, size), 0.10, dtype=np.float32)
        blue = np.full((size, size), 0.03, dtype=np.float32)
        return BandArrays(red=red, nir=nir, swir=swir, blue=blue)

    def test_process_returns_result(self):
        result = process_bands(self._healthy_bands())
        assert isinstance(result, IndicesResult)
        assert result.ndvi is not None
        assert result.ndmi is not None
        assert result.evi  is not None

    def test_process_stats_populated(self):
        result = process_bands(self._healthy_bands())
        assert "ndvi" in result.stats
        assert result.stats["ndvi"]["mean"] is not None

    def test_no_anomaly_for_healthy_vegetation(self):
        result = process_bands(self._healthy_bands())
        assert result.anomalies == []

    def test_anomaly_detected_low_ndvi(self):
        size = 20
        red  = np.full((size, size), 0.45, dtype=np.float32)
        nir  = np.full((size, size), 0.15, dtype=np.float32)
        bands = BandArrays(red=red, nir=nir)
        result = process_bands(bands)
        assert len(result.anomalies) > 0
        tipos = [a["tipo"] for a in result.anomalies]
        assert "estres_severo" in tipos or "estres_moderado" in tipos

    def test_to_dict_structure(self):
        result = process_bands(self._healthy_bands())
        d = result.to_dict()
        assert "ndvi_stats" in d
        assert "anomalies" in d
        assert "pixel_count" in d
        assert "valid_pixels" in d


# ── Suite: anomaly detection ──────────────────────────────────────────────────

class TestAnomalyDetection:

    def _make_result(self, ndvi_mean: float, ndmi_mean: float | None = None) -> IndicesResult:
        arr = np.full((10, 10), ndvi_mean, dtype=np.float32)
        stats: dict = {"ndvi": compute_stats(arr)}
        if ndmi_mean is not None:
            ndmi_arr = np.full((10, 10), ndmi_mean, dtype=np.float32)
            stats["ndmi"] = compute_stats(ndmi_arr)
        return IndicesResult(ndvi=arr, stats=stats)

    def test_no_anomaly_good_ndvi(self):
        result = self._make_result(0.7)
        assert detect_anomalies(result) == []

    def test_critical_anomaly_very_low_ndvi(self):
        result = self._make_result(0.1)
        anomalies = detect_anomalies(result)
        assert any(a["severidad"] == "CRITICA" for a in anomalies)

    def test_moderate_anomaly_low_ndvi(self):
        result = self._make_result(0.3)
        anomalies = detect_anomalies(result)
        assert any(a["tipo"] == "estres_moderado" for a in anomalies)

    def test_water_stress_low_ndmi(self):
        result = self._make_result(0.6, ndmi_mean=-0.4)
        anomalies = detect_anomalies(result)
        assert any(a["tipo"] == "estres_hidrico" for a in anomalies)

    def test_anomaly_has_required_fields(self):
        result = self._make_result(0.1)
        for a in detect_anomalies(result):
            assert "tipo" in a
            assert "severidad" in a
            assert "descripcion" in a
            assert "accion" in a


# ── Suite: simulate_parcela_indices ──────────────────────────────────────────

class TestSimulateParcela:

    def test_deterministic(self):
        r1 = simulate_parcela_indices("PARC-001", "2026-04-01")
        r2 = simulate_parcela_indices("PARC-001", "2026-04-01")
        assert abs(r1.stats["ndvi"]["mean"] - r2.stats["ndvi"]["mean"]) < 1e-6

    def test_different_parcelas_different_results(self):
        r1 = simulate_parcela_indices("PARC-001", "2026-04-01")
        r2 = simulate_parcela_indices("PARC-999", "2026-04-01")
        # Extremely unlikely to be equal
        assert r1.stats["ndvi"]["mean"] != r2.stats["ndvi"]["mean"]

    def test_all_indices_calculated(self):
        result = simulate_parcela_indices("TEST", "2026-01-01")
        assert result.ndvi is not None
        assert result.ndmi is not None
        assert result.evi  is not None


# ── Suite: Copernicus client (sin credenciales → simulado) ─────────────────────

class TestCopernicusClientSim:

    def test_search_returns_simulated_items(self):
        import asyncio
        from services.satellite.copernicus_client import CopernicusClient
        client = CopernicusClient()
        items = asyncio.run(client.search_sentinel2(
            bbox=[-6.15, 38.44, -6.08, 38.50],
            start_date="2026-03-01",
            end_date="2026-04-01",
        ))
        assert len(items) > 0
        assert items[0]["type"] == "Feature"
        assert "B04" in items[0]["assets"]
        assert items[0]["properties"]["sim"] is True

    def test_health_not_configured(self):
        import asyncio
        from services.satellite.copernicus_client import CopernicusClient
        client = CopernicusClient()
        health = asyncio.run(client.health())
        assert health["status"] == "not_configured"


# ── Suite: satellite API endpoint ──────────────────────────────────────────────

class TestSatelliteAPI:

    @pytest.fixture(autouse=True)
    def _client(self, monkeypatch, tmp_path):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("JWT_SECRET_FILE", raising=False)
        monkeypatch.setenv("SATELLITE_RESULTS_PATH", str(tmp_path / "results"))
        monkeypatch.setenv("NDVI_DATA_PATH", str(tmp_path / "ndvi"))
        from main import app
        self.http = TestClient(app)

    def test_satellite_health(self):
        resp = self.http.get("/api/v1/satellite/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "copernicus" in data
        assert "timestamp" in data

    def test_ndvi_endpoint_dev_mode(self):
        resp = self.http.get("/api/v1/satellite/ndvi/PARC-TEST-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "ndvi_stats" in data
        assert data["simulado"] is True

    def test_analyze_endpoint_dev_mode(self):
        resp = self.http.post("/api/v1/satellite/analyze", json={
            "parcela_id": "PARC-E2E-001",
            "nombre":     "Dehesa Test",
            "cultivo":    "pasto_permanente",
            "lon_min":    -6.15,
            "lat_min":    38.44,
            "lon_max":    -6.08,
            "lat_max":    38.50,
            "registrar_blockchain": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["parcela_id"] == "PARC-E2E-001"
        assert "ndvi_stats" in data
        assert "anomalias" in data
        assert "generado_en" in data

    def test_anomalies_endpoint_dev_mode(self):
        resp = self.http.get("/api/v1/satellite/anomalies/PARC-ANOM-001")
        assert resp.status_code == 200
        data = resp.json()
        assert "anomalias" in data
        assert "n_anomalias" in data
        assert "alerta" in data

    def test_analyze_lote_id_too_short_returns_422(self):
        resp = self.http.post("/api/v1/satellite/analyze", json={
            "parcela_id": "AB",   # min_length=3
            "lon_min": -6.15, "lat_min": 38.44,
            "lon_max": -6.08, "lat_max": 38.50,
        })
        assert resp.status_code == 422
