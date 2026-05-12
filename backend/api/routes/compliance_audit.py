from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..services.gaiachain_service import get_audit_trail_from_chain
from ..security.keycloak import get_current_user


router = APIRouter(prefix="/api/compliance", tags=["compliance"])


@router.get("/audit/latest")
async def compliance_audit_latest(
    tokenId: int = Query(default=0, ge=0),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Optional[Dict[str, Any]]:
    """
    Devuelve el evento de auditoría más reciente para un tokenId en GaiaChain.

    Seguridad: requiere un rol con permisos de auditoría (owner/dpo/admin).
    """
    def _roles_of(user: Any) -> set[str]:
        roles = getattr(user, "roles", None)
        if roles is None and hasattr(user, "get"):
            roles = user.get("roles")
        return {str(r) for r in (roles or [])}

    try:
        roles = _roles_of(current_user)
        if not ({"owner", "dpo", "admin"} & roles):
            raise HTTPException(status_code=403, detail="No autorizado")

        trail = get_audit_trail_from_chain(token_id=tokenId)
        if not trail:
            return None
        return trail[-1]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error en compliance_audit_latest: {exc}")

