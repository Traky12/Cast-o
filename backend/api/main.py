# backend/api/main.py
from datetime import datetime, timezone
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .routes import consents, media
from .routes import admin
from .routes import compliance_audit
from .security.audit import audit_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CASTÚO-SYSTEM™ API (EU/OSS)",
    description="Backend para gestión forestal con cumplimiento GDPR, Ley 3/2023 y AI Act",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://dashboard.castuo-system.eu"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith(("/api/docs", "/api/redoc", "/openapi.json")):
        try:
            await audit_logger.log_event(
                request=request,
                event_type="http_request",
                data={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "user_agent": request.headers.get("user-agent", ""),
                },
                compliance={"gdpr": ["Art. 30"], "iso_27001": ["A.12.4.1"]},
            )
        except Exception as e:
            logger.debug("Audit log skip: %s", e)
    return response


app.include_router(consents.router, prefix="/api/consents")
app.include_router(media.router, prefix="/api/media")
app.include_router(admin.router)
app.include_router(compliance_audit.router)


@app.get("/")
def root():
    return {"message": "CASTÚO Consent API LIVE - GDPR/AEPD Ready"}


@app.get("/api/health")
async def health_check():
    rotation_status = {}
    try:
        from .services.key_rotation import KeyRotationService
        svc = KeyRotationService()
        rotation_status = svc.get_rotation_status()
    except Exception as e:
        logger.debug("Rotation status skip: %s", e)
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "rotation_status": rotation_status,
        "compliance": {
            "gdpr": "Art. 32 (seguridad del tratamiento)",
            "iso_27001": "A.13.1.1 (gestión de vulnerabilidades)",
            "ley_3_2023": "Art. 20 (procedimientos de emergencia)",
        },
    }
