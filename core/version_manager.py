# -*- coding: utf-8 -*-
"""
Sistema de gestión de versiones y perfiles SABIONDA.
Motor de perfiles que adapta la respuesta según el tipo de usuario (Gregorio/admin, Landum Pro, técnico, agricultor, auditor, estudiante, invitado).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from dataclasses import dataclass, field

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient


# Identificación de versión y edición SABIONDA
SABIONDA_VERSION = "5.0.0"
SABIONDA_EDITION = "SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO"


class UserProfileType(Enum):
    """Tipos de perfiles de usuario con diferentes niveles de acceso."""

    ADMIN = "admin"  # Acceso total (Gregorio)
    LANDUM_PRO = "landum_pro"  # Versión profesional (SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO)
    TECHNICIAN = "technician"  # Técnicos de campo (acceso a operaciones)
    FARMER = "farmer"  # Agricultores (versión simplificada)
    AUDITOR = "auditor"  # Auditores (solo lectura + informes)
    STUDENT = "student"  # Versión educativa (CASTUO Academy)
    GUEST = "guest"  # Acceso mínimo (demo)


@dataclass
class UserProfile:
    """Configuración de un perfil de usuario: permisos, UI y capacidades."""

    profile_type: UserProfileType
    label: str
    description: str
    permissions: List[str]  # Lista de permisos (ej: "dashboard", "drones", "blockchain", "admin")
    ui_simplified: bool  # True = interfaz simplificada (farmer, guest)
    read_only: bool  # True = solo lectura (auditor)
    max_entities: Optional[int]  # Límite de entidades visibles (None = sin límite)
    features: List[str]  # Features habilitadas para este perfil
    menu_sections: List[str]  # Secciones de menú visibles
    hide_technical: bool  # Ocultar datos técnicos avanzados
    allow_export: bool
    allow_reports: bool


# Definición de perfiles por tipo
PROFILE_CONFIGS: Dict[UserProfileType, UserProfile] = {
    UserProfileType.ADMIN: UserProfile(
        profile_type=UserProfileType.ADMIN,
        label="Administrador",
        description="Acceso total al sistema (Gregorio)",
        permissions=[
            "dashboard",
            "drones",
            "production",
            "blockchain",
            "compliance",
            "security",
            "messaging",
            "academy",
            "admin",
            "version_manager",
            "users",
            "audit",
        ],
        ui_simplified=False,
        read_only=False,
        max_entities=None,
        features=[
            "full_config",
            "gaia_chain",
            "post_quantum",
            "aemps_automation",
            "drone_network",
            "local_production",
            "traceability",
        ],
        menu_sections=[
            "dashboard",
            "operaciones",
            "producción",
            "trazabilidad",
            "cumplimiento",
            "seguridad",
            "red_europea",
            "academia",
            "administración",
        ],
        hide_technical=False,
        allow_export=True,
        allow_reports=True,
    ),
    UserProfileType.LANDUM_PRO: UserProfile(
        profile_type=UserProfileType.LANDUM_PRO,
        label="Landum Profesional",
        description="Versión profesional SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO",
        permissions=[
            "dashboard",
            "drones",
            "production",
            "blockchain",
            "compliance",
            "messaging",
            "academy",
        ],
        ui_simplified=False,
        read_only=False,
        max_entities=None,
        features=[
            "full_config",
            "gaia_chain",
            "drone_network",
            "local_production",
            "traceability",
        ],
        menu_sections=[
            "dashboard",
            "operaciones",
            "producción",
            "trazabilidad",
            "cumplimiento",
            "red_europea",
            "academia",
        ],
        hide_technical=False,
        allow_export=True,
        allow_reports=True,
    ),
    UserProfileType.TECHNICIAN: UserProfile(
        profile_type=UserProfileType.TECHNICIAN,
        label="Técnico de campo",
        description="Acceso a operaciones y equipos",
        permissions=["dashboard", "drones", "production", "messaging"],
        ui_simplified=False,
        read_only=False,
        max_entities=500,
        features=["drone_network", "local_production", "traceability"],
        menu_sections=["dashboard", "operaciones", "producción", "red_europea"],
        hide_technical=True,
        allow_export=True,
        allow_reports=False,
    ),
    UserProfileType.FARMER: UserProfile(
        profile_type=UserProfileType.FARMER,
        label="Agricultor",
        description="Versión simplificada para uso en explotación",
        permissions=["dashboard", "drones", "production"],
        ui_simplified=True,
        read_only=False,
        max_entities=100,
        features=["drone_network", "local_production"],
        menu_sections=["dashboard", "operaciones", "producción"],
        hide_technical=True,
        allow_export=True,
        allow_reports=False,
    ),
    UserProfileType.AUDITOR: UserProfile(
        profile_type=UserProfileType.AUDITOR,
        label="Auditor",
        description="Solo lectura e informes",
        permissions=["dashboard", "blockchain", "compliance", "audit"],
        ui_simplified=False,
        read_only=True,
        max_entities=None,
        features=["gaia_chain", "compliance", "reports"],
        menu_sections=["dashboard", "trazabilidad", "cumplimiento", "informes"],
        hide_technical=False,
        allow_export=True,
        allow_reports=True,
    ),
    UserProfileType.STUDENT: UserProfile(
        profile_type=UserProfileType.STUDENT,
        label="Estudiante (CASTUO Academy)",
        description="Versión educativa con contenido limitado",
        permissions=["dashboard", "academy"],
        ui_simplified=True,
        read_only=True,
        max_entities=50,
        features=["academy", "demo_data"],
        menu_sections=["dashboard", "academia", "recursos"],
        hide_technical=True,
        allow_export=False,
        allow_reports=False,
    ),
    UserProfileType.GUEST: UserProfile(
        profile_type=UserProfileType.GUEST,
        label="Invitado",
        description="Acceso mínimo para demo",
        permissions=["dashboard"],
        ui_simplified=True,
        read_only=True,
        max_entities=10,
        features=["demo_data"],
        menu_sections=["dashboard"],
        hide_technical=True,
        allow_export=False,
        allow_reports=False,
    ),
}


class VersionManager:
    """
    Motor de versiones y perfiles SABIONDA.
    Adapta la respuesta del sistema según el tipo de usuario y registra actividad en GaiaChain.
    """

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self._profile_configs = PROFILE_CONFIGS
        self._version = SABIONDA_VERSION
        self._edition = SABIONDA_EDITION

    def get_version(self) -> Dict[str, str]:
        """Devuelve la versión y edición actual del sistema."""
        return {
            "version": self._version,
            "edition": self._edition,
            "build_id": self._build_id(),
            "timestamp": datetime.now().isoformat(),
        }

    def _build_id(self) -> str:
        """Genera un identificador de build reproducible."""
        data = f"{self._version}-{self._edition}-{datetime.now().strftime('%Y%m%d')}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def get_profile(self, profile_type: Union[UserProfileType, str]) -> UserProfile:
        """Obtiene la configuración de un perfil por tipo."""
        if isinstance(profile_type, str):
            try:
                profile_type = UserProfileType(profile_type)
            except ValueError:
                profile_type = UserProfileType.GUEST
        return self._profile_configs.get(profile_type, self._profile_configs[UserProfileType.GUEST])

    def get_profile_for_user(
        self,
        user_id: str,
        profile_type: Union[UserProfileType, str],
        log_activity: bool = True,
    ) -> Dict[str, Any]:
        """
        Devuelve la configuración de perfil adaptada para un usuario.
        Si log_activity=True, registra la activación del perfil en GaiaChain.
        """
        profile = self.get_profile(profile_type)
        if log_activity and self.gaiachain:
            self.gaiachain.log_profile_activity(
                {
                    "user_id": user_id,
                    "profile_type": profile.profile_type.value,
                    "profile_label": profile.label,
                    "timestamp": datetime.now().isoformat(),
                    "version": self._version,
                    "edition": self._edition,
                }
            )
        return self._profile_to_response(profile, user_id)

    def _profile_to_response(self, profile: UserProfile, user_id: str) -> Dict[str, Any]:
        """Convierte un UserProfile en diccionario de respuesta para la API/UI."""
        return {
            "user_id": user_id,
            "profile_type": profile.profile_type.value,
            "label": profile.label,
            "description": profile.description,
            "permissions": profile.permissions,
            "ui_simplified": profile.ui_simplified,
            "read_only": profile.read_only,
            "max_entities": profile.max_entities,
            "features": profile.features,
            "menu_sections": profile.menu_sections,
            "hide_technical": profile.hide_technical,
            "allow_export": profile.allow_export,
            "allow_reports": profile.allow_reports,
            "version": self._version,
            "edition": self._edition,
        }

    def has_permission(
        self,
        profile_type: Union[UserProfileType, str],
        permission: str,
    ) -> bool:
        """Comprueba si un perfil tiene un permiso concreto."""
        profile = self.get_profile(profile_type)
        return permission in profile.permissions or "admin" in profile.permissions

    def filter_by_profile(
        self,
        profile_type: Union[UserProfileType, str],
        data: Dict[str, Any],
        context: str = "default",
    ) -> Dict[str, Any]:
        """
        Filtra o adapta un diccionario de datos según el perfil (ej. ocultar campos técnicos).
        """
        profile = self.get_profile(profile_type)
        if not profile.hide_technical:
            return data
        # Campos que se ocultan en perfiles simplificados
        technical_keys = {
            "gaiachain_tx",
            "components_hash",
            "quality_hash",
            "blockchain_tx",
            "internal_id",
            "debug",
            "raw_telemetry",
        }
        return self._filter_dict(data, technical_keys)

    def _filter_dict(self, d: Dict[str, Any], hide_keys: set) -> Dict[str, Any]:
        """Recursivamente elimina claves que están en hide_keys."""
        out: Dict[str, Any] = {}
        for k, v in d.items():
            if k in hide_keys:
                continue
            if isinstance(v, dict):
                out[k] = self._filter_dict(v, hide_keys)
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                out[k] = [self._filter_dict(i, hide_keys) for i in v]
            else:
                out[k] = v
        return out

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Lista todos los perfiles disponibles (para selectores de admin)."""
        return [
            {
                "profile_type": p.profile_type.value,
                "label": p.label,
                "description": p.description,
                "read_only": p.read_only,
                "ui_simplified": p.ui_simplified,
            }
            for p in self._profile_configs.values()
        ]


if __name__ == "__main__":
    vm = VersionManager(gaiachain_client=GaiaChainClient())
    print("Versión:", vm.get_version())
    print("\nPerfil ADMIN (Gregorio):")
    r = vm.get_profile_for_user("gregorio", UserProfileType.ADMIN)
    print("  permissions:", r["permissions"][:4], "...")
    print("  menu_sections:", r["menu_sections"])
    print("\nPerfil FARMER:")
    r2 = vm.get_profile_for_user("farmer_01", UserProfileType.FARMER)
    print("  ui_simplified:", r2["ui_simplified"], "read_only:", r2["read_only"])
    print("  menu_sections:", r2["menu_sections"])
    print("\nhas_permission(FARMER, 'admin'):", vm.has_permission(UserProfileType.FARMER, "admin"))
    print("has_permission(ADMIN, 'admin'):", vm.has_permission(UserProfileType.ADMIN, "admin"))
