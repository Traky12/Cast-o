"""
Reserva de interfaz para cliente SIGPAC/FEGA remoto: sin requests, sin host de API.

Hasta contrato y endpoint oficial, el flujo válido es exportación manual desde el visor
y validación con SIGPACValidator.
"""
from __future__ import annotations

from typing import Any, Dict


class SIGPACRemoteClientPlaceholder:
    """Placeholder para futura integración con API SIGPAC (requiere contrato).

    Nota: No implementado. Usar descarga manual de GeoJSON desde
    https://sigpac.mapa.gob.es/ y validación con `SIGPACValidator`.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError(
            "SIGPACRemoteClient no está implementado. "
            "Usar descarga manual de GeoJSON desde https://sigpac.mapa.gob.es/ "
            "y validación con `SIGPACValidator`."
        )

    def validate_parcel(self, parcel_id: str) -> Dict[str, Any]:
        """Validar una parcela mediante API SIGPAC (requiere implementación real)."""
        raise NotImplementedError("Método no implementado. Ver documentación.")

    def get_parcel_geometry(self, parcel_id: str) -> Dict[str, Any]:
        """Obtener geometría de una parcela (requiere implementación real)."""
        raise NotImplementedError("Método no implementado. Ver documentación.")
