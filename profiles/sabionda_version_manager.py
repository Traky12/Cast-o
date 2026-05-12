# -*- coding: utf-8 -*-
"""
Gestor de versiones de SABIONDA para crear y administrar perfiles derivados.
Solo accesible desde SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.profile_engine import ProfileManager, ProfileType
from profiles.sabionda_master_config import get_sabionda_master_config, get_version_restrictions


class SabiondaVersionManager:
    """
    Gestor de versiones de SABIONDA para crear y administrar perfiles derivados.
    Solo accesible desde SABIONDA_MASTER_LANDUM_PROFESIONAL_CASTUO.
    """

    def __init__(self, profile_manager: ProfileManager) -> None:
        self.profile_manager = profile_manager
        self.master_config = get_sabionda_master_config()
        self.version_restrictions = get_version_restrictions()
        self.custom_versions: Dict[str, Dict[str, Any]] = {}

    def create_version(
        self,
        version_id: str,
        base_version: str,
        custom_settings: Dict[str, Any],
    ) -> bool:
        """Crea una versión personalizada basada en un perfil existente."""
        if version_id in self.custom_versions:
            return False
        base_config = self.version_restrictions.get(base_version)
        if not base_config:
            return False

        new_config = {
            **base_config,
            **custom_settings,
            "version_id": version_id,
            "base_version": base_version,
            "type": "custom",
            "created_by": "SABIONDA_MASTER_LANDUM",
            "created_at": datetime.now().isoformat(),
        }
        self.custom_versions[version_id] = new_config

        profile_config = {
            "profile_type": base_version,
            "tone": new_config.get("tone", base_config["tone"]),
            "allowed_modules": new_config.get("allowed_modules", base_config["allowed_modules"]),
            "restrictions": new_config.get("restrictions", base_config["restrictions"]),
            "max_tokens": new_config.get("max_tokens", base_config["max_tokens"]),
            "response_style": new_config.get("response_style", "structured"),
            "custom_settings": custom_settings,
        }
        return self.profile_manager.create_custom_profile(version_id, profile_config)

    def update_version(self, version_id: str, updates: Dict[str, Any]) -> bool:
        """Actualiza una versión personalizada."""
        if version_id not in self.custom_versions:
            return False
        self.custom_versions[version_id].update(updates)
        self.custom_versions[version_id]["updated_at"] = datetime.now().isoformat()
        return self.profile_manager.update_profile(version_id, updates)

    def delete_version(self, version_id: str) -> bool:
        """Elimina una versión personalizada."""
        if version_id not in self.custom_versions:
            return False
        del self.custom_versions[version_id]
        return True

    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de una versión."""
        if version_id in self.custom_versions:
            return self.custom_versions[version_id]
        return self.version_restrictions.get(version_id)

    def list_versions(self) -> List[Dict[str, Any]]:
        """Lista todas las versiones disponibles (estándar + personalizadas)."""
        versions = []
        for vid, config in self.version_restrictions.items():
            versions.append({**config, "version_id": vid, "type": "standard", "created_by": "system"})
        for vid, config in self.custom_versions.items():
            versions.append({
                **config,
                "version_id": vid,
                "type": "custom",
                "created_by": config.get("created_by", "unknown"),
            })
        return versions

    def get_version_diff(self, version_id: str) -> Dict[str, Any]:
        """Compara una versión con su versión base."""
        version = self.get_version(version_id)
        if not version or version.get("type") != "custom":
            return {}
        base_version = version.get("base_version")
        base_config = self.version_restrictions.get(base_version, {})
        diff = {}
        for key in base_config:
            if key in version and version[key] != base_config[key]:
                diff[key] = {"base": base_config[key], "custom": version[key]}
        return diff

    def export_version(self, version_id: str, format: str = "json") -> Union[str, Dict]:
        """Exporta la configuración de una versión."""
        version = self.get_version(version_id)
        if not version:
            return f"Versión {version_id} no encontrada"
        if format.lower() == "json":
            return json.dumps(version, indent=2)
        if format.lower() == "yaml":
            try:
                import yaml
                return yaml.dump(version, default_flow_style=False)
            except ImportError:
                return json.dumps(version, indent=2)
        return f"Formato no soportado: {format}"

    def import_version(self, version_config: Dict[str, Any]) -> bool:
        """Importa una versión desde una configuración externa."""
        version_id = version_config.get("version_id")
        if not version_id or version_id in self.custom_versions:
            return False
        self.custom_versions[version_id] = version_config
        base = version_config.get("base_version", "GUEST")
        return self.profile_manager.create_custom_profile(version_id, {
            "profile_type": base,
            "tone": version_config.get("tone", "neutral"),
            "allowed_modules": version_config.get("allowed_modules", []),
            "restrictions": version_config.get("restrictions", {}),
            "max_tokens": version_config.get("max_tokens", 32000),
            "response_style": version_config.get("response_style", "structured"),
            "custom_settings": version_config.get("custom_settings", {}),
        })


if __name__ == "__main__":
    from blockchain.gaia_chain import GaiaChainClient
    pm = ProfileManager(gaiachain_client=GaiaChainClient())
    vm = SabiondaVersionManager(pm)
    print("Versiones:", [v["version_id"] for v in vm.list_versions()])
    ok = vm.create_version(
        "LANDUM_PRO_AGRO",
        "LANDUM_PRO",
        {
            "tone": "agro_technical",
            "allowed_modules": ["production", "iot", "analytics", "messaging"],
            "restrictions": {"blockchain_write": False, "ai_autonomy": 80, "version_management": False},
            "max_tokens": 192000,
            "response_style": "agro_focused",
        },
    )
    print("Crear LANDUM_PRO_AGRO:", ok)
    if ok:
        print("Diff:", vm.get_version_diff("LANDUM_PRO_AGRO"))
        print("Export:", vm.export_version("LANDUM_PRO_AGRO")[:200] + "...")
