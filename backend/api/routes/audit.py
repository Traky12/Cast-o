from datetime import datetime
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException

from ..services.gaiachain_service import get_audit_trail_from_chain, register_event_in_chain
from ..security.keycloak import get_current_user


router = APIRouter(prefix="/api/audit", tags=["audit"])
logger = logging.getLogger(__name__)


@router.get("/trail", response_model=List[Dict[str, Any]])
async def get_audit_trail(tokenId: int, current_user: dict = Depends(get_current_user)):
  """
  Devuelve el trail de auditoría para un token ForestOwnershipToken concreto.
  Solo accesible para el propietario o el DPO.
  """
  try:
    roles = getattr(current_user, "roles", None) or (
      current_user.get("roles") if hasattr(current_user, "get") else None
    )
    roles = {str(r) for r in (roles or [])}
    if not ({"owner", "dpo"} & roles):
      raise HTTPException(status_code=403, detail="No autorizado")
    audit_trail = get_audit_trail_from_chain(tokenId)
    for event in audit_trail:
      event["compliance"] = {
        "gdpr": "Art. 30 (Registro de actividades)",
        "iso27001": "A.12.4 (Registro de eventos)",
        "eidas": "Nivel Alto" if event.get("transactionHash") else "Nivel Sustancial",
      }
    return audit_trail
  except HTTPException:
    raise
  except Exception as exc:
    logger.error("Error obteniendo trail de auditoría para %s: %s", tokenId, exc)
    raise HTTPException(status_code=500, detail="Error obteniendo trail de auditoría")


@router.post("/register-event", response_model=Dict[str, Any])
async def register_audit_event(
  event_data: Dict[str, Any],
  current_user: dict = Depends(get_current_user),
):
  """
  Registra un evento en el contrato de auditoría de GaiaChain.
  Solo accesible para DPO o admin.
  """
  try:
    roles = getattr(current_user, "roles", None) or (
      current_user.get("roles") if hasattr(current_user, "get") else None
    )
    roles = {str(r) for r in (roles or [])}
    if not ({"dpo", "admin"} & roles):
      raise HTTPException(status_code=403, detail="Solo el DPO puede registrar eventos")
    event_data.setdefault("compliance", {})
    event_data["compliance"].update(
      {
        "gdpr": "Art. 30, 32",
        "iso27001": "A.12.4.1",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "registered_by": getattr(current_user, "sub", None)
        or (current_user.get("sub") if hasattr(current_user, "get") else None)
        or "unknown",
      }
    )
    tx_hash = register_event_in_chain(event_data)
    return {
      "status": "success",
      "transaction_hash": tx_hash,
      "compliance": event_data["compliance"],
    }
  except HTTPException:
    raise
  except Exception as exc:
    logger.error("Error registrando evento de auditoría: %s", exc)
    raise HTTPException(status_code=500, detail="Error registrando evento de auditoría")

