"""
SIGPAC API — Stub de integración
Análisis crítico v2.5 — CTAEX framework.

Estado: STUB (sin contrato activo con MAPA/FEGA)
Requiere: convenio firmado con MAPA + clave API SIGPAC productiva.

Referencia normativa:
  - Reglamento (UE) 1307/2013 — SIGPAC base legal
  - RD 1077/2014 — sistema integrado de gestión y control
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §2.1
"""

from __future__ import annotations


class SIGPACApi:
    """
    Cliente para la API SIGPAC (Sistema de Información Geográfica de Parcelas Agrícolas).

    Stub honesto: no realiza llamadas reales hasta firma de convenio MAPA/FEGA.
    Todos los métodos lanzan NotImplementedError para evitar URLs falsas en producción.
    """

    def get_parcel_data(self, sigpac_ref: str) -> dict:
        """
        Obtiene datos de parcela por referencia SIGPAC.

        Args:
            sigpac_ref: Referencia catastral SIGPAC (ej. "10:001:0001:00001:0001:WI")

        Raises:
            NotImplementedError: Siempre — requiere contrato activo con MAPA/FEGA.
        """
        raise NotImplementedError(
            "Requiere contrato MAPA/FEGA: integración SIGPAC no disponible. "
            "Contactar con MAPA para obtener acceso a la API SIGPAC productiva."
        )

    def validate_parcel_eligibility(self, sigpac_ref: str, uso_sigpac: str) -> dict:
        """
        Valida elegibilidad PAC de una parcela.

        Raises:
            NotImplementedError: Siempre — requiere contrato activo con MAPA/FEGA.
        """
        raise NotImplementedError(
            "Requiere contrato MAPA/FEGA: validación PAC no disponible."
        )

    def get_geospatial_data(self, provincia: int, municipio: int, poligono: int, parcela: int) -> dict:
        """
        Obtiene geometría GeoJSON de parcela por referencia catastral.

        Raises:
            NotImplementedError: Siempre — requiere contrato activo con MAPA/FEGA.
        """
        raise NotImplementedError(
            "Requiere contrato MAPA/FEGA: datos geoespaciales SIGPAC no disponibles."
        )
