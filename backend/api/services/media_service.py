# backend/api/services/media_service.py
"""Wrapper de generación de media EU/OSS (Stable Diffusion, SadTalker, AnimateDiff)."""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request, status

from ..security.audit import audit_logger
from ..security.policies import policy_checker
from ..security.vault import vault

logger = logging.getLogger(__name__)

STABLE_DIFFUSION_EU_URL = os.getenv("STABLE_DIFFUSION_EU_URL", "http://sd-eu:7860")
SADTALKER_EU_URL = os.getenv("SADTALKER_EU_URL", "http://sadtalker-eu:8000")
ANIMATEDIFF_EU_URL = os.getenv("ANIMATEDIFF_EU_URL", "http://animatediff-eu:7861")

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False


class MediaService:
    def __init__(self) -> None:
        self.stable_diffusion_url = STABLE_DIFFUSION_EU_URL
        self.sadtalker_url = SADTALKER_EU_URL
        self.animatediff_url = ANIMATEDIFF_EU_URL

    @staticmethod
    def _sanitize_prompt(prompt: str) -> str:
        """Sanitiza el prompt para evitar inyecciones."""
        if not prompt or not isinstance(prompt, str):
            return ""
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.:;()")
        return "".join(c for c in prompt.strip() if c in allowed or c.isspace())[:4000]

    async def _register_media_in_blockchain(
        self,
        request: Request,
        media_type: str,
        prompt: str,
        result: Dict[str, Any],
        compliance: Dict[str, Any],
    ) -> str:
        """Registra el media en GaiaChain para auditoría."""
        user = getattr(request.state, "user", None) or {}
        token_id = user.get("token_id") or 0
        if isinstance(token_id, str) and token_id.isdigit():
            token_id = int(token_id)

        try:
            from .gaiachain import GaiaChainService

            gaiachain = GaiaChainService()
            tx_hash = await gaiachain.register_event(
                token_id=token_id,
                action_type=f"media_generation_{media_type}",
                status="registered",
                ipfs_cid="pending",
                norms=["GDPR:6.1(a)", "GDPR:30", "AI_Act:52", "Ley_3_2023:18", "ISO_27001:A.12.4.1"],
                legal_basis=compliance,
            )
            return tx_hash or "0xfallback"
        except Exception as e:
            logger.error("Error registrando media en GaiaChain: %s", e)
            return "fallback-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")

    async def generate_educational_video(
        self,
        request: Request,
        prompt: str,
        style: str = "realistic",
        resolution: str = "1080p",
        duration: int = 30,
        token_id: int = 0,
    ) -> Dict[str, Any]:
        """
        Genera vídeo educativo con Stable Diffusion EU (sandbox).
        Cumple GDPR Art. 6.1(a), AI Act Art. 52, Ley 3/2023 Art. 18.
        """
        user = getattr(request.state, "user", None) or {}

        if not user.get("compliance", {}).get("media_generation", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Consentimiento para generación de media no otorgado (GDPR Art. 6.1(a))",
            )

        if not policy_checker.check_media_access(user.get("roles", []), "educational_video"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado a generación de media (ISO 27001 A.9.1.1)",
            )

        sanitized_prompt = self._sanitize_prompt(prompt)
        payload = {
            "prompt": sanitized_prompt,
            "style": style,
            "resolution": resolution,
            "steps": 50,
            "compliance": {
                "gdpr": "EU_hosted",
                "ai_act": "transparency_provided",
                "ley_3_2023": "educational_content",
            },
            "metadata": {
                "token_id": token_id,
                "user_id": user.get("sub", "unknown"),
                "source": "CASTÚO-SYSTEM™",
                "purpose": "Educación forestal",
            },
        }

        try:
            if not _HAS_HTTPX:
                gaiachain_tx = await self._register_media_in_blockchain(
                    request, "educational_video", sanitized_prompt,
                    {"media_id": f"sd-eu-mock-{token_id}", "url": "", "thumbnail": ""},
                    payload["compliance"],
                )
                await audit_logger.log_event(
                    request,
                    "media_generation_educational",
                    {"media_id": "sd-eu-mock", "prompt": sanitized_prompt[:200], "gaiachain_tx": gaiachain_tx},
                    {"gdpr": ["Art. 6.1(a)", "Art. 30"], "ai_act": ["Art. 52"], "ley_3_2023": ["Art. 18"], "iso_27001": ["A.12.4.1"]},
                )
                return {
                    "status": "success",
                    "media": {
                        "media_id": f"sd-eu-mock-{token_id}",
                        "url": "",
                        "thumbnail": "",
                        "compliance": {"evidence": {"gaiachain_tx": gaiachain_tx, "hosting": "OVH Francia (GDPR compliant)", "license": "EUPL-1.2"}},
                    },
                }

            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.stable_diffusion_url.rstrip('/')}/sdapi/v1/txt2img",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

            gaiachain_tx = await self._register_media_in_blockchain(
                request, "educational_video", sanitized_prompt, result, payload["compliance"],
            )
            await audit_logger.log_event(
                request,
                "media_generation_educational",
                {
                    "media_id": result.get("media_id", "unknown"),
                    "prompt": sanitized_prompt[:200],
                    "gaiachain_tx": gaiachain_tx,
                    "user": user,
                },
                {"gdpr": ["Art. 6.1(a)", "Art. 30"], "ai_act": ["Art. 52"], "ley_3_2023": ["Art. 18"], "iso_27001": ["A.12.4.1"]},
            )

            return {
                "status": "success",
                "media": {
                    "media_id": result.get("media_id", "sd-eu-unknown"),
                    "url": result.get("url", ""),
                    "thumbnail": result.get("thumbnail", ""),
                    "compliance": {
                        "evidence": {
                            "gaiachain_tx": gaiachain_tx,
                            "hosting": "OVH Francia (GDPR compliant)",
                            "license": "EUPL-1.2",
                        }
                    },
                },
            }
        except httpx.HTTPError as e:
            logger.error("Media generation error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error generando media: {e}",
            ) from e
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor",
            ) from e


media_service = MediaService()
