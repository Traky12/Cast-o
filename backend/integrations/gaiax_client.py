"""
Gaia-X / Copernicus — Stub de integración
Análisis crítico v2.5 — CTAEX framework.

Estado: STUB (requiere onboarding en Gaia-X + acceso Copernicus)
Gaia-X onboarding: https://gaia-x.eu/onboarding
Copernicus DIAS: https://www.copernicus.eu/en/access-data/dias

Referencia normativa:
  - Regulación (UE) 2021/696 — Programa Espacial Europeo (Copernicus)
  - Gaia-X Trust Framework 22.10
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §2.1
"""

from __future__ import annotations


class GaiaXClient:
    """
    Cliente para Gaia-X Federation Services y Copernicus Data Space.

    Stub honesto: no realiza llamadas reales hasta completar onboarding Gaia-X.
    El proceso requiere verificación de Participante y firma del Trust Framework.
    """

    def register_asset(self, asset_description: dict) -> dict:
        """
        Registra un asset en el catálogo Gaia-X (Self-Description).

        Args:
            asset_description: Metadatos del asset en formato Gaia-X Self-Description

        Raises:
            NotImplementedError: Siempre — requiere onboarding Gaia-X completado.
        """
        raise NotImplementedError(
            "Requiere contrato Gaia-X: completar onboarding como Participante Gaia-X. "
            "Iniciar proceso en https://gaia-x.eu/onboarding"
        )

    def get_copernicus_satellite_data(
        self,
        bbox: tuple[float, float, float, float],
        fecha_ini: str,
        fecha_fin: str,
        dataset: str = "sentinel-2-l2a",
    ) -> dict:
        """
        Obtiene datos de satélite Copernicus (Sentinel-2) para un área geográfica.

        Args:
            bbox: Bounding box (lon_min, lat_min, lon_max, lat_max)
            fecha_ini: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
            dataset: Dataset Copernicus (ej. "sentinel-2-l2a")

        Raises:
            NotImplementedError: Siempre — requiere acceso Copernicus DIAS.
        """
        raise NotImplementedError(
            "Requiere acceso Copernicus DIAS: registrarse en https://www.copernicus.eu/en/access-data/dias"
        )

    def create_verifiable_credential(self, claims: dict) -> dict:
        """
        Emite una Verifiable Credential Gaia-X para trazabilidad de datos.

        Raises:
            NotImplementedError: Siempre — requiere identidad Gaia-X verificada.
        """
        raise NotImplementedError(
            "Requiere contrato Gaia-X: emisión de VC requiere identidad verificada."
        )
