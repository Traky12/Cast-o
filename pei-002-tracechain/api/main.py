"""
Microservicio STUB para ensayar envelopes PEI-002 (puerto dedicado, p. ej. 8010).

NO es el backend Castuo: la ruta real de auditoria + cadena es
  POST /api/audit/register-event en FastAPI principal + register_event_in_chain.

Autenticacion: Authorization: Bearer <PEI002_STUB_BEARER_TOKEN>
Persistencia: SQLite (PEI002_SQLITE_PATH o api/data/pei002_stub.db junto a este servicio).
"""
from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from models import ParcelAuditPayload, SigpacValidationEnvelope
from sqlite_store import init_schema, insert_envelope, insert_parcel, list_envelopes, list_parcels

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    init_schema()
    yield


app = FastAPI(
    title="PEI-002 TraceChain stub",
    version="0.1.0",
    description="Laboratorio: ingesta de envelopes SIGPAC sin explorer ni URLs inventadas.",
    lifespan=_lifespan,
)

bearer = HTTPBearer(auto_error=True)


def _expected_bearer() -> str:
    return (os.environ.get("PEI002_STUB_BEARER_TOKEN") or "").strip()


async def verify_stub_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> str:
    expected = _expected_bearer()
    if not expected:
        raise HTTPException(status_code=503, detail="PEI002_STUB_BEARER_TOKEN no configurado")
    if credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="Bearer invalido")
    return credentials.credentials


@app.post("/api/pei-002/envelope", response_model=Dict[str, Any])
def ingest_envelope(
    payload: SigpacValidationEnvelope,
    _: str = Depends(verify_stub_token),
) -> Dict[str, Any]:
    if not payload.digest.startswith("sha256:"):
        raise HTTPException(status_code=400, detail="digest debe comenzar por sha256:")
    rid = f"pei002-env-{uuid.uuid4().hex[:12]}"
    rec = {
        "id": rid,
        "received_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload.model_dump(),
    }
    insert_envelope(rec)
    logger.info("Envelope almacenado stub id=%s parcelas=%s", rid, payload.parcelas)
    return {
        "status": "received",
        "token_id": rid,
        "stub_id": rid,
        "blockchain_tx": None,
        "explorer_url": None,
        "message": "Envelope recibido en stub (laboratorio). Produccion: POST /api/audit/register-event en monolito Castuo.",
    }


@app.post("/api/pei-002/parcel", response_model=Dict[str, Any])
def ingest_parcel(
    payload: ParcelAuditPayload,
    _: str = Depends(verify_stub_token),
) -> Dict[str, Any]:
    if not payload.digest.startswith("sha256:"):
        raise HTTPException(status_code=400, detail="digest debe comenzar por sha256:")
    rid = f"pei002-parc-{payload.parcela_id}-{uuid.uuid4().hex[:8]}"
    rec = {
        "id": rid,
        "received_utc": datetime.now(timezone.utc).isoformat(),
        "payload": payload.model_dump(),
    }
    insert_parcel(rec)
    logger.info("Parcela stub id=%s parcela_id=%s", rid, payload.parcela_id)
    return {
        "status": "received",
        "token_id": rid,
        "stub_id": rid,
        "blockchain_tx": None,
        "explorer_url": None,
        "message": "Parcela recibida en stub. DPIA si parcela_id o metadatos enlazan con persona fisica.",
    }


@app.get("/api/pei-002/events/envelopes", response_model=List[Dict[str, Any]])
def list_envelopes_endpoint(_: str = Depends(verify_stub_token)) -> List[Dict[str, Any]]:
    return list_envelopes()


@app.get("/api/pei-002/events/parcels", response_model=List[Dict[str, Any]])
def list_parcels_endpoint(_: str = Depends(verify_stub_token)) -> List[Dict[str, Any]]:
    return list_parcels()


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": "pei-002-stub"}
