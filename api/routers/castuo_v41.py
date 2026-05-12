import logging
import os
import secrets
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["Castuo-v4.1"])
logger = logging.getLogger(__name__)


class ThingsDataPayload(BaseModel):
    device_id: str
    data: dict[str, Any]
    metadata: dict[str, Any] | None = None


async def verify_webhook_secret(
    x_webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> None:
    webhook_secret = os.getenv("WEBHOOK_SECRET", "").strip()
    runtime_env = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()

    if not webhook_secret:
        if runtime_env == "production":
            raise HTTPException(
                status_code=500,
                detail="WEBHOOK_SECRET is required in production",
            )
        logger.warning(
            "WEBHOOK_SECRET not configured; ThingsData ingest endpoint runs without secret validation",
        )
        return
    if not x_webhook_secret or not secrets.compare_digest(x_webhook_secret, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")


@router.get("/system/health")
async def system_health() -> dict[str, str]:
    return {
        "status": "operational",
        "engine": "Castuo-v4.1",
        "location": "Hetzner-EU",
    }


@router.post("/thingsdata/ingest")
async def ingest_thingsdata(
    payload: ThingsDataPayload,
    _auth: None = Depends(verify_webhook_secret),
) -> dict[str, str]:
    logger.info("ThingsData ingestion accepted for device_id=%s", payload.device_id)
    return {"status": "success", "received": payload.device_id}
