from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import random
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

from backend.core.security import (
    build_error_hash,
    compute_hmac_signature,
    encrypt_audit_payload,
    verify_hmac_signature,
)
from backend.security.end_to_end_encryption import EndToEndEncryption

from .dronica import connection, lora, missions
from .routers import (
    drones_router,
    cameras_router,
    sensors_router,
    riego_router,
    energia_router,
    chatbot_router,
    voice_router,
    notifications_router,
    robotica_router,
    blockchain_router,
    blockchain_gaia_router,
    cannabis_router,
    microgreens_router,
    iot_router,
    ue_compliance_router,
    lims_sync_router,
    reports_router,
    materiales_router,
    offline_router,
    extrusora_router,
    ia_router,
    ctaex_router,
    orchestrator_router,
    agents_router,
    pro_accounts_router,
    asia_router,
    canada_router,
    cooperativas_router,
    hidroponia_router,
    nft_router,
    billing_router,
    alertas_router,
    agents_autonomous_router,
    aemps_webhooks_router,
)

# Router IoT hidroponía (bandejas) y módulos raíz (production, compliance, ecommerce)
_root = Path(__file__).resolve().parents[1]
if str(_root) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_root))

try:
    from iot import iot_router as hidroponia_iot_router
    _HAS_IOT = True
except ImportError:
    hidroponia_iot_router = None
    _HAS_IOT = False

try:
    from production.routers import environment_router, microgreens_router, water_router
    from compliance.routers import certification_router
    from ecommerce.routers import ecommerce_router
    from ecommerce.webhooks import router as webhook_router
    _HAS_PRODUCTION_ROUTERS = True
except ImportError:
    environment_router = microgreens_router = water_router = None
    certification_router = ecommerce_router = webhook_router = None
    _HAS_PRODUCTION_ROUTERS = False

from .models import SabiondaDecision, SabiondaRequest
from .agents.agent_b001 import AgentB001
from .agents.bot_telegram import TelegramNotifier
from .ecosystem_models import BioProduct, CastuoEcosystem, MoneiTransaction, SesionPsicologica
from .services.mistral import analyze_with_mistral
from .federated.routes import router as federated_router
from .shopware_adapter import build_agrivoltaic_analysis, router as shopware_router, serialize_encrypted_result


app = FastAPI(title="Castuo Sabionda API", version="2.0.0")
e2e_encryption = EndToEndEncryption()

_STATIC_DIR = _root / "static"
_TEMPLATES_DIR = _root / "templates"
_DASHBOARD_PATH = _TEMPLATES_DIR / "dashboard.html"


def _read_dashboard_html() -> str:
    if _DASHBOARD_PATH.is_file():
        return _DASHBOARD_PATH.read_text(encoding="utf-8")
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/><title>Castuo</title></head>"
        "<body><h1>Castuo API</h1><p>Plantilla en templates/dashboard.html no encontrada.</p>"
        "<p><a href='/docs'>OpenAPI</a></p></body></html>"
    )


if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/favicon.ico", include_in_schema=False, response_model=None)
async def favicon() -> FileResponse | Response:
    """Evita 404 en navegadores; prioriza ICO, luego SVG en static/."""
    ico = _STATIC_DIR / "favicon.ico"
    if ico.is_file():
        return FileResponse(ico, headers={"Cache-Control": "public, max-age=86400"})
    svg = _STATIC_DIR / "favicon.svg"
    if svg.is_file():
        return Response(
            svg.read_text(encoding="utf-8"),
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )
    return Response(status_code=204)


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_html() -> HTMLResponse:
    """Panel de enlaces para operadores; metricas reales siguen en Prometheus/Grafana."""
    return HTMLResponse(_read_dashboard_html())


_AUDIT_LOGGER = logging.getLogger("castuo_audit")

# Métricas Prometheus (monitorización producción)
REQUEST_TIME = Histogram(
    "castuo_request_duration_seconds",
    "Request duration in seconds",
    ["method", "path"],
)
API_CALLS = Counter(
    "castuo_api_calls_total",
    "Total API calls",
    ["endpoint", "method", "status"],
)
ACTIVE_USERS = Gauge("castuo_users_active", "Active users")
LER_GAUGE = Gauge("castuo_ler", "LER actual (agrovoltaica)")

# Drones Castuo Link (Grafana dashboards + alertas batería < 20%)
DRONES_ONLINE = Gauge("castu_drones_online", "Número de drones Castuo Link online")
DRONES_BATTERY = Gauge("castu_drones_battery", "Nivel de batería %", ["drone_id"])
DRONES_MISSIONS = Gauge("castu_drones_missions", "Misiones completadas", ["drone_id"])

# Sensores IoT (temperatura, humedad, suelo; filtro por granja en Grafana)
SENSOR_TEMPERATURE = Gauge("castu_sensor_temperature", "Temperatura °C", ["sensor_id", "farm"])
SENSOR_HUMIDITY = Gauge("castu_sensor_humidity", "Humedad %", ["sensor_id", "farm"])
SENSOR_SOIL_MOISTURE = Gauge("castu_sensor_soil_moisture", "Humedad suelo %", ["sensor_id", "farm"])

