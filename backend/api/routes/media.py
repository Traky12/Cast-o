# backend/api/routes/media.py
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from ..security.keycloak import TokenData, get_current_user, require_owner
from ..services.media_service import media_service

router = APIRouter(tags=["media"])


@router.post("/generate-educational-video", dependencies=[Depends(require_owner)])
async def generate_educational_video(
    request: Request,
    prompt: str,
    style: str = "realistic",
    resolution: str = "1080p",
    duration: int = 30,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Genera un vídeo educativo sobre gestión forestal.
    Requiere JWT válido, rol 'owner' y consentimiento para generación de media (GDPR Art. 6.1(a)).
    """
    request.state.user = {
        "sub": current_user.sub,
        "email": current_user.email,
        "roles": current_user.roles,
        "token_id": current_user.token_id,
        "compliance": current_user.compliance,
    }
    try:
        result = await media_service.generate_educational_video(
            request=request,
            prompt=prompt,
            style=style,
            resolution=resolution,
            duration=duration,
            token_id=current_user.token_id or 0,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando vídeo: {e}",
        ) from e
