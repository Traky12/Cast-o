"""
AEMET OpenData API — Stub de integración
Análisis crítico v2.5 — CTAEX framework.

Estado: STUB (requiere clave API AEMET OpenData activa)
Registro gratuito en: https://opendata.aemet.es/centrodedescargas/altaUsuario

Referencia normativa:
  - Ley 14/2015 del Meteorólogo — uso de datos AEMET
  - Open Data AEMET — licencia CC BY 4.0
  - PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §2.1
"""

from __future__ import annotations


class AEMETClient:
    """
    Cliente para AEMET OpenData API (Agencia Estatal de Meteorología).

    Stub honesto: no realiza llamadas reales hasta configurar clave API.
    Registrarse en https://opendata.aemet.es para obtener clave gratuita.
    """

    def get_realtime_data(self, estacion_id: str) -> dict:
        """
        Obtiene datos meteorológicos en tiempo real de una estación AEMET.

        Args:
            estacion_id: Identificador de estación AEMET (ej. "3195")

        Raises:
            NotImplementedError: Siempre — requiere clave API AEMET configurada.
        """
        raise NotImplementedError(
            "Requiere clave API AEMET: configurar AEMET_API_KEY en .env. "
            "Registro gratuito en https://opendata.aemet.es/centrodedescargas/altaUsuario"
        )

    def get_forecast(self, municipio_code: str, days: int = 7) -> dict:
        """
        Obtiene previsión meteorológica para un municipio.

        Raises:
            NotImplementedError: Siempre — requiere clave API AEMET configurada.
        """
        raise NotImplementedError(
            "Requiere clave API AEMET: configurar AEMET_API_KEY en .env."
        )

    def get_agroclimatic_data(self, estacion_id: str, fecha_ini: str, fecha_fin: str) -> dict:
        """
        Obtiene datos agroclimáticos históricos (temperatura, precipitación, ETo).

        Raises:
            NotImplementedError: Siempre — requiere clave API AEMET configurada.
        """
        raise NotImplementedError(
            "Requiere clave API AEMET: datos agroclimáticos no disponibles."
        )
