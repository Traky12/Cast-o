"""
CASTÚO-SYSTEM™ — Permission checks (RBAC)
Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §3.1 (matriz de permisos)

admin_general has full access (*) — all check_permission calls return True.
Identities (emails, UIDs) are NOT stored here; they come from IdP / .env at runtime.
"""
from __future__ import annotations

from backend.auth_roles import Role

# Permission matrix — extend as endpoints are added.
# Format: role → set of "resource:action" strings. "*" = full access.
_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.ADMIN_GENERAL: frozenset({"*"}),
    Role.ADMIN_CTAEX: frozenset({
        "users:read", "users:write",
        "audit:read",
        "config:read", "config:write",
        "reports:read",
    }),
    Role.TECHNICIAN: frozenset({
        "config:read", "config:write",
        "logs:read",
        "maintenance:read", "maintenance:write",
        "health:read",
    }),
    Role.AUDITOR: frozenset({
        "audit:read",
        "reports:read",
        "logs:read",
        "health:read",
    }),
    Role.BASIC_USER: frozenset({
        "data:read",
        "health:read",
    }),
}


def check_permission(role: Role, permission: str) -> bool:
    """
    Returns True if role has the given permission.
    admin_general always returns True (*).

    Permission format: "resource:action" (e.g. "audit:read", "config:write").
    """
    perms = _PERMISSIONS.get(role, frozenset())
    return "*" in perms or permission in perms


def assert_permission(role: Role, permission: str) -> None:
    """
    Raises PermissionError if role lacks permission.
    Convenience wrapper for non-FastAPI code paths.
    """
    if not check_permission(role, permission):
        raise PermissionError(
            f"Role '{role.value}' does not have permission '{permission}'"
        )
