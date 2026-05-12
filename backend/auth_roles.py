"""
CASTÚO-SYSTEM™ — Bearer token auth + role resolution
Ref: PRONTUARIO-LEGAL-MAESTRO-ROBOTICS-2026.md §3 (roles) + Prontuario Secrets §1

Tokens are OPAQUE bearers resolved via read_secret() — never plain env in prod.
  Option A: CASTUO_ADMIN_GENERAL_BEARER_FILE=/run/secrets/castuo_admin_general_bearer
  Option B: Vault KV v2 path castuo/admin_general/bearer

Roles defined in Prontuario cifrado §3.1:
  admin_general, admin_ctaex, technician, auditor, basic_user

FastAPI usage:
    from backend.auth_roles import Role, require_role
    @router.get("/admin/action")
    async def action(role: Role = Depends(require_role(Role.ADMIN_GENERAL))):
        ...
"""
from __future__ import annotations

from enum import Enum
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.security.vault import read_secret

_bearer_scheme = HTTPBearer(auto_error=False)


# ─── Roles ────────────────────────────────────────────────────────────────────

class Role(str, Enum):
    ADMIN_GENERAL = "admin_general"   # Gobierno global — acceso total (*)
    ADMIN_CTAEX   = "admin_ctaex"     # Ámbito CTAEX: usuarios, auditoría, config
    TECHNICIAN    = "technician"      # Config técnica, logs, mantenimiento
    AUDITOR       = "auditor"         # Lectura e informes; sin mutación sensible
    BASIC_USER    = "basic_user"      # Datos no sensibles o según matriz publicada


# Map role → secret name resolved via read_secret() (Option A or B)
# Secret names align with VAULT_KV_PATHS.md and Docker secret basenames.
_ROLE_SECRET: dict[Role, str] = {
    Role.ADMIN_GENERAL: "CASTUO_ADMIN_GENERAL_BEARER",
    Role.ADMIN_CTAEX:   "CASTUO_ADMIN_CTAEX_BEARER",
    Role.TECHNICIAN:    "CASTUO_TECHNICIAN_BEARER",
    Role.AUDITOR:       "CASTUO_AUDITOR_BEARER",
    # BASIC_USER: no bearer required (public or session-scoped)
}


def _resolve_bearer(role: Role) -> str:
    """Read the expected bearer token for a role. Returns "" if not configured."""
    secret_name = _ROLE_SECRET.get(role, "")
    return read_secret(secret_name) if secret_name else ""


# ─── FastAPI dependency factory ───────────────────────────────────────────────

def require_role(required_role: Role) -> Callable:
    """
    FastAPI dependency factory.
    Usage: Depends(require_role(Role.ADMIN_GENERAL))

    Raises:
        401 — missing Authorization header
        503 — role token not configured in this deployment
        403 — token doesn't match
    """
    def _verify(
        credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    ) -> Role:
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        expected = _resolve_bearer(required_role)
        if not expected:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Role '{required_role.value}' token not configured — set {_ROLE_SECRET.get(required_role, '')}_FILE",
            )
        # Use constant-time comparison to prevent timing attacks
        import hmac
        if not hmac.compare_digest(credentials.credentials, expected):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return required_role

    return _verify


# ─── Robotics Lab bearer (separate token, narrower scope) ────────────────────

def verify_robotics_lab_bearer(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
) -> bool:
    """
    Verify the Robotics Lab bearer token.
    Ref: Prontuario §1 — CASTUO_ROBOTICS_LAB_BEARER_TOKEN_FILE
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Authorization header required")
    expected = read_secret("CASTUO_ROBOTICS_LAB_BEARER_TOKEN")
    if not expected:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Robotics lab token not configured")
    import hmac
    if not hmac.compare_digest(credentials.credentials, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid robotics lab token")
    return True
