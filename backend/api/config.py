"""
Configuración API EU/OSS (mínima).

Motivo: varios servicios bajo `backend/api/services/*` referencian `from ..config import settings`.
En este repositorio no existía `backend/api/config.py`, lo que impedía importar rutas
como `/api/admin/pqc/sign` y los endpoints de auditoría GaiaChain.
"""

from __future__ import annotations

import os


class _Settings:
    # RPC de GaiaChain (por defecto: entorno local/dehesa).
    GAIA_CHAIN_RPC: str = os.getenv(
        "GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com"
    ).strip()

    # Contrato de auditoría (address) y ABI en string JSON.
    GAIA_CHAIN_AUDIT_CONTRACT: str = os.getenv(
        "GAIA_CHAIN_AUDIT_CONTRACT",
        "0x0000000000000000000000000000000000000000",
    ).strip()
    GAIA_CHAIN_AUDIT_ABI: str = os.getenv(
        "GAIA_CHAIN_AUDIT_ABI",
        "[]",
    ).strip()

    # Clave privada para registrar eventos on-chain (operación interna; mantener en Vault/HSM real).
    GAIA_CHAIN_PRIVATE_KEY: str = os.getenv(
        "GAIA_CHAIN_PRIVATE_KEY",
        "0x0",
    ).strip()


settings = _Settings()

