# -*- coding: utf-8 -*-
"""Núcleo SABIONDA: gestión de versiones, perfiles, sesiones y módulos."""
from .version_manager import (
    UserProfileType,
    UserProfile,
    VersionManager,
    SABIONDA_VERSION,
    SABIONDA_EDITION,
)
from .profile_engine import ProfileType, ProfileConfig, ProfileManager
from .response_engine import AdaptiveResponseEngine
from .audit_system import AuditSystem
from .module_loader import ModuleLoader
from .dependency_manager import DependencyManager

__all__ = [
    "UserProfileType",
    "UserProfile",
    "VersionManager",
    "SABIONDA_VERSION",
    "SABIONDA_EDITION",
    "ProfileType",
    "ProfileConfig",
    "ProfileManager",
    "AdaptiveResponseEngine",
    "AuditSystem",
    "ModuleLoader",
    "DependencyManager",
]
