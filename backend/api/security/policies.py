# backend/api/security/policies.py
"""Reglas ABAC/OPA (EU/OSS). En producción integrar con Open Policy Agent."""

from typing import List


class PolicyChecker:
    def __init__(self) -> None:
        self.opa_enabled = False

    def check_media_access(self, user_roles: List[str], media_type: str) -> bool:
        """Verifica acceso a generación de media según políticas."""
        if not self.opa_enabled:
            return "owner" in user_roles

        allowed_roles = {
            "educational_video": ["owner", "dpo"],
            "technical_video": ["owner", "admin"],
            "talking_head": ["owner", "dpo"],
        }
        roles = allowed_roles.get(media_type, ["owner"])
        return any(r in user_roles for r in roles)

    def check_audit_read(self, user_roles: List[str]) -> bool:
        """Verifica acceso a logs de auditoría."""
        return "dpo" in user_roles or "admin" in user_roles or "auditor" in user_roles


policy_checker = PolicyChecker()
