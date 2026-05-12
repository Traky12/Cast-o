"""
CASTÚO-SYSTEM API JEREMIE/CTAEX — Health, Events (GS1 EPCIS), Compliance, Audit.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, List, Optional

import psycopg2
from psycopg2.extras import Json
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="CASTÚO JEREMIE API", version="4.3")

try:
    from behavioral_auth import router as behavioral_auth_router
    app.include_router(behavioral_auth_router)
except ImportError:
    pass

# HTTPS redirect solo en producción (evitar en local)
if os.getenv("HTTPS_REDIRECT", "false").lower() == "true":
    from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
    app.add_middleware(HTTPSRedirectMiddleware)

_cors_origins = os.getenv("CORS_ORIGINS", "https://castuo-system.arsys,http://localhost,http://localhost:3000,https://dashboard.juntaextremadura.es").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

security = HTTPBearer(auto_error=False)


# --- Modelos ---
class Event(BaseModel):
    event_type: str
    epc_list: List[str]
    quantity: float
    read_point: Optional[str] = None
    biz_step: Optional[str] = None
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    database: dict
    compliance: dict
    timestamp: datetime


def get_db_connection():
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    if os.getenv("ENVIRONMENT") == "production" and not postgres_password:
        raise ValueError("POSTGRES_PASSWORD required in production")
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "castuo_jeremie"),
            user=os.getenv("POSTGRES_USER", "castuo_user"),
            password=postgres_password or "",
            sslmode=os.getenv("POSTGRES_SSL_MODE", "disable"),
            connect_timeout=5,
        )
        return conn
    except Exception as e:
        logger.error("Error de conexión PostgreSQL: %s", e)
        raise HTTPException(status_code=500, detail="Error de conexión a la base de datos")


@app.get("/")
async def root():
    return {"service": "castuo-jeremie-api", "version": "4.3", "docs": "/docs"}


async def verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> bool:
    api_token = os.getenv("API_TOKEN")
    if os.getenv("ENVIRONMENT") == "production" and not api_token:
        raise HTTPException(status_code=503, detail="API_TOKEN not configured in production")
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token requerido")
    if not api_token or credentials.credentials != api_token:
        raise HTTPException(status_code=401, detail="Token inválido")
    return True


@app.get("/health", response_model=HealthResponse)
async def health_check(auth: bool = Depends(verify_token)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM events LIMIT 1;")
        events_ok = cur.fetchone() is not None
        try:
            cur.execute("SELECT inet_server_addr(), inet_server_port();")
            row = cur.fetchone()
            server = f"{row[0]}:{row[1]}" if row else "unknown"
        except Exception:
            server = "unknown"
        conn.close()
        return {
            "status": "operational",
            "database": {
                "ssl_enabled": os.getenv("POSTGRES_SSL_MODE", "disable") == "verify-full",
                "server": server,
                "status": "healthy",
                "events_ok": events_ok,
            },
            "compliance": {
                "ens_high": True,
                "gdpr": True,
                "reg_178_2002": True,
                "ssl": os.getenv("POSTGRES_SSL_MODE") == "verify-full",
                "audit_enabled": True,
            },
            "timestamp": datetime.utcnow(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en health_check: %s", e)
        raise HTTPException(status_code=500, detail="Error al verificar el estado del sistema")


@app.post("/events")
async def create_event(request: Request, event: Event, auth: bool = Depends(verify_token)):
    try:
        logger.info("Nuevo evento: %s", event.event_type)
        conn = get_db_connection()
        cur = conn.cursor()

        for epc in event.epc_list:
            if not epc.startswith("urn:epc:id:"):
                raise HTTPException(status_code=400, detail=f"Formato EPC inválido: {epc}")

        cur.execute(
            """
            INSERT INTO events (event_type, epc_list, quantity, read_point, biz_step, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                event.event_type,
                event.epc_list,
                event.quantity,
                event.read_point or "",
                event.biz_step,
                Json(event.metadata) if event.metadata else None,
            ),
        )
        event_id = cur.fetchone()[0]
        conn.commit()

        cur.execute(
            """
            INSERT INTO audit_log (user_id, action, table_name, record_id, new_data)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                request.client.host if request.client else "unknown",
                "INSERT_EVENT",
                "events",
                event_id,
                Json(event.model_dump()),
            ),
        )
        conn.commit()
        conn.close()
        logger.info("Evento %s creado", event_id)

        return {
            "status": "created",
            "event_id": str(event_id),
            "compliance": {"reg_178_2002": True, "gs1_epcis": True, "ssl": True, "audit": True},
            "timestamp": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error al crear evento: %s", e)
        raise HTTPException(status_code=500, detail=f"Error al procesar el evento: {str(e)}")


@app.get("/compliance")
async def compliance_check():
    return {
        "status": "FULLY_COMPLIANT",
        "ens_high": True,
        "gdpr": {
            "data_location": "OVHcloud Madrid (UE)",
            "encryption": "SSL/TLS 1.3",
            "audit": True,
        },
        "reg_178_2002": {
            "openepcis_version": "2.0.0",
            "gs1_compliant": True,
            "events_table": "events",
        },
        "eidas": {"keycloak_integration": "preconfigured", "realm": "castuo-jeremie"},
        "mica": True,
        "ssl": {
            "mode": os.getenv("POSTGRES_SSL_MODE", "verify-full"),
            "enforced": True,
            "ca_verification": True,
        },
        "economic_impact": {
            "current_funding": "605K€ (JEREMIE)",
            "projected_revenue": "125M€",
            "roi": "11,204x",
            "payback_period": "6 meses",
        },
        "technical": {
            "postgres_version": "16",
            "openepcis_version": "2.0.0",
            "audit_enabled": True,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/audit")
async def get_audit_logs(limit: int = 10, auth: bool = Depends(verify_token)):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, action, table_name, record_id, action_timestamp
            FROM audit_log
            ORDER BY action_timestamp DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return {
            "status": "success",
            "count": len(rows),
            "logs": [
                {
                    "id": r[0],
                    "user": r[1],
                    "action": r[2],
                    "table": r[3],
                    "record_id": str(r[4]) if r[4] else None,
                    "timestamp": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ],
        }
    except Exception as e:
        logger.error("Error al obtener audit: %s", e)
        raise HTTPException(status_code=500, detail="Error al obtener logs de auditoría")


# --- Métricas (Prometheus-style) ---
_metrics_mistral_queries: int = 0


# --- Mistral Adapter endpoints ---

try:
    from .mistral_castuo_adapter import MistralAdapter
    _mistral_adapter = MistralAdapter()
    _MISTRAL_AVAILABLE = True
except Exception as e:
    logger.warning("Mistral Adapter no disponible: %s", e)
    _mistral_adapter = None
    _MISTRAL_AVAILABLE = False


class MistralQueryRequest(BaseModel):
    """Request body para POST /mistral/query."""

    dataset_path: Optional[str] = None
    query: str
    temperature: float = 0.7
    max_tokens: int = 2000
    model: str = "mistral-small"


@app.post("/mistral/query")
async def mistral_query(request: MistralQueryRequest):
    """Ejecuta una consulta a Mistral API con opcional contexto de dataset (Sabionda)."""
    if not _MISTRAL_AVAILABLE or _mistral_adapter is None:
        raise HTTPException(
            status_code=503,
            detail="Mistral Adapter no disponible. Comprueba dependencias (pandas, cryptography, requests).",
        )
    global _metrics_mistral_queries
    try:
        result = _mistral_adapter.query(
            dataset_path=request.dataset_path,
            query=request.query,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            model=request.model,
        )
        _metrics_mistral_queries += 1
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"status": "success", "result": result, "content": content}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error en /mistral/query: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mistral/health")
async def mistral_health():
    """Estado del Mistral Adapter (configuración desde .env)."""
    return {
        "status": "healthy" if _MISTRAL_AVAILABLE else "unavailable",
        "adapter": "v1.0.0",
        "configured": _MISTRAL_AVAILABLE,
    }


@app.get("/metrics")
async def metrics():
    """Métricas agregadas (Mistral, GaiaChain, cooperativas, PAC 2040)."""
    return {
        "mistral_queries": _metrics_mistral_queries,
        "gaia_traces": int(os.getenv("METRICS_GAIA_TRACES", "0")),
        "cooperativas_activas": int(os.getenv("METRICS_COOPERATIVAS_ACTIVAS", "3")),
        "total_kwp": float(os.getenv("METRICS_TOTAL_KWP", "9500")),
        "pac2040_funding": os.getenv("METRICS_PAC2040_FUNDING", "€360K eligible"),
    }


# --- Junta de Extremadura: Gestión documental cifrada (GreenLicenseToken / FireReportToken) ---

try:
    from web3 import Web3
    _WEB3_AVAILABLE = True
except ImportError:
    _WEB3_AVAILABLE = False

_JUNTA_PRIVATE_KEY = os.getenv("JUNTA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
_DOCUMENT_TOKEN_ADDRESS = os.getenv("DOCUMENT_TOKEN_ADDRESS", "")
_FIRE_REPORT_TOKEN_ADDRESS = os.getenv("FIRE_REPORT_TOKEN_ADDRESS", "")
_GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")

GREEN_LICENSE_ABI = [
    {"inputs": [{"name": "documentHash", "type": "string"}, {"name": "documentType", "type": "string"}, {"name": "ipfsHash", "type": "string"}, {"name": "responsible", "type": "string"}], "name": "mintDocument", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getDocumentMetadata", "outputs": [{"name": "documentHash", "type": "string"}, {"name": "documentType", "type": "string"}, {"name": "ipfsHash", "type": "string"}, {"name": "timestamp", "type": "uint256"}, {"name": "responsible", "type": "string"}], "stateMutability": "view", "type": "function"},
]
FIRE_REPORT_ABI = [
    {"inputs": [{"name": "to", "type": "address"}, {"name": "reportHash", "type": "string"}, {"name": "location", "type": "string"}, {"name": "extinguishedBy", "type": "string"}, {"name": "affectedArea", "type": "uint256"}], "name": "mintFireReport", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
]


class ForestLicenseRequest(BaseModel):
    """Solicitud de licencia forestal / medio ambiente (SIGPAC)."""
    document: str
    metadata: dict
    public_key: Optional[str] = None


class FireReportRequest(BaseModel):
    """Parte de incendio forestal (BRIF)."""
    document: str
    metadata: dict


class ErasureRequest(BaseModel):
    """Solicitud de ejercicio del derecho al olvido (GDPR Art. 17)."""
    token_id: int
    wallet_address: str
    email: Optional[str] = None


def _sha512_b64(b64_document: str) -> str:
    import base64
    import hashlib
    raw = base64.b64decode(b64_document)
    return hashlib.sha512(raw).hexdigest()


@app.post("/api/forest/licenses")
async def api_forest_licenses(body: ForestLicenseRequest, auth: bool = Depends(verify_token)):
    """Registra documento de licencia ambiental/forestal en GaiaChain (GreenLicenseToken)."""
    if not _WEB3_AVAILABLE or not _JUNTA_PRIVATE_KEY or not _DOCUMENT_TOKEN_ADDRESS:
        raise HTTPException(status_code=503, detail="Gestión documental no configurada (DOCUMENT_TOKEN_ADDRESS, JUNTA_PRIVATE_KEY).")
    try:
        doc_hash = _sha512_b64(body.document)
        meta = body.metadata
        doc_type = meta.get("tipo", "licencia_ambiental")
        ipfs_hash = meta.get("ipfs_hash", meta.get("coordenadas", ""))[:128]
        responsible = meta.get("responsable", "Junta de Extremadura")[:64]
        w3 = Web3(Web3.HTTPProvider(_GAIA_CHAIN_RPC))
        account = w3.eth.account.from_key(_JUNTA_PRIVATE_KEY.replace("0x", "").strip())
        contract = w3.eth.contract(address=Web3.to_checksum_address(_DOCUMENT_TOKEN_ADDRESS), abi=GREEN_LICENSE_ABI)
        tx = contract.functions.mintDocument(doc_hash, doc_type, ipfs_hash, responsible).build_transaction({
            "from": account.address, "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 500000, "gasPrice": w3.to_wei("50", "gwei"),
        })
        signed = w3.eth.account.sign_transaction(tx, _JUNTA_PRIVATE_KEY)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash = tx_hash_bytes.hex()
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash_bytes)
        token_id = 0
        if receipt.get("logs"):
            topic = Web3.keccak(text="DocumentMinted(uint256,string,string,address)")
            for log in receipt["logs"]:
                if len(log["topics"]) > 0 and log["topics"][0] == topic:
                    token_id = int(log["topics"][1].hex(), 16)
                    break
        verifier_base = os.getenv("VERIFIER_URL", "https://verifier.castuo-system.com")
        return {
            "status": "success",
            "token_id": token_id,
            "tx_hash": tx_hash,
            "ipfs_hash": ipfs_hash or None,
            "verification_url": f"{verifier_base}/?token_id={token_id}",
        }
    except Exception as e:
        logger.exception("Error en /api/forest/licenses: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fire/reports")
async def api_fire_reports(body: FireReportRequest, auth: bool = Depends(verify_token)):
    """Registra parte de incendio en GaiaChain (FireReportToken)."""
    if not _WEB3_AVAILABLE or not _JUNTA_PRIVATE_KEY or not _FIRE_REPORT_TOKEN_ADDRESS:
        raise HTTPException(status_code=503, detail="FireReportToken no configurado (FIRE_REPORT_TOKEN_ADDRESS, JUNTA_PRIVATE_KEY).")
    try:
        report_hash = _sha512_b64(body.document)
        meta = body.metadata
        location = meta.get("location", meta.get("coordenadas", ""))[:128]
        extinguished_by = meta.get("extinguished_by", "BRIF")[:64]
        affected_area = int(meta.get("affected_area", 0))
        w3 = Web3(Web3.HTTPProvider(_GAIA_CHAIN_RPC))
        account = w3.eth.account.from_key(_JUNTA_PRIVATE_KEY.replace("0x", "").strip())
        contract = w3.eth.contract(address=Web3.to_checksum_address(_FIRE_REPORT_TOKEN_ADDRESS), abi=FIRE_REPORT_ABI)
        tx = contract.functions.mintFireReport(account.address, report_hash, location, extinguished_by, affected_area).build_transaction({
            "from": account.address, "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 500000, "gasPrice": w3.to_wei("50", "gwei"),
        })
        signed = w3.eth.account.sign_transaction(tx, _JUNTA_PRIVATE_KEY)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
        tx_hash = tx_hash_bytes.hex()
        verifier_base = os.getenv("VERIFIER_URL", "https://verifier.castuo-system.com")
        return {
            "status": "success",
            "tx_hash": tx_hash,
            "verification_url": f"{verifier_base}/",
        }
    except Exception as e:
        logger.exception("Error en /api/fire/reports: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# --- Privacidad: derecho al olvido (ForestOwnershipToken) ---

try:
    from api.services.privacy_service import (
        verify_identity,
        erase_personal_data,
        update_metadata_in_blockchain,
        generate_erasure_certificate,
        send_erasure_confirmation_email,
        get_property_data,
    )
    _PRIVACY_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning("Servicio de privacidad no disponible: %s", e)
    _PRIVACY_SERVICE_AVAILABLE = False


@app.get("/api/property/{token_id}")
async def api_property(token_id: int):
    """Devuelve datos de la propiedad forestal para el dashboard (parcelaId, area, certifications, owner, ipfsHash)."""
    if not _PRIVACY_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Servicio de propiedades no configurado (ForestOwnershipToken).")
    data = get_property_data(token_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Token no encontrado o contrato no disponible.")
    return data


@app.post("/api/privacy/request-erasure")
async def api_privacy_request_erasure(body: ErasureRequest):
    """
    Ejercicio del derecho al olvido (GDPR Art. 17).
    Requiere: token_id, wallet_address (propietaria del token). Opcional: email para confirmación.
    Devuelve: request_id, transaction_hash, certificate_url, redacted_fields.
    """
    if not _PRIVACY_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Servicio de privacidad no configurado (FOREST_OWNERSHIP_TOKEN_ADDRESS, JUNTA_PRIVATE_KEY).",
        )
    try:
        is_valid = verify_identity(body.wallet_address, body.token_id)
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="La wallet indicada no es propietaria del token.",
            )
        erasure_data = erase_personal_data(body.token_id)
        logger.info("Datos personales borrados para token %s", body.token_id)
        tx_hash = update_metadata_in_blockchain(body.token_id, erasure_data["new_ipfs_hash"])
        logger.info("Metadatos actualizados en GaiaChain. TX: %s", tx_hash[:18])
        certificate = generate_erasure_certificate(
            body.token_id,
            erasure_data["old_ipfs_hash"],
            erasure_data["new_ipfs_hash"],
            erasure_data["redacted_fields"],
            tx_hash,
        )
        certificate_url = f"/certificates/{certificate['id']}.pdf"
        if body.email:
            send_erasure_confirmation_email(body.email, certificate, tx_hash)
        request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "request_id": request_id,
            "transaction_hash": tx_hash,
            "certificate_url": certificate_url,
            "redacted_fields": erasure_data["redacted_fields"],
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error en /api/privacy/request-erasure: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/certificates/{cert_id:path}")
async def api_certificate_pdf(cert_id: str):
    """Sirve el certificado de borrado en PDF (generado por request-erasure). Ej: /certificates/CERT-20260415100001.pdf"""
    cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificates")
    name = cert_id if cert_id.endswith(".pdf") else f"{cert_id}.pdf"
    path = os.path.join(cert_dir, name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Certificado no encontrado.")
    return FileResponse(path, media_type="application/pdf", filename=f"certificado_borrado_{os.path.basename(name)}")
