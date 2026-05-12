"""
Preprocesado satelital open-source (Sentinel-2 / Landsat): indices NDVI y albedo aproximado.

Requiere credenciales Copernicus para descarga OData real; aqui el nucleo estable es NDVI
desde bandas locales (.jp2/.tif) para no bloquear CI sin GDAL instalado.

Soberania UE: con CASTUO_EU_DATA_SOVEREIGNTY=1 (por defecto) solo queda catalogo Sentinel-2 (Copernicus/ESA);
Landsat (USGS) queda excluido del catalogo en runtime. Descarga OData solo hacia hosts *.copernicus.eu.
"""

from __future__ import annotations

import argparse
import json
import os
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np

from .eu_data_sovereignty import (
    build_copernicus_product_download_url,
    eu_processing_metadata,
    filter_band_catalog_for_eu,
)
from .witness_minimal import witness_energy_event

try:
    import rasterio
except ImportError:
    rasterio = None  # type: ignore


class SatelliteProcessor:
    def __init__(self, output_dir: str = "data/satellite/processed") -> None:
        _all_bands: Dict[str, Dict[str, str]] = {
            "Sentinel-2": {
                "B02": "blue",
                "B03": "green",
                "B04": "red",
                "B08": "nir",
                "B11": "swir1",
                "B12": "swir2",
            },
            "Landsat-8": {
                "B2": "blue",
                "B3": "green",
                "B4": "red",
                "B5": "nir",
                "B6": "swir1",
                "B7": "swir2",
            },
        }
        self.bands = filter_band_catalog_for_eu(_all_bands)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def compute_ndvi_from_pair(
        self, red_path: str, nir_path: str, out_path: str | None = None
    ) -> Dict[str, Any]:
        """NDVI desde B04/B08 locales; salida por defecto bajo ``output_dir``."""
        target = out_path or os.path.join(self.output_dir, "NDVI_from_pair.tif")
        return compute_ndvi_from_pair(red_path, nir_path, target)

    def download_sentinel_scene(self, product_id: str, output_dir: str = "data/satellite/raw") -> str:
        """
        Descarga OData Copernicus: en produccion usar credenciales DHuS y cliente oficial.
        Sin COPERNICUS_USER/PASS este metodo documenta la URL y exige implementacion operativa.
        """
        os.makedirs(output_dir, exist_ok=True)
        local_path = os.path.join(output_dir, f"{product_id}.zip")
        user = os.environ.get("COPERNICUS_USER", "").strip()
        pwd = os.environ.get("COPERNICUS_PASSWORD", "").strip()
        if not user or not pwd:
            raise RuntimeError(
                "Definir COPERNICUS_USER y COPERNICUS_PASSWORD para descarga OData, "
                "o descargar la escena manualmente al directorio raw."
            )
        url = build_copernicus_product_download_url(product_id)
        import requests

        with requests.get(url, stream=True, auth=(user, pwd), timeout=600) as response:
            response.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        return local_path

    def _find_band_paths(self, root: str, suffix: str) -> List[str]:
        out: List[str] = []
        for dirpath, _, files in os.walk(root):
            for name in files:
                if name.endswith(suffix):
                    out.append(os.path.join(dirpath, name))
        return out

    def preprocess_sentinel(self, zip_path: str, product_id: str) -> Dict[str, Any]:
        if rasterio is None:
            raise RuntimeError("Instalar rasterio + GDAL para preprocess_sentinel (pip install rasterio).")

        temp_root = os.path.join("data", "satellite", "temp", product_id.replace("/", "_"))
        os.makedirs(temp_root, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_root)

        reds = self._find_band_paths(temp_root, "B04.jp2") or self._find_band_paths(temp_root, "B04_10m.jp2")
        nirs = self._find_band_paths(temp_root, "B08.jp2") or self._find_band_paths(temp_root, "B08_10m.jp2")
        if not reds or not nirs:
            raise FileNotFoundError(
                "No se encontraron B04/B08 en el ZIP; verificar estructura L2A / GRD."
            )

        red_path, nir_path = reds[0], nirs[0]
        with rasterio.open(red_path) as red_src:
            red = red_src.read(1).astype("float32")
            profile = red_src.profile.copy()
        with rasterio.open(nir_path) as nir_src:
            nir = nir_src.read(1).astype("float32")

        if red.shape != nir.shape:
            raise ValueError("Dimensiones B04/B08 distintas; reproyectar antes de NDVI.")

        denom = nir + red
        ndvi = np.where(denom == 0, 0, (nir - red) / denom)

        out_path = os.path.join(self.output_dir, f"{product_id}_NDVI.tif")
        profile.update(dtype=rasterio.float32, count=1, compress="deflate")
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(ndvi.astype("float32"), 1)

        ndvi_stats = {
            "min": float(np.nanmin(ndvi)),
            "max": float(np.nanmax(ndvi)),
            "mean": float(np.nanmean(ndvi)),
            "std": float(np.nanstd(ndvi)),
            "product_id": product_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_path": out_path,
        }

        witness_energy_event(
            {
                "type": "satellite_processing",
                "product_id": product_id,
                "index": "NDVI",
                "stats": ndvi_stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "eu_sovereignty": eu_processing_metadata({"source_mission": "Sentinel-2"}),
            },
            os.environ.get("GAIA_COOP_ID", "CASTUO-ENERGY-01"),
        )
        return ndvi_stats

    def calculate_albedo(
        self,
        product_id: str,
        blue_path: str,
        red_path: str,
        nir_path: str,
    ) -> Dict[str, Any]:
        if rasterio is None:
            raise RuntimeError("Instalar rasterio para calculate_albedo.")
        with rasterio.open(blue_path) as blue_src:
            blue = blue_src.read(1).astype("float32")
        with rasterio.open(red_path) as red_src:
            red = red_src.read(1).astype("float32")
            profile = red_src.profile.copy()
        with rasterio.open(nir_path) as nir_src:
            nir = nir_src.read(1).astype("float32")
        if blue.shape != red.shape or red.shape != nir.shape:
            raise ValueError("Band dimension mismatch para albedo.")
        # Ponderacion simplificada (calibrar con literatura para vuestra ROI).
        albedo = 0.25 * blue + 0.5 * red + 0.25 * nir
        out_path = os.path.join(self.output_dir, f"{product_id}_ALBEDO.tif")
        profile.update(dtype=rasterio.float32, count=1, compress="deflate")
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(albedo.astype("float32"), 1)
        return {
            "min": float(np.nanmin(albedo)),
            "max": float(np.nanmax(albedo)),
            "mean": float(np.nanmean(albedo)),
            "product_id": product_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output_path": out_path,
        }


