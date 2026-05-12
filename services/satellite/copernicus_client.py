"""
CASTÚO-SYSTEM™ v3.1 — Copernicus Data Space Client
Acceso soberano UE a datos Sentinel-1/2/3 vía CDSE OData/STAC API

Documentación oficial:
  https://dataspace.copernicus.eu/analyse-data/apis/catalogue-apis/stac-api
  https://dataspace.copernicus.eu/analyse-data/apis/odata

Variables de entorno:
  COPERNICUS_CLIENT_ID      — Client ID de CDSE (registro gratuito)
  COPERNICUS_CLIENT_SECRET  — Client Secret CDSE
  COPERNICUS_TOKEN_URL      — Token URL (default: Keycloak CDSE)
  COPERNICUS_STAC_URL       — STAC catalog URL
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger("castuo.satellite.copernicus")

# ── Configuración ──────────────────────────────────────────────────────────────
_CLIENT_ID      = os.getenv("COPERNICUS_CLIENT_ID", "")
_CLIENT_SECRET  = os.getenv("COPERNICUS_CLIENT_SECRET", "")
_TOKEN_URL      = os.getenv(
    "COPERNICUS_TOKEN_URL",
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
)
_STAC_URL       = os.getenv("COPERNICUS_STAC_URL", "https://catalogue.dataspace.copernicus.eu/stac")
_ODATA_URL      = os.getenv("COPERNICUS_ODATA_URL", "https://catalogue.dataspace.copernicus.eu/odata/v1")
_REQUEST_TIMEOUT = int(os.getenv("COPERNICUS_TIMEOUT_S", "30"))


class CopernicusClient:
    """
    Cliente para Copernicus Data Space Ecosystem (CDSE).

    Soporta:
    - Autenticación OAuth2 con renovación automática de token
    - Búsqueda STAC de productos Sentinel-1/2/3
    - Descarga de productos (OData)
    - Fallback a datos simulados cuando las credenciales no están configuradas
    """

    def __init__(self) -> None:
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def _configured(self) -> bool:
        return bool(_CLIENT_ID and _CLIENT_SECRET)

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_REQUEST_TIMEOUT)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _ensure_token(self) -> Optional[str]:
        """Obtiene o renueva el token OAuth2 de CDSE."""
        if not self._configured:
            return None

        now = datetime.now(timezone.utc)
        if self._token and self._token_expires and now < self._token_expires:
            return self._token

        try:
            resp = await self.client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": _CLIENT_ID,
                    "client_secret": _CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires = now + timedelta(seconds=data.get("expires_in", 600) - 30)
            logger.info("[copernicus] Token OAuth2 renovado")
            return self._token
        except Exception as exc:
            logger.warning("[copernicus] Error de autenticación: %s", exc)
            return None

    async def search_sentinel2(
        self,
        bbox: list[float],          # [lon_min, lat_min, lon_max, lat_max]
        start_date: str,            # "2026-03-01"
        end_date: str,              # "2026-04-01"
        cloud_cover_max: float = 20.0,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Busca productos Sentinel-2 L2A para el bounding-box y período indicados.
        Devuelve lista de items STAC con metadatos y URLs de descarga.
        """
        if not self._configured:
            logger.warning("[copernicus] Credenciales no configuradas — retornando datos simulados")
            return self._simulated_sentinel2(bbox, start_date, end_date)

        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        params = {
            "collections": "SENTINEL-2",
            "bbox": ",".join(str(v) for v in bbox),
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "query": f'{{"eo:cloud_cover":{{"lt":{cloud_cover_max}}},"s2:processing_baseline":{{"gt":"04.00"}}}}',
            "limit": limit,
        }

        try:
            resp = await self.client.get(f"{_STAC_URL}/search", params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("features", [])
            logger.info("[copernicus] Sentinel-2 búsqueda: %d items en %s", len(items), bbox)
            return items
        except Exception as exc:
            logger.warning("[copernicus] Error en búsqueda STAC: %s — fallback simulado", exc)
            return self._simulated_sentinel2(bbox, start_date, end_date)

    async def get_product_bands(
        self,
        product_id: str,
        bands: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Obtiene URLs de descarga de bandas específicas de un producto.
        bands: ["B04", "B08", "B11"] (rojo, NIR, SWIR)
        """
        if not self._configured:
            return self._simulated_band_urls(product_id, bands or ["B04", "B08"])

        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        try:
            resp = await self.client.get(
                f"{_ODATA_URL}/Products({product_id})/Nodes",
                headers=headers,
            )
            resp.raise_for_status()
            nodes = resp.json().get("value", [])
            band_urls = {}
            for node in nodes:
                name = node.get("Name", "")
                if bands is None or any(b in name for b in (bands or [])):
                    band_urls[name] = node.get("@odata.mediaReadLink", "")
            return band_urls
        except Exception as exc:
            logger.warning("[copernicus] Error obteniendo bandas: %s", exc)
            return self._simulated_band_urls(product_id, bands or ["B04", "B08"])

    async def health(self) -> dict[str, Any]:
        """Verifica disponibilidad de CDSE."""
        if not self._configured:
            return {
                "status": "not_configured",
                "message": "COPERNICUS_CLIENT_ID / COPERNICUS_CLIENT_SECRET no configurados",
            }
        try:
            resp = await self.client.get(f"{_STAC_URL}/", timeout=5)
            return {"status": "ok" if resp.status_code < 400 else "error", "http": resp.status_code}
        except Exception as exc:
            return {"status": "unreachable", "error": str(exc)}

    # ── Datos simulados (dev/staging sin credenciales) ────────────────────────

    def _simulated_sentinel2(
        self, bbox: list[float], start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Devuelve un item STAC simulado reproducible para desarrollo."""
        bbox_hash = hashlib.sha256(f"{bbox}{start_date}".encode()).hexdigest()[:8]
        return [
            {
                "type": "Feature",
                "stac_version": "1.0.0",
                "id": f"SIM-S2A-{bbox_hash}",
                "collection": "SENTINEL-2",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[bbox[0], bbox[1]], [bbox[2], bbox[1]],
                                     [bbox[2], bbox[3]], [bbox[0], bbox[3]],
                                     [bbox[0], bbox[1]]]],
                },
                "properties": {
                    "datetime": f"{start_date}T10:30:00Z",
                    "eo:cloud_cover": 5.2,
                    "platform": "sentinel-2a",
                    "instrument": "msi",
                    "sim": True,
                },
                "assets": {
                    "B04": {"href": f"sim://sentinel-2/{bbox_hash}/B04.tif", "type": "image/tiff"},
                    "B08": {"href": f"sim://sentinel-2/{bbox_hash}/B08.tif", "type": "image/tiff"},
                    "B11": {"href": f"sim://sentinel-2/{bbox_hash}/B11.tif", "type": "image/tiff"},
                },
            }
        ]

    def _simulated_band_urls(
        self, product_id: str, bands: list[str]
    ) -> dict[str, str]:
        return {b: f"sim://sentinel-2/{product_id}/{b}.tif" for b in bands}
