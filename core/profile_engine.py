# -*- coding: utf-8 -*-
"""
Motor de perfiles dinámicos SABIONDA.
Gestiona permisos, tonos de voz y funcionalidades por perfil con sesiones y GaiaChain.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from blockchain.gaia_chain import GaiaChainClient


class ProfileType(Enum):
    """Tipos de perfiles con niveles de acceso escalonados."""

    SABIONDA_MASTER_LANDUM = auto()
    LANDUM_PRO = auto()
    TECHNICIAN = auto()
    FARMER = auto()
    AUDITOR = auto()
    STUDENT = auto()
    GUEST = auto()

    @property
    def access_level(self) -> int:
        """Nivel de acceso (1-100)."""
        levels = {
            ProfileType.SABIONDA_MASTER_LANDUM: 100,
            ProfileType.LANDUM_PRO: 90,
            ProfileType.TECHNICIAN: 70,
            ProfileType.FARMER: 50,
            ProfileType.AUDITOR: 30,
            ProfileType.STUDENT: 20,
            ProfileType.GUEST: 10,
        }
        return levels.get(self, 0)


@dataclass
class ProfileConfig:
    """Configuración de un perfil de usuario."""

    profile_type: ProfileType
    tone: str
    allowed_modules: List[str]
    restrictions: Dict[str, bool]
    max_tokens: int = 128000
    response_style: str = "structured"
    custom_settings: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "profile_type": self.profile_type.name,
            "access_level": self.profile_type.access_level,
            "tone": self.tone,
            "allowed_modules": self.allowed_modules,
            "restrictions": self.restrictions,
            "max_tokens": self.max_tokens,
            "response_style": self.response_style,
        }
        if self.custom_settings:
            d["custom_settings"] = self.custom_settings
        return d


class ProfileManager:
    """Gestor central de perfiles de usuario con integración en GaiaChain."""

    def __init__(self, gaiachain_client: Optional[GaiaChainClient] = None) -> None:
        self.gaiachain = gaiachain_client or GaiaChainClient()
        self.profiles_db = self._load_default_profiles()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def _load_default_profiles(self) -> Dict[str, ProfileConfig]:
        """Carga la configuración por defecto de los perfiles."""
        return {
            "SABIONDA_MASTER_LANDUM": ProfileConfig(
                profile_type=ProfileType.SABIONDA_MASTER_LANDUM,
                tone="professional",
                allowed_modules=["*"],
                restrictions={},
                max_tokens=256000,
                response_style="detailed",
            ),
            "LANDUM_PRO": ProfileConfig(
                profile_type=ProfileType.LANDUM_PRO,
                tone="technical",
                allowed_modules=[
                    "security",
                    "production",
                    "blockchain",
                    "compliance",
                    "analytics",
                    "messaging",
                ],
                restrictions={"blockchain_write": True, "security_admin": True},
                max_tokens=128000,
                response_style="structured",
            ),
            "TECHNICIAN": ProfileConfig(
                profile_type=ProfileType.TECHNICIAN,
                tone="friendly",
                allowed_modules=["production", "iot", "maintenance"],
                restrictions={
                    "blockchain_write": True,
                    "security_admin": True,
                    "compliance_edit": True,
                },
                max_tokens=64000,
                response_style="concise",
            ),
            "FARMER": ProfileConfig(
                profile_type=ProfileType.FARMER,
                tone="extremeño",
                allowed_modules=["iot", "alerts", "basic_analytics"],
                restrictions={
                    "blockchain_write": True,
                    "security_admin": True,
                    "compliance_edit": True,
                    "advanced_analytics": True,
                },
                max_tokens=32000,
                response_style="simple",
            ),
            "AUDITOR": ProfileConfig(
                profile_type=ProfileType.AUDITOR,
                tone="formal",
                allowed_modules=["compliance", "reports", "blockchain_read"],
                restrictions={
                    "blockchain_write": True,
                    "security_admin": True,
                    "production_edit": True,
                },
                max_tokens=64000,
                response_style="structured",
            ),
            "STUDENT": ProfileConfig(
                profile_type=ProfileType.STUDENT,
                tone="educational",
                allowed_modules=["academy", "simulations", "basic_reports"],
                restrictions={
                    "blockchain_write": True,
                    "security_admin": True,
                    "production_edit": True,
                    "sensitive_data": True,
                },
                max_tokens=16000,
                response_style="step_by_step",
            ),
            "GUEST": ProfileConfig(
                profile_type=ProfileType.GUEST,
                tone="neutral",
                allowed_modules=["demo", "basic_info"],
                restrictions={
                    "blockchain_write": True,
                    "security_admin": True,
                    "production_edit": True,
                    "sensitive_data": True,
                    "advanced_features": True,
                },
                max_tokens=8000,
                response_style="minimal",
            ),
        }

    def get_profile(self, profile_id: str) -> Optional[ProfileConfig]:
        """Obtiene la configuración de un perfil."""
        return self.profiles_db.get(profile_id)

    def create_session(self, user_id: str, profile_id: str) -> str:
        """Crea una nueva sesión para un usuario con un perfil específico."""
        profile = self.profiles_db.get(profile_id)
        if not profile:
            raise ValueError(f"Perfil {profile_id} no encontrado")

        session_id = hashlib.sha256(
            f"{user_id}_{profile_id}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "profile": profile,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }

        if self.gaiachain:
            self.gaiachain.log_user_session(
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "profile": profile_id,
                    "access_level": profile.profile_type.access_level,
                    "timestamp": datetime.now().isoformat(),
                    "status": "active",
                }
            )
        return session_id

    def validate_access(self, session_id: str, module: str, action: str) -> bool:
        """Valida si una sesión tiene acceso a un módulo/acción."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False

        profile = session["profile"]
        if module not in profile.allowed_modules and "*" not in profile.allowed_modules:
            return False
        if action == "write" and profile.restrictions.get("blockchain_write"):
            return False
        if action == "admin" and profile.restrictions.get("security_admin"):
            return False
        if action == "admin" and profile.restrictions.get(f"{module}_admin"):
            return False
        return True

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una sesión activa."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        return {
            "session_id": session_id,
            "user_id": session["user_id"],
            "profile": session["profile"].to_dict(),
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
        }

    def close_session(self, session_id: str) -> bool:
        """Cierra una sesión activa."""
        if session_id not in self.active_sessions:
            return False
        session = self.active_sessions.pop(session_id)
        if self.gaiachain:
            created = datetime.fromisoformat(session["created_at"])
            self.gaiachain.log_user_session(
                {
                    "session_id": session_id,
                    "user_id": session["user_id"],
                    "status": "closed",
                    "timestamp": datetime.now().isoformat(),
                    "duration": int((datetime.now() - created).total_seconds()),
                }
            )
        return True

    def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> bool:
        """Actualiza la configuración de un perfil."""
        if profile_id not in self.profiles_db:
            return False
        for key, value in updates.items():
            if hasattr(self.profiles_db[profile_id], key):
                setattr(self.profiles_db[profile_id], key, value)
        if self.gaiachain:
            self.gaiachain.log_profile_update(
                {
                    "profile_id": profile_id,
                    "updates": updates,
                    "timestamp": datetime.now().isoformat(),
                    "updated_by": "SABIONDA_MASTER_LANDUM",
                }
            )
        return True

    def create_custom_profile(self, profile_id: str, config: Dict[str, Any]) -> bool:
        """Crea un perfil personalizado (solo para SABIONDA_MASTER_LANDUM)."""
        if profile_id in self.profiles_db:
            return False
        try:
            profile_type = ProfileType[config["profile_type"]]
            self.profiles_db[profile_id] = ProfileConfig(
                profile_type=profile_type,
                tone=config.get("tone", "neutral"),
                allowed_modules=config.get("allowed_modules", []),
                restrictions=config.get("restrictions", {}),
                max_tokens=config.get("max_tokens", 32000),
                response_style=config.get("response_style", "structured"),
                custom_settings=config.get("custom_settings"),
            )
            if self.gaiachain:
                self.gaiachain.log_profile_creation(
                    {
                        "profile_id": profile_id,
                        "config": config,
                        "timestamp": datetime.now().isoformat(),
                        "created_by": "SABIONDA_MASTER_LANDUM",
                    }
                )
            return True
        except (KeyError, ValueError) as e:
            return False


if __name__ == "__main__":
    pm = ProfileManager(gaiachain_client=GaiaChainClient())
    landum_pro = pm.get_profile("LANDUM_PRO")
    print("Configuración LANDUM_PRO:", json.dumps(landum_pro.to_dict(), indent=2))
    session_id = pm.create_session("gregorio@castu.system", "LANDUM_PRO")
    print("Sesión creada:", session_id)
    print("Acceso security:read:", pm.validate_access(session_id, "security", "read"))
    print("Sesión info:", json.dumps(pm.get_session_info(session_id), indent=2, default=str))
    pm.close_session(session_id)
    print("Sesión cerrada.")
