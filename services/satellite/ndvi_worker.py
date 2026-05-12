"""
CASTÚO-SYSTEM™ v3.1 — NDVI/NDMI/EVI Worker
Calcula índices de vegetación a partir de bandas Sentinel-2 L2A.

Índices implementados:
  NDVI  = (NIR - Red) / (NIR + Red)             — salud vegetación
  NDMI  = (NIR - SWIR) / (NIR + SWIR)           — contenido de humedad
  EVI   = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)  — vegetación densa

Dependencias opcionales:
  rasterio  — lectura/escritura GeoTIFF (si no disponible, trabaja con arrays NumPy)
  numpy     — cálculo de índices

Cuando rasterio no está disponible, los métodos file_* retornan None con warning.
Los métodos array_* funcionan siempre (solo requieren numpy).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("castuo.satellite.ndvi")

try:
    import rasterio
    from rasterio.transform import from_bounds
    _RASTERIO_AVAILABLE = True
except ImportError:
    _RASTERIO_AVAILABLE = False
    logger.info("[ndvi_worker] rasterio no disponible — modo array-only")

_NODATA = -9999.0
_OUTPUT_DIR = os.getenv("NDVI_DATA_PATH", "/data/satellite/ndvi")


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class BandArrays:
    """Arrays NumPy normalizados de reflectancia (0–1) de bandas Sentinel-2."""
    red:   np.ndarray          # B04
    nir:   np.ndarray          # B08
    swir:  Optional[np.ndarray] = None   # B11
    blue:  Optional[np.ndarray] = None   # B02


@dataclass
class IndicesResult:
    """Resultado del cálculo de índices de vegetación."""
    ndvi:  np.ndarray
    ndmi:  Optional[np.ndarray] = None
    evi:   Optional[np.ndarray] = None
    stats: dict[str, Any] = field(default_factory=dict)
    anomalies: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ndvi_stats":  self.stats.get("ndvi", {}),
            "ndmi_stats":  self.stats.get("ndmi"),
            "evi_stats":   self.stats.get("evi"),
            "anomalies":   self.anomalies,
            "pixel_count": int(self.ndvi.size),
            "valid_pixels": int(np.sum(self.ndvi != _NODATA)),
        }


# ── Cálculos principales ─────────────────────────────────────────────────────

def calculate_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI = (NIR - Red) / (NIR + Red). Rango: -1 a 1."""
    red  = red.astype(np.float32)
    nir  = nir.astype(np.float32)
    denom = nir + red
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = np.where(denom != 0, (nir - red) / denom, _NODATA)
    return ndvi.astype(np.float32)


def calculate_ndmi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """NDMI = (NIR - SWIR) / (NIR + SWIR). Rango: -1 a 1."""
    nir  = nir.astype(np.float32)
    swir = swir.astype(np.float32)
    denom = nir + swir
    with np.errstate(divide="ignore", invalid="ignore"):
        ndmi = np.where(denom != 0, (nir - swir) / denom, _NODATA)
    return ndmi.astype(np.float32)


