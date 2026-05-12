# backend/crypto_master/hierarchical_keys.py
# Derivación sub-claves por nivel (HKDF). Roles jerárquicos.

from __future__ import annotations

from typing import Any, Dict, List

try:
    from .master_key_manager import MasterKeyManager
except ImportError:
    from master_key_manager import MasterKeyManager

ADMIN_STRUCTURE: List[Dict[str, Any]] = [
    {
        "nivel": 0,
        "rol": "GREGORIO",
        "clave": "CLAVE_MAESTRA",
        "acceso": "TOTAL",
        "riesgo": "CRÍTICO",
        "playbook": "backend.models.system_admin_playbook.ADMIN_GENERAL_ROLE",
    },
    {"nivel": 1, "rol": "SABIONDA", "clave": "derive_key(0,1)", "acceso": "ORQUESTACIÓN", "riesgo": "ALTO"},
    {"nivel": 2, "rol": "FEDERACIÓN", "clave": "derive_key(0,2)", "acceso": "3 NODOS", "riesgo": "MEDIO"},
    {"nivel": 3, "rol": "EDU/AGENTES", "clave": "derive_key(0,3)", "acceso": "EJECUCIÓN", "riesgo": "BAJO"},
    {"nivel": 4, "rol": "AUDIT", "clave": "derive_key(0,4)", "acceso": "READ-ONLY", "riesgo": "MÍNIMO"},
]

SYSTEM_IDS = ["OMEGA", "SABIONDA", "FEDERACION", "EDU", "AUDIT"]


def get_subkey_for_level(manager: MasterKeyManager, system_id: str, level: int) -> bytes:
    """Deriva sub-clave para sistema y nivel."""
    return manager.derive_subkey(system_id, level)


def get_admin_structure() -> List[Dict[str, Any]]:
    """Estructura de roles jerárquicos encriptados."""
    return list(ADMIN_STRUCTURE)
