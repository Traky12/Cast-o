from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.ctaex.climate_config import ExtremaduraClimateConfig


class TestExtremaduraClimateConfig:
    def test_init_raises_on_invalid_numeric_yaml(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.yaml"
        bad.write_text(
            yaml.dump(
                {
                    "temperature": {"heatwave": "not_a_number", "frost": 0},
                    "humidity": {"low": 20, "high": 85},
                    "solar_radiation": {"high": 1100},
                    "wind_speed": {"moderate": 5, "high": 10, "extreme": 15},
                    "precipitation": {"drought": 5, "heavy_rain": 30},
                    "et0": {"high": 8},
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="numérico"):
            ExtremaduraClimateConfig(config_path=bad)

    def test_init_raises_on_broken_yaml_syntax(self, tmp_path: Path) -> None:
        broken = tmp_path / "broken.yaml"
        broken.write_text("{ no es yaml válido", encoding="utf-8")
        with pytest.raises(yaml.YAMLError):
            ExtremaduraClimateConfig(config_path=broken)

    def test_crop_specific_et0_tomate_raf_uses_high_not_optimal(self) -> None:
        config = ExtremaduraClimateConfig()
        result = config.check_violation("et0", 8.0, crop_type="tomate_raf")
        assert result["status"] == "warning"
        assert "7" in result["message"]
        assert "FAO-56" in result["normative"][0] or "UNE 50510" in result["normative"][0]

    def test_fallback_to_global_thresholds(self) -> None:
        config = ExtremaduraClimateConfig()
        result = config.check_violation("temperature", 43.0, crop_type="unknown_crop")
        assert result["status"] == "critical"
        assert "42" in result["message"]

    def test_et0_cereales_crop_specific_high(self) -> None:
        config = ExtremaduraClimateConfig()
        result = config.check_violation("et0", 8.0, crop_type="cereales")
        assert result["status"] == "warning"
        assert "7" in result["message"]
        assert any("UNE 50510" in x for x in result["normative"])