def calculate_evi(red: np.ndarray, nir: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """EVI = 2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)."""
    red  = red.astype(np.float32)
    nir  = nir.astype(np.float32)
    blue = blue.astype(np.float32)
    denom = nir + 6 * red - 7.5 * blue + 1
    with np.errstate(divide="ignore", invalid="ignore"):
        evi = np.where(denom != 0, 2.5 * (nir - red) / denom, _NODATA)
    return np.clip(evi, -1.0, 1.0).astype(np.float32)


def compute_stats(arr: np.ndarray, name: str = "") -> dict[str, float]:
    """Estadísticas básicas sobre un array de índice, excluyendo nodata."""
    valid = arr[arr != _NODATA]
    if valid.size == 0:
        return {"min": None, "max": None, "mean": None, "std": None, "valid_pct": 0.0}
    return {
        "min":       float(np.nanmin(valid)),
        "max":       float(np.nanmax(valid)),
        "mean":      float(np.nanmean(valid)),
        "std":       float(np.nanstd(valid)),
        "p10":       float(np.nanpercentile(valid, 10)),
        "p25":       float(np.nanpercentile(valid, 25)),
        "p75":       float(np.nanpercentile(valid, 75)),
        "p90":       float(np.nanpercentile(valid, 90)),
        "valid_pct": float(valid.size / arr.size * 100),
    }


def detect_anomalies(result: IndicesResult) -> list[dict[str, Any]]:
    """
    Detecta anomalías agronómicas basadas en umbrales de índices.

    Umbrales (basados en literatura agrícola europea):
      NDVI < 0.2  → estrés severo / suelo desnudo
      NDVI < 0.4  → vegetación escasa / estrés moderado
      NDMI < -0.2 → estrés hídrico
      EVI  < 0.15 → vegetación muy baja (en zonas con vegetación esperada)
    """
    anomalies: list[dict[str, Any]] = []
    ndvi_stats = result.stats.get("ndvi", {})
    ndmi_stats = result.stats.get("ndmi") or {}

    mean_ndvi = ndvi_stats.get("mean")
    if mean_ndvi is not None:
        if mean_ndvi < 0.2:
            anomalies.append({
                "tipo": "estres_severo",
                "indice": "NDVI",
                "valor": round(mean_ndvi, 4),
                "umbral": 0.2,
                "severidad": "CRITICA",
                "descripcion": "NDVI muy bajo — posible suelo desnudo, cosecha reciente o estrés severo",
                "accion": "Inspección inmediata en campo requerida",
            })
        elif mean_ndvi < 0.4:
            anomalies.append({
                "tipo": "estres_moderado",
                "indice": "NDVI",
                "valor": round(mean_ndvi, 4),
                "umbral": 0.4,
                "severidad": "MODERADA",
                "descripcion": "NDVI bajo — vegetación escasa o estrés moderado",
                "accion": "Revisar riego y estado nutricional del cultivo",
            })

    mean_ndmi = ndmi_stats.get("mean")
    if mean_ndmi is not None and mean_ndmi < -0.2:
        anomalies.append({
            "tipo": "estres_hidrico",
            "indice": "NDMI",
            "valor": round(mean_ndmi, 4),
            "umbral": -0.2,
            "severidad": "MODERADA",
            "descripcion": "NDMI bajo — posible estrés hídrico en el cultivo",
            "accion": "Incrementar frecuencia de riego o revisar sensores de humedad",
        })

    return anomalies


# ── API de alto nivel ────────────────────────────────────────────────────────

def process_bands(bands: BandArrays) -> IndicesResult:
    """
    Procesa arrays de bandas y devuelve todos los índices calculados.
    Punto de entrada principal para el worker.
    """
    ndvi = calculate_ndvi(bands.red, bands.nir)
    stats = {"ndvi": compute_stats(ndvi, "NDVI")}

    ndmi = None
    if bands.swir is not None:
        ndmi = calculate_ndmi(bands.nir, bands.swir)
        stats["ndmi"] = compute_stats(ndmi, "NDMI")

    evi = None
    if bands.blue is not None:
        evi = calculate_evi(bands.red, bands.nir, bands.blue)
        stats["evi"] = compute_stats(evi, "EVI")

    result = IndicesResult(ndvi=ndvi, ndmi=ndmi, evi=evi, stats=stats)
    result.anomalies = detect_anomalies(result)

    logger.info(
        "[ndvi_worker] Procesado: NDVI=%.3f±%.3f anomalias=%d",
        stats["ndvi"].get("mean", 0),
        stats["ndvi"].get("std", 0),
        len(result.anomalies),
    )
    return result


def process_image_file(input_path: str, output_path: str | None = None) -> Optional[IndicesResult]:
    """
    Procesa un GeoTIFF multi-banda Sentinel-2 L2A.
    Bandas esperadas: 1=Blue(B02), 2=Green(B03), 3=Red(B04), ..., 8=NIR(B08), 11=SWIR(B11)
    """
    if not _RASTERIO_AVAILABLE:
        logger.warning("[ndvi_worker] rasterio no disponible — no se puede procesar ficheros TIFF")
        return None

    try:
        with rasterio.open(input_path) as src:
            # Sentinel-2 L2A: banda 4 = Red (B04), banda 8 = NIR (B08)
            # Normalizar de reflectancia (0–10000) a (0–1)
            red  = src.read(4).astype(np.float32) / 10000.0
            nir  = src.read(8).astype(np.float32) / 10000.0
            swir = None
            blue = None
            if src.count >= 11:
                swir = src.read(11).astype(np.float32) / 10000.0
            if src.count >= 2:
                blue = src.read(2).astype(np.float32) / 10000.0

            bands  = BandArrays(red=red, nir=nir, swir=swir, blue=blue)
            result = process_bands(bands)

            if output_path:
                _write_ndvi_tiff(result.ndvi, src.profile, output_path)

            return result

    except Exception as exc:
        logger.error("[ndvi_worker] Error procesando %s: %s", input_path, exc)
        return None


def _write_ndvi_tiff(ndvi: np.ndarray, profile: Any, output_path: str) -> None:
    """Escribe un GeoTIFF con el resultado NDVI."""
    profile = profile.copy()
    profile.update(dtype=rasterio.float32, count=1, nodata=_NODATA)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(ndvi, 1)
    logger.info("[ndvi_worker] NDVI GeoTIFF guardado: %s", output_path)


def simulate_parcela_indices(parcela_id: str, fecha: str) -> IndicesResult:
    """
    Genera índices simulados para una parcela cuando no hay datos reales.
    Determinista: mismo parcela_id + fecha → mismo resultado.
    """
    import hashlib
    seed = int(hashlib.sha256(f"{parcela_id}{fecha}".encode()).hexdigest()[:8], 16)
    rng  = np.random.default_rng(seed)

    size = 100  # 100x100 px simulado
    base_ndvi = rng.uniform(0.35, 0.75)
    red  = rng.uniform(0.03, 0.15, (size, size)).astype(np.float32)
    nir  = (red * (1 + base_ndvi) / (1 - base_ndvi + 1e-9)).astype(np.float32)
    swir = rng.uniform(0.05, 0.20, (size, size)).astype(np.float32)
    blue = rng.uniform(0.01, 0.08, (size, size)).astype(np.float32)

    bands  = BandArrays(red=red, nir=nir, swir=swir, blue=blue)
    result = process_bands(bands)
    return result
