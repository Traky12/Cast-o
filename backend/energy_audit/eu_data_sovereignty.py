"""
Soberania de datos UE: fuentes, descarga y metadatos de procesado alineados con residencia europea.

Sin esto, el dato puede cruzar fronteras extracomunitarias (p. ej. Landsat USGS) y debilitar el Art. 44-49 RGPD.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Mapping
from urllib.parse import urlparse

_STRICT_ENV = "CASTUO_EU_DATA_SOVEREIGNTY"
_DEFAULT_DHUS = "https://scihub.copernicus.eu/dhus"


def _is_copernicus_eu_host(hostname: str) -> bool:
    h = hostname.lower().strip(".")
    return h == "copernicus.eu" or h.endswith(".copernicus.eu")


def eu_data_sovereignty_strict() -> bool:
    """Modo estricto UE: excluye fuentes satelitales no comunitarias y valida endpoints Copernicus."""
    return os.environ.get(_STRICT_ENV, "1").strip().lower() in ("1", "true", "yes", "on")


def filter_band_catalog_for_eu(bands: Mapping[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Retira catalogos no-UE (p. ej. Landsat/USGS) cuando el modo estricto esta activo."""
    if not eu_data_sovereignty_strict():
        return dict(bands)
    out: Dict[str, Dict[str, str]] = {}
    for name, mapping in bands.items():
        if name.upper().startswith("LANDSAT"):
            continue
        out[name] = dict(mapping)
    return out


def copernicus_dhus_base() -> str:
    """Base DHuS/OData Copernicus; por defecto infraestructura ESA/UE (scihub)."""
    return os.environ.get("COPERNICUS_DHUS_BASE", _DEFAULT_DHUS).rstrip("/")


def assert_eu_copernicus_host(url: str) -> None:
    """Falla si la URL de descarga no pertenece al dominio Copernicus UE (anti suplantacion)."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip()
    if not host or not _is_copernicus_eu_host(host):
        raise ValueError(
            f"CASTUO: host Copernicus no UE o no permitido ({host!r}). "
            "Use scihub.copernicus.eu o *.dataspace.copernicus.eu."
        )


def build_copernicus_product_download_url(product_id: str) -> str:
    """URL OData para producto; valida host UE antes de exponer credenciales."""
    base = copernicus_dhus_base()
    assert_eu_copernicus_host(base + "/")
    return f"{base}/odata/v1/Products('{product_id}')/$value"


def eu_processing_metadata(extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Metadatos minimos para trazabilidad de procesado bajo marco UE."""
    meta: Dict[str, Any] = {
        "data_jurisdiction_target": "EU",
        "processing_policy": "CASTUO_EU_DATA_SOVEREIGNTY",
        "eu_strict": eu_data_sovereignty_strict(),
        "copernicus_endpoint": copernicus_dhus_base(),
    }
    if extra:
        meta.update(extra)
    return meta