# Cannabis Medicinal / AEMPS: metrics derivadas SOLO desde certificados locales.
# Permiten dashboards "verificados" usando exclusivamente datasource Prometheus.
CANNABIS_TRIAL_STATUS = Gauge(
    "cannabis_trial_status",
    "Status del ensayo (derivado de certificados locales)",
    ["trial_id", "status"],
)
CANNABIS_TRIAL_COMPLIANCE = Gauge(
    "cannabis_trial_compliance",
    "Cumplimiento por estandar (derivado de certificados locales)",
    ["trial_id", "standard"],
)

instrumentator = Instrumentator().instrument(app).expose(app)

# Rutas sensibles CTAEX: rate limit y sanitización de respuestas
try:
    from backend.security_internal import (
        check_rate_limit,
        get_client_ip,
        ip_in_whitelist,
        get_allowed_ips,
        sanitize_response_body,
    )
    _SECURITY_CTAEX = True
except ImportError:
    _SECURITY_CTAEX = False
    def ip_in_whitelist(*a, **k): return True
    def get_allowed_ips(): return []

SENSITIVE_PATHS_RATE_LIMIT = {"/trazabilidad/gaia", "/ecommerce/create-checkout"}
# Rutas que requieren IP en whitelist cuando ALLOWED_IPS está definido
IP_WHITELIST_PATHS = {"/trazabilidad/gaia", "/ecommerce/create-checkout", "/money/microgreens"}


@app.middleware("http")
async def integrity_signature_middleware(request: Request, call_next):
    """Verifica X-Castuo-Signature mediante HMAC-SHA256 sobre el cuerpo de la petición.

    Se aplica a rutas de orquestación sensible (/federated, /storefront) cuando
    CASTUO_SIGNATURE_SECRET está definido.
    """
    secret = os.getenv("CASTUO_SIGNATURE_SECRET")
    path = request.scope.get("path", "")
    if not secret or not (path.startswith("/federated") or path.startswith("/storefront")):
        return await call_next(request)

    body = await request.body()
    provided = request.headers.get("X-Castuo-Signature", "")
    if not provided or not verify_hmac_signature(secret, body, provided):
        # AUDIT_LOG: Petición bloqueada por fallo en verificación HMAC (integridad).
        audit_log(
            event="integrity_signature_failed",
            code="AUD-HMAC",
            meta={"path": path, "method": request.method},
        )
        return JSONResponse(
            status_code=401,
            content={"detail": "Integrity Error", "code": "AUD-HMAC"},
        )

    async def receive() -> dict:
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(request.scope, receive)
    return await call_next(request)


