from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from backend.integrations import sigpac_validator as sv
from backend.integrations.sigpac_remote_placeholder import SIGPACRemoteClientPlaceholder
from backend.integrations.sigpac_validator import SIGPACValidator


class TestSIGPACValidator:
    @pytest.fixture
    def validator(self) -> SIGPACValidator:
        return SIGPACValidator()

    def test_not_feature_returns_error(self, validator: SIGPACValidator) -> None:
        result = validator.validate_geojson({"type": "FeatureCollection"}, "parcel_001")
        assert result["status"] == "error"
        assert "Feature" in result["message"]

    def test_polygon_not_closed_returns_error(self, validator: SIGPACValidator) -> None:
        geojson_data = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]]},
        }
        result = validator.validate_geojson(geojson_data, "parcel_001")
        assert result["status"] == "error"
        assert "cerrado" in result["message"]

    def test_without_gdal_structural_ok_and_no_area(self, validator: SIGPACValidator) -> None:
        geojson_data = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
        }
        with patch.object(sv, "_OGR_AVAILABLE", False):
            result = validator.validate_geojson(geojson_data, "parcel_001")
        assert result["status"] == "valid"
        assert result.get("area_ha") is None
        assert "Sin GDAL" in (result.get("validation_note") or "")

    @pytest.mark.skipif(not sv._OGR_AVAILABLE, reason="Requiere GDAL/osgeo para área en EPSG:25830")
    def test_epsg25830_square_1ha_numeric_area_warning_logged(
        self, validator: SIGPACValidator, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING, logger="backend.integrations.sigpac_validator")
        geojson_data = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [100, 0], [100, 100], [0, 100], [0, 0]]],
            },
            "properties": {"area_ha": "not_a_number"},
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}},
        }
        result = validator.validate_geojson(geojson_data, "parcel_001")
        assert result["status"] == "valid"
        assert result.get("area_ha") is not None
        assert abs(float(result["area_ha"]) - 1.0) < 0.1
        assert "no numérico" in caplog.text
        assert "parcel_001" in caplog.text

    @pytest.mark.skipif(not sv._OGR_AVAILABLE, reason="Requiere GDAL/osgeo para reproyección 4326→25830")
    def test_reprojection_wgs84_extent_returns_valid_area(self, validator: SIGPACValidator) -> None:
        """BBox ~0,1°×0,1°: orden de magnitud >> 5 ha (el rango 0,05–5 ha solo aplica a polígonos mucho más pequeños)."""
        geojson_data = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[-6.0, 39.0], [-5.9, 39.0], [-5.9, 39.1], [-6.0, 39.1], [-6.0, 39.0]]
                ],
            },
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
        }
        result = validator.validate_geojson(geojson_data, "parcel_001")
        assert result["status"] == "valid"
        assert result.get("area_ha") is not None
        assert 1000.0 < float(result["area_ha"]) < 20_000.0

    def test_area_ogr_transform_failure_returns_invalid(self, validator: SIGPACValidator) -> None:
        """El flujo real usa geometry.Transform(tx), no CoordinateTransformation.TransformPoint."""
        geojson_data = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::4326"}},
        }
        mock_geom = MagicMock()
        mock_geom.IsValid.return_value = True
        mock_clone = MagicMock()
        mock_clone.Transform.side_effect = RuntimeError("OGR error")
        mock_geom.Clone.return_value = mock_clone
        fake_ogr = MagicMock()
        fake_ogr.CreateGeometryFromJson.return_value = mock_geom
        fake_osr = MagicMock()
        fake_osr.SpatialReference.return_value = MagicMock()
        fake_osr.CoordinateTransformation.return_value = MagicMock()
        with patch.object(sv, "_OGR_AVAILABLE", True):
            with patch.object(sv, "ogr", fake_ogr):
                with patch.object(sv, "osr", fake_osr):
                    result = validator.validate_geojson(geojson_data, "parcel_001")
        assert result["status"] == "invalid"
        assert "OGR error" in result["message"]

    def test_gaiachain_register_failure_still_valid(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        validator: SIGPACValidator,
    ) -> None:
        monkeypatch.setenv("CASTUO_SIGPAC_AUDIT_TOKEN_ID", "1")
        caplog.set_level(logging.ERROR, logger="backend.integrations.sigpac_validator")
        geojson_data = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
            "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}},
        }
        with patch("backend.api.services.gaiachain_service.register_event_in_chain") as mock_register:
            mock_register.side_effect = RuntimeError("GaiaChain error")
            with patch.object(sv, "_OGR_AVAILABLE", False):
                result = validator.validate_geojson(geojson_data, "parcel_001")
        assert result["status"] == "valid"
        assert "GaiaChain error" in caplog.text
        err_records = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert err_records
        assert err_records[-1].exc_info is not None


def test_sigpac_remote_placeholder_not_constructible() -> None:
    with pytest.raises(NotImplementedError) as exc_info:
        SIGPACRemoteClientPlaceholder()
    msg = str(exc_info.value)
    assert "descarga manual de GeoJSON" in msg
    assert "https://sigpac.mapa.gob.es/" in msg
    assert "SIGPACValidator" in msg
