from __future__ import annotations

import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CONFIG = _REPO_ROOT / "config" / "extremadura_climate.yaml"


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _validate_optimal_range_block(path: str, d: Dict[str, Any]) -> None:
    for k, v in d.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                if not _is_number(sv):
                    raise ValueError(f"{path}.{k}.{sk} debe ser numérico")
        elif not _is_number(v):
            raise ValueError(f"{path}.{k} debe ser numérico")


def _validate_parameter_block(pname: str, blk: Dict[str, Any]) -> None:
    for k, v in blk.items():
        if k == "optimal_range" and isinstance(v, dict):
            _validate_optimal_range_block(f"{pname}.optimal_range", v)
        elif isinstance(v, dict):
            continue
        elif not _is_number(v):
            raise ValueError(f"{pname}.{k} debe ser numérico")


class ExtremaduraClimateConfig:
    """Carga umbrales desde YAML; el ahorro hídrico exige medir antes de automatizar alertas."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._path = Path(config_path) if config_path else _DEFAULT_CONFIG
        self.config: Dict[str, Any] = self._load_config()
        self._validate_numeric_thresholds(self.config)

    def _load_config(self) -> Dict[str, Any]:
        if not self._path.is_file():
            raise FileNotFoundError(f"extremadura_climate.yaml no encontrado: {self._path}")
        with self._path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError("YAML climático debe ser un objeto raíz (mapping)")
        return data

    def _validate_numeric_thresholds(self, root: Dict[str, Any]) -> None:
        for pname in ("temperature", "humidity", "solar_radiation", "wind_speed", "precipitation", "et0"):
            blk = root.get(pname)
            if isinstance(blk, dict):
                _validate_parameter_block(pname, blk)

        cs = root.get("crop_specific")
        if isinstance(cs, dict):
            for crop, cblk in cs.items():
                if not isinstance(cblk, dict):
                    continue
                for pname, pblk in cblk.items():
                    if isinstance(pblk, dict):
                        _validate_parameter_block(f"crop_specific.{crop}.{pname}", pblk)

    def get_threshold(
        self, parameter: str, threshold_type: str
    ) -> Optional[Union[float, Dict[str, Any]]]:
        block = self.config.get(parameter)
        if not isinstance(block, dict):
            return None
        return block.get(threshold_type)

    def _merge_crop_thresholds(
        self, parameter: str, crop_type: Optional[str]
    ) -> Dict[str, Any]:
        base = self.config.get(parameter, {})
        if not isinstance(base, dict):
            return {}
        merged: Dict[str, Any] = deepcopy(base)
        cs_root = self.config.get("crop_specific")
        if not crop_type or not isinstance(cs_root, dict):
            return merged
        crop_block = cs_root.get(crop_type)
        if not isinstance(crop_block, dict):
            return merged
        override = crop_block.get(parameter)
        if isinstance(override, dict):
            merged.update(override)
        return merged

    def check_violation(
        self, parameter: str, value: float, crop_type: Optional[str] = None
    ) -> Dict[str, Any]:
        thresholds = self._merge_crop_thresholds(parameter, crop_type)
        if not isinstance(thresholds, dict) or not thresholds:
            return {
                "status": "unknown",
                "message": f"Parámetro desconocido o vacío: {parameter}",
                "normative": [],
                "crop_type": crop_type,
            }

        result: Dict[str, Any] = {
            "status": "normal",
            "thresholds": thresholds,
            "normative": [],
            "crop_type": crop_type,
        }

        try:
            if parameter == "temperature":
                hw = float(thresholds.get("heatwave", 42))
                fr = float(thresholds.get("frost", 0))
                if value >= hw:
                    result.update(
                        {
                            "status": "critical",
                            "message": f"Ola de calor: {value}°C >= {hw}°C",
                            "severity": "high",
                            "normative": ["RD 169/2021 - Anexo IV", "Ley 3/2020"],
                        }
                    )
                elif value <= fr:
                    result.update(
                        {
                            "status": "critical",
                            "message": f"Helada: {value}°C <= {fr}°C",
                            "severity": "high",
                            "normative": ["UNE 50510 - §5.3", "RD 169/2021 - Anexo III"],
                        }
                    )

            elif parameter == "humidity":
                low = float(thresholds.get("low", 20))
                high = float(thresholds.get("high", 85))
                if value <= low:
                    result.update(
                        {
                            "status": "warning",
                            "message": f"Baja humedad: {value}% <= {low}%",
                            "severity": "medium",
                            "normative": ["UNE 50510 - §6.2", "RD 169/2021 - Anexo V"],
                        }
                    )
                elif value >= high:
                    result.update(
                        {
                            "status": "warning",
                            "message": f"Alta humedad: {value}% >= {high}%",
                            "severity": "medium",
                            "normative": ["UNE 50510 - §6.3"],
                        }
                    )

            elif parameter == "et0":
                high = float(thresholds.get("high", 8))
                if value >= high:
                    result.update(
                        {
                            "status": "warning",
                            "message": f"ET0 alta: {value} mm/día >= {high}",
                            "severity": "medium",
                            "normative": ["FAO-56", "UNE 50510"],
                        }
                    )
        except (TypeError, ValueError) as exc:
            logger.warning("Umbral inválido para %s (cultivo=%s): %s", parameter, crop_type, exc)
            return {
                "status": "error",
                "message": str(exc),
                "parameter": parameter,
                "crop_type": crop_type,
                "normative": [],
            }

        return result
