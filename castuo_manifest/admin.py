"""Perfil administrador general — overrides CASTUO_ADMIN_* en despliegue."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default).strip() or default


@dataclass(frozen=True)
class AdminProfile:
    name: str = field(default_factory=lambda: _env("CASTUO_ADMIN_NAME", "Gregorio Jiménez"))
    email: str = field(
        default_factory=lambda: _env("CASTUO_ADMIN_EMAIL", "gregorio.jimenez.proyectos@email.com")
    )
    phone: str = field(default_factory=lambda: _env("CASTUO_ADMIN_PHONE", "+34 600 000 000"))
    location: str = field(
        default_factory=lambda: _env("CASTUO_ADMIN_LOCATION", "Membrío, Cáceres, España")
    )
    role: str = "Administrador General"
    permissions: tuple[str, ...] = ("all",)

    def get_profile(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "role": self.role,
            "permissions": list(self.permissions),
        }
