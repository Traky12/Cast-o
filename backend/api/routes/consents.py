# backend/api/routes/consents.py
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from ..services.consent_service import get_consent
from models.consent_event import ConsentEvent
from ..security.keycloak import TokenData, get_current_user, require_owner

router = APIRouter(tags=["consents"])


@router.get("/{token_id}")
async def read_consent(
    token_id: str,
    _user: TokenData = Depends(require_owner),
    current_user: TokenData = Depends(get_current_user),
) -> ConsentEvent:
    if current_user.token_id is not None and str(current_user.token_id) != str(token_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes acceder a tus propios consentimientos",
        )
    raw_data = get_consent(token_id)
    safe_data = {
        "token_id": raw_data["token_id"],
        "status": raw_data["status"],
        "timestamp": raw_data["timestamp"],
        "gaiachain_tx": raw_data.get("gaiachain_tx"),
        "ipfs_cid": raw_data.get("ipfs_cid"),
        "block_number": raw_data.get("block_number"),
        "audit_trail": raw_data.get("audit_trail"),
        "error": raw_data.get("error"),
    }
    return ConsentEvent(**safe_data)


@router.post("/{token_id}/withdraw")
async def withdraw_consent(
    token_id: str,
    _user: TokenData = Depends(require_owner),
    current_user: TokenData = Depends(get_current_user),
):
    if current_user.token_id is not None and str(current_user.token_id) != str(token_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puedes retirar tus propios consentimientos",
        )
    return {
        "token_id": token_id,
        "status": "withdrawn",
        "timestamp": "2026-03-16T15:09:00Z",
    }