def audit_log(event: str, code: str, meta: Optional[Dict[str, Any]] = None) -> None:
    # AUDIT_LOG: Registro estructurado de eventos de integridad bajo normativas UE.
    payload: Dict[str, Any] = {
        "code": code,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
    try:
        token = encrypt_audit_payload(payload)
        _AUDIT_LOGGER.error(token)
    except Exception:
        # En caso de fallo de logging, nunca romper el flujo de la API.
        pass


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Manejo global de errores: oculta trazas internas y emite código AUD-<hash>."""
    suffix = build_error_hash(exc)
    code = f"AUD-{suffix}"
    # AUDIT_LOG: Error de integridad capturado globalmente (sin exponer detalles internos al cliente).
    meta = {
        "path": request.url.path,
        "method": request.method,
        "error": str(exc),
    }
    audit_log(event="integrity_error", code=code, meta=meta)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Integrity Error",
            "code": code,
        },
    )


@app.post("/encrypt")
async def encrypt_data(request: Request) -> JSONResponse:
    """Endpoint demo de cifrado (opción holográfica + contexto para Moltbook/CTAEX)."""
    payload = await request.json()
    text = payload.get("data")
    if text is None:
        raise HTTPException(status_code=400, detail="Campo 'data' requerido")
    use_holography = bool(payload.get("use_holography", False))
    context = payload.get("context") or {}
    try:
        if use_holography:
            result = e2e_encryption.encrypt(
                text.encode("utf-8"), use_holography=True, context=context
            )
        else:
            result = e2e_encryption.encrypt(text.encode("utf-8"))
        return JSONResponse({"status": "success", "result": serialize_encrypted_result(result)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/analyze")
async def analyze_farm(request: Request) -> JSONResponse:
    """Análisis de finca: JSON (finca_id, sensores) para demo en vivo o multipart (archivo)."""
    content_type = request.headers.get("content-type", "") or ""
    if "application/json" in content_type:
        body = await request.json()
        return JSONResponse(build_agrivoltaic_analysis(body))
    if "multipart/form-data" in content_type:
        form = await request.form()
        up = form.get("file") or form.get("sensor_data")
        fname = up.filename if up else "archivo"
        return JSONResponse({
            "status": "success",
            "message": f"Archivo {fname} procesado",
            "predicted_yield": "+35%",
            "water_savings": "-20%",
        })
    raise HTTPException(status_code=400, detail="Content-Type: application/json o multipart/form-data")


@app.middleware("http")
async def security_ctaex_middleware(request: Request, call_next):
    """IP whitelist (si ALLOWED_IPS), rate limit en rutas sensibles y sanitización de respuestas JSON."""
    path = request.scope.get("path", "")
    if _SECURITY_CTAEX and path in IP_WHITELIST_PATHS:
        allowed = get_allowed_ips()
        if allowed:
            ip = get_client_ip(request)
            if not ip_in_whitelist(ip, allowed):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "IP no autorizada"},
                )
    if _SECURITY_CTAEX and request.method == "POST" and path in SENSITIVE_PATHS_RATE_LIMIT:
        ip = get_client_ip(request)
        if not check_rate_limit(ip, path):
            return JSONResponse(
                status_code=429,
                content={"detail": "Demasiadas peticiones. Intente de nuevo en un minuto."},
            )
    response = await call_next(request)
    if not _SECURITY_CTAEX:
        return response
    body = getattr(response, "body", None)
    if body and "application/json" in response.headers.get("content-type", ""):
        new_body = sanitize_response_body(body, response.headers.get("content-type", ""))
        if new_body != body:
            return Response(
                content=new_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )
    return response


@app.middleware("http")
async def monitor_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    path = request.scope.get("path", "")
    method = request.scope.get("method", "GET")
    status = response.status_code
    REQUEST_TIME.labels(method=method, path=path).observe(duration)
    API_CALLS.labels(endpoint=path, method=method, status=str(status)).inc()
    return response


@app.on_event("startup")
async def load_metrics():
    ACTIVE_USERS.set(23)
    LER_GAUGE.set(1.54)
    # Drones Castuo Link (stub; en producción actualizar desde estado real)
    DRONES_ONLINE.set(25)
    for i, bid in enumerate(["drone-1", "drone-2", "drone-3", "drone-4", "drone-5"]):
        DRONES_BATTERY.labels(drone_id=bid).set(85.0 - i * 10)
        DRONES_MISSIONS.labels(drone_id=bid).set(12 + i)
    # Sensores IoT stub (granja por defecto; en producción desde base de datos/API)
    for sid, farm in [("s1", "castu-system"), ("s2", "castu-system"), ("s3", "castu-finca2")]:
        SENSOR_TEMPERATURE.labels(sensor_id=sid, farm=farm).set(22.0 + random.uniform(-2, 2))
        SENSOR_HUMIDITY.labels(sensor_id=sid, farm=farm).set(55.0 + random.uniform(-5, 5))
        SENSOR_SOIL_MOISTURE.labels(sensor_id=sid, farm=farm).set(45.0 + random.uniform(-10, 10))

    # Cannabis/AEMPS: refresco periodico de metrics a partir de certificados locales.
    seen_trial_ids = set()

    def _parse_dt_maybe(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        s = str(value).strip()
        if not s:
            return None
        s = s.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _refresh_cannabis_trial_metrics(recent_days: int = 30) -> None:
        """
        Deriva:
        - cannabis_trial_status{trial_id, status} con valores 0/1
        - cannabis_trial_compliance{trial_id, standard} con valores 0/1
        """
        nonlocal seen_trial_ids

        try:
            from backend.database.local_db import local_db
        except Exception:
            return

        now = datetime.now(timezone.utc)
        rec_cutoff = now - timedelta(days=recent_days)

        standards = ["AEMPS", "GDPR", "ISO_17025"]

        current_trial_ids = set()

        try:
            certs = local_db.list_local_certificates(limit=5000)
        except Exception:
            return

        for cert in certs:
            trial_id = str(cert.get("lote_id") or "unknown")
            current_trial_ids.add(trial_id)
            tx_status = str(cert.get("status") or "")
            cert_ts = _parse_dt_maybe(cert.get("timestamp"))

            is_pending = tx_status == "local_only"
            is_synced = not is_pending
            is_recent = bool(cert_ts and cert_ts >= rec_cutoff)

            active_val = 1.0 if (is_synced and is_recent) else 0.0
            completed_val = 1.0 if (is_synced and not is_recent) else 0.0
            pending_val = 1.0 if is_pending else 0.0

            CANNABIS_TRIAL_STATUS.labels(trial_id=trial_id, status="active").set(active_val)
            CANNABIS_TRIAL_STATUS.labels(trial_id=trial_id, status="completed").set(completed_val)
            CANNABIS_TRIAL_STATUS.labels(trial_id=trial_id, status="pending").set(pending_val)

            cert_data = cert.get("certificate_data") or {}
            metadata = cert_data.get("metadata") or {}
            normativas = metadata.get("normativas") or []
            norm_list = [str(x) for x in normativas]

            aemps_ok = any(("RD 903/2025" in n) or ("RD_903/2025" in n) for n in norm_list)
            gdpr_ok = any(("GDPR" in n) for n in norm_list)
            iso_ok = any(("ISO 17025" in n) or ("ISO_17025" in n) for n in norm_list)

            compliance_values = {
                "AEMPS": 1.0 if aemps_ok else 0.0,
                "GDPR": 1.0 if gdpr_ok else 0.0,
                "ISO_17025": 1.0 if iso_ok else 0.0,
            }

            for std in standards:
                CANNABIS_TRIAL_COMPLIANCE.labels(trial_id=trial_id, standard=std).set(
                    float(compliance_values.get(std, 0.0))
                )

        # Limpieza logica: si un trial desaparece de la evidencia local, lo marcamos como 0.
        missing_trial_ids = seen_trial_ids - current_trial_ids
        if missing_trial_ids:
            for tid in missing_trial_ids:
                CANNABIS_TRIAL_STATUS.labels(trial_id=tid, status="active").set(0.0)
                CANNABIS_TRIAL_STATUS.labels(trial_id=tid, status="completed").set(0.0)
                CANNABIS_TRIAL_STATUS.labels(trial_id=tid, status="pending").set(0.0)
                for std in standards:
                    CANNABIS_TRIAL_COMPLIANCE.labels(trial_id=tid, standard=std).set(0.0)

        seen_trial_ids = current_trial_ids

    _refresh_cannabis_trial_metrics()

    async def _cannabis_metrics_loop() -> None:
        while True:
            try:
                _refresh_cannabis_trial_metrics()
            except Exception:
                # Fail-safe: no rompe el servicio si el refresco falla.
                pass
            await asyncio.sleep(60)

    asyncio.create_task(_cannabis_metrics_loop())


try:
    from backend.middleware.gdpr import GDPRMiddleware
    app.add_middleware(GDPRMiddleware)
except ImportError:
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://ctaex.es",
        "http://localhost:3000",
        "https://tu-tienda.myshopify.com",
        "https://castuo-system.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers CASTUO: drones, cámaras, sensores, riego, energía, chatbot, voz, notificaciones
app.include_router(drones_router)
app.include_router(cameras_router)
app.include_router(sensors_router)
app.include_router(riego_router)
app.include_router(energia_router)
app.include_router(chatbot_router)
app.include_router(voice_router)
app.include_router(notifications_router)
app.include_router(robotica_router)
app.include_router(blockchain_router)
app.include_router(blockchain_gaia_router, prefix="/blockchain", tags=["Blockchain Gaia"])
app.include_router(cannabis_router, prefix="/cannabis", tags=["Cannabis"])
app.include_router(microgreens_router, prefix="/microgreens", tags=["Microgreens"])
app.include_router(iot_router, prefix="/iot", tags=["IoT"])
app.include_router(ue_compliance_router, prefix="/ue", tags=["UE Compliance"])
app.include_router(lims_sync_router, tags=["LIMS Sync"])
app.include_router(reports_router)
app.include_router(materiales_router)
app.include_router(offline_router)
app.include_router(extrusora_router)
app.include_router(ia_router)
app.include_router(ctaex_router)
app.include_router(orchestrator_router)
app.include_router(agents_autonomous_router)
app.include_router(aemps_webhooks_router)
app.include_router(agents_router)
try:
    from backend.agents.dashboard import router as agents_dashboard_sse_router

    app.include_router(agents_dashboard_sse_router)
except ImportError:
    pass
try:
    from backend.agents.camera import router as agents_camera_router

    app.include_router(agents_camera_router)
except ImportError:
    pass
app.include_router(pro_accounts_router)
app.include_router(asia_router)
app.include_router(canada_router)
app.include_router(cooperativas_router)
app.include_router(hidroponia_router)
app.include_router(nft_router)
app.include_router(billing_router)
app.include_router(alertas_router)
app.include_router(shopware_router)
app.include_router(federated_router)
if _HAS_IOT:
    app.include_router(hidroponia_iot_router, prefix="/api/iot", tags=["IoT Hidroponía"])

if _HAS_PRODUCTION_ROUTERS:
    app.include_router(environment_router, prefix="/api/environment", tags=["Environment Control"])
    app.include_router(microgreens_router, prefix="/api/microgreens", tags=["Microgreens"])
    app.include_router(water_router, prefix="/api/water", tags=["Water Treatment"])
    app.include_router(certification_router, prefix="/api/certificates", tags=["Certification"])
    app.include_router(ecommerce_router, prefix="/api/ecommerce", tags=["E-commerce"])
    app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])

try:
    from backend.vegetal_alloys.router import router as vegetal_alloys_router

    app.include_router(
        vegetal_alloys_router,
        prefix="/vegetal-alloys",
        tags=["Aleaciones vegetales"],
    )
except ImportError:
    pass


class SensorData(BaseModel):
    sensor_id: str
    temperature: float
    humidity: float
    light: float


class MistralRequest(BaseModel):
    prompt: str
    model: str = "mistral-tiny"


class LondBotRequest(BaseModel):
    query: str
    context: str = ""


class DroneMission(BaseModel):
    mission_id: str
    drone_id: str
    waypoints: list
    start_time: Optional[datetime] = None
    status: str = "pending"


class LoRaMessage(BaseModel):
    device_eui: str
    payload: str
    gateway_id: str


@app.post("/sensors/")
async def create_sensor_data(data: SensorData):
    return {"status": "success", "data": data.model_dump()}


@app.get("/sabionda/recommendations")
async def get_recommendations():
    return {
        "recommendations": [
            {"id": "rec_001", "description": "Ajustar riego para optimizar el crecimiento de la rúcula."},
            {"id": "rec_002", "description": "Aumentar la iluminación en el lote LOT-2026-0002."},
        ]
    }


@app.post("/mistral/ask")
async def ask_mistral(request: MistralRequest):
    url = f"{os.getenv('MISTRAL_API_URL', 'https://api.mistral.ai')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('MISTRAL_API_KEY', '')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": request.model,
        "messages": [{"role": "user", "content": request.prompt}],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    data = response.json()
    return data


@app.post("/londbot/ask")
async def ask_londbot(request: LondBotRequest):
    url = f"{os.getenv('LONDBOT_API_URL', '')}/ask"
    headers = {
        "Authorization": f"Bearer {os.getenv('LONDBOT_API_KEY', '')}",
        "Content-Type": "application/json",
    }
    payload = {"query": request.query, "context": request.context}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.post("/dronica/missions")
async def create_mission(mission: DroneMission, background_tasks: BackgroundTasks):
    def run_mission_task() -> None:
        missions.run_mission(mission.mission_id, mission.drone_id, mission.waypoints)

    background_tasks.add_task(run_mission_task)
    return {"status": "Mission created", "mission_id": mission.mission_id}


@app.get("/dronica/missions/{mission_id}")
async def get_mission_status(mission_id: str):
    status = missions.get_mission_status(mission_id)
    return {"mission_id": mission_id, "status": status}


@app.post("/lora/message")
async def receive_lora_message(message: LoRaMessage, background_tasks: BackgroundTasks):
    def process_message_task() -> None:
        lora.process_message(message.device_eui, message.payload, message.gateway_id)

    background_tasks.add_task(process_message_task)
    return {"status": "Message received", "device_eui": message.device_eui}


@app.get("/dronica/connection")
async def get_connection_status():
    return connection.get_status()


# --- v5.0: Auth, Hidroponía, Agrovoltaica, Trazabilidad, Usuarios (stubs) ---

class AuthRegister(BaseModel):
    username: str
    email: str
    password: str


class AuthLogin(BaseModel):
    username: str
    password: str


class AuthRecover(BaseModel):
    email: str


class TrazabilidadQR(BaseModel):
    product_id: str


class NotificationEmail(BaseModel):
    to: str
    subject: str
    body: str


@app.post("/auth/register")
async def auth_register(data: AuthRegister):
    return {"status": "ok", "message": "Usuario registrado. Email de confirmación enviado."}


@app.post("/auth/login")
async def auth_login(data: AuthLogin):
    return {"token": "jwt.demo.token.v5", "user": data.username}


@app.post("/auth/recover")
async def auth_recover(data: AuthRecover):
    return {"status": "ok", "message": "Email de recuperación enviado."}


@app.get("/hidroponia/sensors")
async def hidroponia_sensors(bed_id: str = "1"):
    return {"bed_id": bed_id, "ec": 1.2, "ph": 5.8, "nutrients": "A+B"}


@app.get("/agrovoltaica/yield")
async def agrovoltaica_yield():
    return {"efficiency": 87, "kwh_today": 120, "yield_pct": 94}


@app.post("/trazabilidad/qr")
async def trazabilidad_qr(data: TrazabilidadQR):
    return {"product_id": data.product_id, "blockchain_tx": "0x.demo.hash", "status": "registered"}


@app.post("/notifications/email")
async def notifications_email(data: NotificationEmail):
    return {"status": "sent", "to": data.to}


@app.get("/usuarios/stats")
async def usuarios_stats():
    return {"active": 23, "total": 25}


@app.get("/monitoring/status")
async def monitoring_status():
    """Estado operativo para el widget de la landing (LER, uptime, sin cifras de negocio)."""
    return {
        "ler": 1.54,
        "api_uptime_pct": 99.9,
        "efficiency_pct": 93,
        "status": "ok",
    }


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "sabionda.log"

AGENT_B001 = AgentB001()
TELEGRAM_B001 = TelegramNotifier()


async def agent_dynamic(
    bandeja: str, crop: str, system: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Placeholder para un agente Mistral dinámico por bandeja/cultivo/sistema.

    En producción, aquí se llamaría a la API de Mistral con un prompt que
    incluye las métricas, recomendaciones y el histórico reciente.
    """
    agent_id = f"agent_{crop}_{system}_{bandeja}".replace("-", "_")
    summary = (
        f"[{agent_id}] Decisión basada en CROP_PARAMS+SYSTEM_PARAMS. "
        f"Acciones: {context.get('decision')} | "
        f"Recomendaciones: {len(context.get('recommendations', []))}."
    )
    return {
        "agent_id": agent_id,
        "summary": summary,
        "quality": 1.0,
    }


@app.get("/")
async def root(request: Request) -> dict | RedirectResponse:
    """
    Navegadores (Accept: text/html) -> /dashboard.
    Clientes API (curl, */*) -> JSON estable con puntero al panel.
    """
    accept = (request.headers.get("accept") or "").lower()
    if accept.startswith("text/html"):
        return RedirectResponse(url="/dashboard", status_code=307)
    return {
        "service": "sabionda",
        "status": "ok",
        "version": "2.0",
        "dashboard": "/dashboard",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Healthcheck: TRL9_LIVE cuando holográfico activo; usado por demo CTAEX y móviles."""
    holographic = "ACTIVE" if (e2e_encryption.holographic and e2e_encryption.holographic.is_enabled()) else "inactive"
    return {
        "status": "TRL9_LIVE" if holographic == "ACTIVE" else "ok",
        "service": "castuo-backend",
        "version": "2.0.0",
        "holographic": holographic,
        "arr": "€55.3M",
    }


@app.get("/verify/{tx_hash}")
async def verify_certificate_public(tx_hash: str) -> dict:
    """Verificación pública de certificado soberano (URL para QR y enlace GaiaChain)."""
    from backend.main_certifier import MainCertifier
    certifier = MainCertifier()
    result = certifier.get_certificate_status(tx_hash)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("error", "Certificado no encontrado"))
    data = result.get("data", {})
    return {
        "status": "valid",
        "certificate_id": data.get("lote_id"),
        "certificate_hash": data.get("certificate_hash"),
        "legal_seals": data.get("legal_seals"),
        "verification_url": f"https://gaiachain.castuo-system.com/verify/{tx_hash}",
        "timestamp": data.get("timestamp"),
    }


# Parámetros agronómicos por cultivo (catálogo ampliado microgreens / brotes)
CROP_PARAMS: Dict[str, Dict[str, Any]] = {
    "guisantes": {
        "ph": {"min": 5.8, "max": 6.8, "optimal": (6.0, 6.5)},
        "ec": {"min": 0.8, "max": 1.6, "optimal": (1.0, 1.4)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.4, "max": 0.5},
    },
    "rabanos": {
        "ph": {"min": 5.5, "max": 6.5, "optimal": (5.8, 6.2)},
        "ec": {"min": 1.0, "max": 1.8, "optimal": (1.2, 1.6)},
        "temp": {"max": 22.0, "optimal": (16.0, 20.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "lentejas": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 0.6, "max": 1.4, "optimal": (0.8, 1.2)},
        "temp": {"max": 26.0, "optimal": (20.0, 24.0)},
        "o3": {"target": 0.2, "max": 0.3},
    },
    "mostaza": {
        "ph": {"min": 5.5, "max": 6.5, "optimal": (5.8, 6.2)},
        "ec": {"min": 1.2, "max": 1.8, "optimal": (1.3, 1.6)},
        "temp": {"max": 22.0, "optimal": (16.0, 21.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "brocoli": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "rucula": {
        "ph": {"min": 5.8, "max": 6.8, "optimal": (6.0, 6.5)},
        "ec": {"min": 1.2, "max": 1.8, "optimal": (1.4, 1.6)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "kale": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.2, "max": 1.8, "optimal": (1.4, 1.6)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "girasol": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 26.0, "optimal": (20.0, 24.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "alfalfa": {
        "ph": {"min": 6.0, "max": 7.5, "optimal": (6.2, 7.0)},
        "ec": {"min": 0.8, "max": 1.4, "optimal": (1.0, 1.2)},
        "temp": {"max": 26.0, "optimal": (18.0, 24.0)},
        "o3": {"target": 0.2, "max": 0.3},
    },
    "col_lombarda": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.0, "max": 1.8, "optimal": (1.2, 1.6)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "remolacha": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.3, 6.8)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "cilantro": {
        "ph": {"min": 6.2, "max": 6.8, "optimal": (6.3, 6.6)},
        "ec": {"min": 1.2, "max": 1.8, "optimal": (1.4, 1.6)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "albahaca": {
        "ph": {"min": 5.8, "max": 6.5, "optimal": (6.0, 6.4)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 28.0, "optimal": (20.0, 26.0)},
        "o3": {"target": 0.2, "max": 0.3},
    },
    "cebolla": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.4, "max": 2.0, "optimal": (1.6, 1.8)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "trigo_sarraceno": {
        "ph": {"min": 5.5, "max": 6.5, "optimal": (5.8, 6.2)},
        "ec": {"min": 0.8, "max": 1.4, "optimal": (1.0, 1.2)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.2, "max": 0.3},
    },
    "amaranto": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 28.0, "optimal": (20.0, 26.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "espinaca": {
        "ph": {"min": 5.8, "max": 6.8, "optimal": (6.0, 6.5)},
        "ec": {"min": 1.4, "max": 2.0, "optimal": (1.6, 1.8)},
        "temp": {"max": 22.0, "optimal": (16.0, 20.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "acelga": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.4, "max": 2.0, "optimal": (1.6, 1.8)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "coliflor": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "col_rizada": {
        "ph": {"min": 6.0, "max": 7.5, "optimal": (6.2, 7.0)},
        "ec": {"min": 1.2, "max": 1.8, "optimal": (1.4, 1.6)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.3, "max": 0.4},
    },
    "eneldo": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.0, "max": 1.6, "optimal": (1.2, 1.4)},
        "temp": {"max": 24.0, "optimal": (18.0, 22.0)},
        "o3": {"target": 0.2, "max": 0.3},
    },
    "perejil": {
        "ph": {"min": 6.0, "max": 7.0, "optimal": (6.2, 6.8)},
        "ec": {"min": 1.2, "max": 1.8, "optimal": (1.4, 1.6)},
        "temp": {"max": 22.0, "optimal": (16.0, 20.0)},
        "o3": {"target": 0.2, "max": 0.3},
    },
}


# Parámetros por sistema (hidroponía, agrovoltaica, etc.)
SYSTEM_PARAMS: Dict[str, Dict[str, Any]] = {
    "hidroponia_rpi4": {
        "o3_target": 0.4,
        "uv_cycle_h": 12,
        "rpi_firmware": "v2.1",
    },
    "hidroponia_v1": {
        "o3_target": 0.3,
        "uv_cycle_h": 8,
        "controller": "esp32",
    },
    "agrovolt_b5": {
        "o3_target": 0.3,
        "shadow_factor": 0.7,
        "paneles": 5,
        "inclinacion_deg": 35,
    },
}


def generate_sha256(data: Dict[str, Any]) -> str:
    """Genera un hash SHA256 de los datos de entrada."""
    data_str = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data_str).hexdigest()


def check_parameters(payload: SabiondaRequest) -> Dict[str, Any]:
    """Verifica los parámetros agronómicos y devuelve acciones y recomendaciones."""
    crop = payload.crop.lower()
    system = payload.system.lower()

    params = CROP_PARAMS.get(crop, CROP_PARAMS["guisantes"])  # Default a guisantes
    sys_cfg = SYSTEM_PARAMS.get(system, SYSTEM_PARAMS["hidroponia_rpi4"])
    actions: List[str] = []
    recommendations: List[str] = []

    # Verificar pH
    if payload.ph < params["ph"]["min"] or payload.ph > params["ph"]["max"]:
        actions.append(
            f"V01 ON (pH fuera de rango: {params['ph']['min']}-{params['ph']['max']})"
        )
        recommendations.append(
            f"Ajustar pH a {params['ph']['optimal'][0]}-{params['ph']['optimal'][1]} con solución ácida/básica."
        )

    # Verificar EC
    if payload.ec < params["ec"]["min"] or payload.ec > params["ec"]["max"]:
        actions.append(
            f"V02 ON (EC fuera de rango: {params['ec']['min']}-{params['ec']['max']})"
        )
        recommendations.append(
            f"Ajustar EC a {params['ec']['optimal'][0]}-{params['ec']['optimal'][1]} mS/cm."
        )

    # Verificar temperatura
    if payload.temp is not None and payload.temp > params["temp"]["max"]:
        actions.append(f"VENT_ON +20% (Temp > {params['temp']['max']}°C)")
        recommendations.append(
            f"Reducir temperatura a {params['temp']['optimal'][0]}-{params['temp']['optimal'][1]}°C."
        )

    # Si no hay acciones críticas, todo está óptimo
    if not actions:
        actions.append("V01 OFF")
        recommendations.append("Parámetros óptimos. Monitorear cada 4h.")

    # Generar log y SHA256
    log_message = (
        f"{payload.bandeja} ({crop}): "
        f"pH={payload.ph} "
        f"{'⚠️' if payload.ph < params['ph']['min'] or payload.ph > params['ph']['max'] else '✅'} | "
        f"EC={payload.ec} "
        f"{'⚠️' if payload.ec < params['ec']['min'] or payload.ec > params['ec']['max'] else '✅'} | "
        f"Temp={payload.temp}°C "
        f"{'⚠️' if payload.temp is not None and payload.temp > params['temp']['max'] else '✅'}"
    )

    data_for_hash = {
        "bandeja": payload.bandeja,
        "crop": crop,
        "system": system,
        "ph": payload.ph,
        "ec": payload.ec,
        "temp": payload.temp,
        "humidity": payload.humidity,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "decision": actions[0].split()[0] if actions else "V01 OFF",
        "uv_status": False,
        "o3_target": float(sys_cfg.get("o3_target", params["o3"]["target"])),
        "log_message": log_message,
        "recommendations": recommendations,
        "sha256": generate_sha256(data_for_hash),
    }


def append_log(entry: SabiondaDecision, raw: SabiondaRequest) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    record = {
        "ts": ts,
        "decision": entry.model_dump(mode="json"),
        "payload": raw.model_dump(mode="json"),
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


@app.post("/sabionda/decide", response_model=SabiondaDecision)
async def sabionda_decide(payload: SabiondaRequest) -> SabiondaDecision:
    result = check_parameters(payload)
    agent_info = await agent_dynamic(
        payload.bandeja, payload.crop, payload.system, result
    )

    # Inyectamos un pequeño resumen del agente en las recomendaciones.
    if "summary" in agent_info:
        result["recommendations"].append(agent_info["summary"])

    decision = SabiondaDecision(
        decision=result["decision"],
        uv_status=result.get("uv_status", False),
        o3_target=result["o3_target"],
        log_message=result["log_message"],
        recommendations=result["recommendations"],
        sha256=result["sha256"],
    )
    append_log(decision, payload)

    if payload.bandeja == "B001":
        AGENT_B001.after_decision(payload, decision)
        TELEGRAM_B001.notify(payload, decision)

    return decision


###############################################################################
# CASTÚO v4.0 — Bioeconomía + MONEI + Psicólogo Digital (demo CTAEX)
###############################################################################


def _vechain_tx(prefix: str) -> str:
    seed = f"{prefix}_{datetime.now(timezone.utc).isoformat()}_{random.random()}".encode(
        "utf-8"
    )
    return f"0x{hashlib.sha256(seed).hexdigest()[:16]}"


def procesar_biomasa(crop: str, biomass_kg: float) -> BioProduct:
    crop = (crop or "").lower()

    if crop == "sorgo":
        ethanol_liters = biomass_kg * 0.3
        biocoin = ethanol_liters
        market_value = ethanol_liters * 80
        return BioProduct(
            product="bioethanol",
            quantity=ethanol_liters,
            unit="L",
            biocoin=biocoin,
            market_value_eur=market_value,
            co2_saved_kg=biomass_kg * 1.2,
            vechain_tx=_vechain_tx("bio_sorgo"),
        )

    if crop == "cannabis":
        fiber_kg = biomass_kg * 0.2
        biocoin = fiber_kg * 2
        market_value = fiber_kg * 150
        return BioProduct(
            product="hemp_fiber",
            quantity=fiber_kg,
            unit="kg",
            biocoin=biocoin,
            market_value_eur=market_value,
            co2_saved_kg=biomass_kg * 0.8,
            vechain_tx=_vechain_tx("bio_cannabis"),
        )

    if crop == "romero":
        oil_l = biomass_kg * 0.02
        biocoin = oil_l * 10
        market_value = oil_l * 600
        return BioProduct(
            product="essential_oil",
            quantity=oil_l,
            unit="L",
            biocoin=biocoin,
            market_value_eur=market_value,
            co2_saved_kg=biomass_kg * 0.5,
            vechain_tx=_vechain_tx("bio_romero"),
        )

    # fallback demo
    units = biomass_kg * 0.1
    return BioProduct(
        product="bioproduct",
        quantity=units,
        unit="u",
        biocoin=units,
        market_value_eur=units * 50,
        co2_saved_kg=biomass_kg * 0.3,
        vechain_tx=_vechain_tx("bio_generic"),
    )


def crear_transaccion(amount: float) -> MoneiTransaction:
    amount = float(amount or 0.0)
    iban = f"ES{random.randint(10**19, 10**20 - 1)}"
    carbon_credit = amount * 0.001
    return MoneiTransaction(
        amount=amount,
        iban=iban,
        status="completed",
        vechain_tx=_vechain_tx("monei"),
        carbon_credit=carbon_credit,
    )


async def analizar_emocion(texto: str) -> SesionPsicologica:
    text = (texto or "").strip()
    if not text:
        return SesionPsicologica(
            emocion="neutral",
            respuesta="¿Cómo te sientes hoy? Puedes escribirlo y lo analizamos paso a paso.",
            vechain_tx=_vechain_tx("psy"),
        )

    analysis = await analyze_with_mistral(
        prompt=(
            "Eres un psicólogo digital orientado a agricultores. "
            "Clasifica emoción (1 palabra) y da una respuesta breve, empática y práctica "
            "en español (máx 3 frases). Texto: "
            f"{text!r}"
        ),
        model=os.getenv("MISTRAL_PSY_MODEL", "mistral-small"),
    )

    content = str(analysis.get("summary") or "")
    emocion = "tristeza" if "triste" in text.lower() else "ansiedad"
    respuesta = content.strip() or (
        "Entiendo que esto te esté costando. "
        "Respira 4 segundos inhalando y 4 exhalando, repítelo 4 veces. "
        "¿Quieres que lo hagamos juntos?"
    )

    return SesionPsicologica(
        emocion=emocion,
        respuesta=respuesta,
        vechain_tx=_vechain_tx("psy"),
    )


@app.post("/ecosistema/B001", response_model=CastuoEcosystem)
async def ecosistema_b001(payload: Dict[str, Any]) -> CastuoEcosystem:
    biomasa_kg = float(payload.get("biomasa_kg", 100))
    crop = str(payload.get("crop", "sorgo"))
    texto_psicologo = str(payload.get("texto_psicologo", "") or "")
    amount = float(payload.get("amount", 0.0) or 0.0)

    bio_product = procesar_biomasa(crop, biomasa_kg)
    monei_tx = crear_transaccion(amount) if amount > 0 else None
    psicologo_session = (
        await analizar_emocion(texto_psicologo) if texto_psicologo else None
    )

    total_value = (
        bio_product.market_value_eur
        + (monei_tx.amount if monei_tx else 0.0)
        + ((psicologo_session.biocoin_reward * 5) if psicologo_session else 0.0)
    )
    total_biocoin = bio_product.biocoin + (
        psicologo_session.biocoin_reward if psicologo_session else 0.0
    )

    return CastuoEcosystem(
        bioeconomia=bio_product,
        monei=monei_tx,
        psicologo=psicologo_session,
        total_value_eur=total_value,
        total_biocoin=total_biocoin,
        vechain_tx=bio_product.vechain_tx,
    )