def compute_ndvi_from_pair(red_path: str, nir_path: str, out_path: str) -> Dict[str, Any]:
    """API estable para pruebas locales sin ZIP completo."""
    if rasterio is None:
        raise RuntimeError("Instalar rasterio.")
    with rasterio.open(red_path) as rsrc:
        red = rsrc.read(1).astype("float32")
        profile = rsrc.profile.copy()
    with rasterio.open(nir_path) as nsrc:
        nir = nsrc.read(1).astype("float32")
    denom = nir + red
    ndvi = np.where(denom == 0, 0, (nir - red) / denom)
    profile.update(dtype=rasterio.float32, count=1)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(ndvi.astype("float32"), 1)
    return {
        "mean": float(np.nanmean(ndvi)),
        "output_path": out_path,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "eu_sovereignty": eu_processing_metadata({"source_mission": "Sentinel-2"}),
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Preprocesado satelital Castuo energy_audit")
    p.add_argument("--product_id", type=str, help="ID Sentinel-2 L2A")
    p.add_argument("--zip", type=str, help="Ruta al .zip descargado")
    p.add_argument("--red", type=str, help="GeoTIFF/jp2 banda roja")
    p.add_argument("--nir", type=str, help="GeoTIFF/jp2 NIR")
    p.add_argument("--out", type=str, default="data/satellite/processed/NDVI_local.tif")
    args = p.parse_args()

    proc = SatelliteProcessor()
    if args.red and args.nir:
        stats = compute_ndvi_from_pair(args.red, args.nir, args.out)
        print(json.dumps(stats, indent=2))
        return
    if args.zip and args.product_id:
        stats = proc.preprocess_sentinel(args.zip, args.product_id)
        print(json.dumps(stats, indent=2))
        return
    p.print_help()


if __name__ == "__main__":
    main()
