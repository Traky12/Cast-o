# -*- coding: utf-8 -*-
"""Core SABIONDA: registro de agentes, cuentas Pro y validación de contenido."""
from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

from backend.models.agent import CustomAgent
from backend.models.permissions import ROLE_PERMISSIONS

if TYPE_CHECKING:
    from backend.models.pro_account import ProAccount


class SabiondaMaster:
    """Registra agentes personalizables, cuentas Pro y valida contenido."""

    def __init__(self) -> None:
        self.agents: Dict[str, CustomAgent] = {}
        self.pro_accounts: Dict[str, "ProAccount"] = {}

    def register_pro_account(self, account: "ProAccount") -> str:
        """Registra una cuenta Pro en el sistema."""
        self.pro_accounts[account.account_id] = account
        return f"Cuenta Pro {account.account_id} registrada."

    def get_user_permissions(self, user_id: str) -> Dict[str, Any]:
        """Obtiene los permisos de un usuario en todas sus cuentas Pro."""
        perms: Dict[str, Any] = {}
        for account in self.pro_accounts.values():
            for member in account.members:
                if member.user_id == user_id:
                    perms[account.account_id] = ROLE_PERMISSIONS.get(
                        member.role, {}
                    )
                    break
        return perms

    def validate_content(self, account_id: str, content: Dict[str, Any]) -> bool:
        """Valida contenido según las restricciones de la cuenta Pro."""
        if account_id not in self.pro_accounts:
            return False
        from backend.services.content_moderator import ContentModerator

        account = self.pro_accounts[account_id]
        owner = account.owner
        if not owner:
            return False
        moderator = ContentModerator(owner.restrictions)
        for key, value in content.items():
            if isinstance(value, str):
                ok, _ = moderator.moderate_text(value)
                if not ok:
                    return False
        return True

    def register_agent(self, agent: CustomAgent) -> str:
        """Registra un agente personalizable en el sistema."""
        self.agents[agent.agent_id] = agent
        return f"Agente {agent.name} ({agent.agent_id}) registrado."

    def get_agent_response(
        self,
        agent_id: str,
        user_input: str,
        user_profile: Dict[str, Any],
    ) -> str:
        """Genera una respuesta adaptada al usuario y perfil del agente."""
        if agent_id not in self.agents:
            return "Agente no encontrado."

        agent = self.agents[agent_id]
        personality = agent.personality or {}
        ethics = agent.ethics

        response = f"""
[Respuesta de {agent.name} (v{agent.version})]
- Tipo: {agent.type}
- Ética: Equidad={getattr(ethics, 'equity', 1.0)}, Igualdad={getattr(ethics, 'equality', 1.0)}
- Personalidad: {personality}

{user_input} → [Respuesta adaptada según tu perfil]
"""
        return response.strip()


_master_instance: "SabiondaMaster | None" = None


def get_sabionda_master() -> SabiondaMaster:
    """Instancia única de SabiondaMaster (agentes + cuentas Pro)."""
    global _master_instance
    if _master_instance is None:
        _master_instance = SabiondaMaster()
    return _master_instance
