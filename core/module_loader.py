# -*- coding: utf-8 -*-
"""
Cargador dinámico de módulos según perfil de usuario.
Carga solo los módulos permitidos por el perfil (configuración sin import real de clases).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.profile_engine import ProfileType


class ModuleLoader:
    """Cargador dinámico de módulos según el perfil de usuario."""

    def __init__(self) -> None:
        self.available_modules = self._discover_modules()
        self.loaded_modules: Dict[str, Any] = {}

    def _discover_modules(self) -> Dict[str, Dict[str, Any]]:
        """Descubre los módulos disponibles en el sistema."""
        return {
            "security": {
                "path": "security",
                "class": "SecurityManager",
                "description": "Gestión de seguridad física y cibernéctica",
                "required_profile": ProfileType.TECHNICIAN,
                "dependencies": ["blockchain", "iot"],
            },
            "production": {
                "path": "production",
                "class": "LocalProductionSystem",
                "description": "Gestión de producción agrícola con drones",
                "required_profile": ProfileType.FARMER,
                "dependencies": ["blockchain"],
            },
            "blockchain": {
                "path": "blockchain",
                "class": "GaiaChainClient",
                "description": "Gestión de GaiaChain y smart contracts",
                "required_profile": ProfileType.LANDUM_PRO,
                "dependencies": [],
            },
            "compliance": {
                "path": "compliance",
                "class": "AEMPSCompliance",
                "description": "Gestión de normativas (AEMPS, ISO, etc.)",
                "required_profile": ProfileType.AUDITOR,
                "dependencies": ["blockchain"],
            },
            "iot": {
                "path": "iot",
                "class": "IoTManager",
                "description": "Gestión de sensores y dispositivos IoT",
                "required_profile": ProfileType.FARMER,
                "dependencies": [],
            },
            "messaging": {
                "path": "messaging",
                "class": "EuropeanDroneNetwork",
                "description": "Red europea de drones y mensajería",
                "required_profile": ProfileType.LANDUM_PRO,
                "dependencies": ["blockchain"],
            },
            "analytics": {
                "path": "analytics",
                "class": "AnalyticsManager",
                "description": "Análisis avanzado de datos agrícolas",
                "required_profile": ProfileType.LANDUM_PRO,
                "dependencies": ["production", "blockchain"],
            },
            "academy": {
                "path": "academy",
                "class": "CastuaLMS",
                "description": "Gestión de CASTUO Academy",
                "required_profile": ProfileType.STUDENT,
                "dependencies": [],
            },
        }

    def load_module(self, module_name: str, profile_type: ProfileType) -> Optional[Any]:
        """Carga un módulo si el perfil tiene permisos (retorna instancia stub o real según disponibilidad)."""
        module_info = self.available_modules.get(module_name)
        if not module_info:
            return None
        required_level = module_info["required_profile"].access_level
        if profile_type.access_level < required_level:
            return None
        for dep in module_info.get("dependencies", []):
            if dep not in self.loaded_modules:
                self.load_module(dep, profile_type)
        if module_name in self.loaded_modules:
            return self.loaded_modules[module_name]
        try:
            mod = __import__(module_info["path"], fromlist=[module_info["class"]])
            cls = getattr(mod, module_info["class"], None)
            if cls is not None:
                try:
                    instance = cls()
                except TypeError:
                    instance = cls(None)
            else:
                instance = {"module": module_name, "stub": True}
            self.loaded_modules[module_name] = instance
            return instance
        except (ImportError, AttributeError, TypeError) as e:
            self.loaded_modules[module_name] = {"module": module_name, "stub": True, "error": str(e)}
            return self.loaded_modules[module_name]

    def unload_module(self, module_name: str) -> bool:
        """Descarga un módulo si está cargado."""
        if module_name not in self.loaded_modules:
            return False
        del self.loaded_modules[module_name]
        return True

    def get_available_modules(self, profile_type: ProfileType) -> List[Dict[str, Any]]:
        """Obtiene los módulos disponibles para un perfil."""
        return [
            {
                **info,
                "available": profile_type.access_level >= info["required_profile"].access_level,
            }
            for name, info in self.available_modules.items()
        ]

    def get_loaded_modules(self) -> List[str]:
        """Obtiene la lista de módulos actualmente cargados."""
        return list(self.loaded_modules.keys())


if __name__ == "__main__":
    loader = ModuleLoader()
    for m in loader.get_available_modules(ProfileType.LANDUM_PRO):
        print(m["description"], "- Disponible:", m["available"])
    b = loader.load_module("blockchain", ProfileType.LANDUM_PRO)
    print("Cargados:", loader.get_loaded_modules())
