from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from ...security_internal import (
    audit_log,
    check_and_handle_request_storm,
    check_rate_limit,
    get_client_ip,
    ip_in_whitelist,
    pseudonymize_api_key,
)

router = APIRouter(tags=["public-key"])

API_KEY_HEADER = "X-API-Key"
REQUEST_ID_HEADER = "X-Request-Id"


def _get_request_id(request: Request) -> str:
    rid = request.headers.get(REQUEST_ID_HEADER)
    if rid:
        return str(rid).strip()
    return str(uuid.uuid4())


def _can_bridge_to_gaia_chain() -> bool:
    return __import__("os").environ.get("EDUCACION_GAIACHAIN_BRIDGE_ENABLED", "false").strip().lower() == "true"


def _educacion_gaia_token_id() -> int:
    raw = __import__("os").environ.get("EDUCACION_GAIACHAIN_TOKEN_ID", "1001").strip()
    try:
        return int(raw)
    except Exception:
        return 1001


def _rotate_pqc_keys_on_storm_task() -> None:
    """
    Rotación proactiva bajo señal centinela (feature flag).
    Opera en BackgroundTasks para no romper compatibilidad con Base44.
    """
    try:
        if __import__("os").environ.get("EDUCACION_ROTATE_ON_STORM", "false").strip().lower() != "true":
            return
        from backend.scripts.rotate_pqc_keys import rotate_keys

        rotate_keys(dry_run=False)
    except Exception:
        return


def _log_to_gaia_chain_public_key_safe(
    *,
    request_id: str,
    api_key: str,
    payload: Dict[str, Any],
    core_event_type: str = "educacion_public_key_bootstrap",
) -> None:
    if not _can_bridge_to_gaia_chain():
        return
    try:
        from backend.api.services.gaiachain_service import register_event_in_chain
    except Exception:
        # No rompe compatibilidad con Base44.
        return

    try:
        details = {
            "endpoint": "/public_key/ml_dsa",
            "request_id": request_id,
            "api_key_id": pseudonymize_api_key(api_key),
            "key_id": payload.get("key_id"),
            "previous_key_id": payload.get("previous_key_id"),
            "grace_expires_at": payload.get("grace_expires_at"),
            "algorithm": payload.get("algorithm"),
        }
        event_data = {
            "tokenId": _educacion_gaia_token_id(),
            "action": core_event_type,
            "status": "success",
            "details": details,
            "compliance": {
                "gdpr": "Art. 30 (Registro de actividades)",
                "iso27001": "A.12.4.1 (Registro de eventos)",
                "eidas2": "Bootstrap public key ML-DSA para Base44",
            },
            "tokenId_source": "EDUCACION_GAIACHAIN_TOKEN_ID",
        }
        # register_event_in_chain es sync
        register_event_in_chain(event_data)
    except Exception:
        return


def _load_educacion_api_keys() -> List[str]:
    raw = __import__("os").getenv("EDUCACION_API_KEYS", "").strip()
    if not raw:
        return []
    # Rotación simple: lista separada por comas.
    return [k.strip() for k in raw.split(",") if k.strip()]


EDUCACION_API_KEYS = _load_educacion_api_keys()


def _require_educacion_api_key(x_api_key: Optional[str]) -> str:
    if not EDUCACION_API_KEYS:
        # Si no hay claves configuradas, bloqueamos para evitar fuga por error.
        raise HTTPException(status_code=503, detail="EDUCACION_API_KEYS no configurado")
    if not x_api_key or x_api_key not in set(EDUCACION_API_KEYS):
        raise HTTPException(status_code=403, detail="API Key inválida")
    return x_api_key


def _sign_response(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Firma PQC (ML-DSA) del JSON canónico (estable).
    Se devuelve en headers para que Base44 pueda auditar integridad del canal.
    """
    from backend.api.security.pqc import pqc

    data_str = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sig = pqc.sign_data_pqc(data_str)
    signature = sig.get("signature") or "ml-dsa-signature-missing"
    algorithm = sig.get("algorithm") or "ML-DSA-Dilithium5"
    return {"X-Sabionda-PQC-Signature": signature, "X-Sabionda-PQC-Algorithm": algorithm}


@router.get("/public_key/ml_dsa")
async def get_public_key_ml_dsa(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
) -> Dict[str, Any]:
    """
    Bootstrap seguro para Base44:
    - Devuelve la public key ML-DSA (Dilithium-5) en base64.
    - Incluye fingerprint blake3 para pinning.
    - No requiere rol admin.
    """
    api_key = _require_educacion_api_key(x_api_key)

    endpoint = "/public_key/ml_dsa"
    request_id = _get_request_id(request)
    response.headers[REQUEST_ID_HEADER] = request_id

    api_key_pseudo = pseudonymize_api_key(api_key)
    storm = check_and_handle_request_storm(api_key_pseudo=api_key_pseudo, request_id=request_id)
    if storm:
        audit_log(
            event_type="educacion_node_isolation",
            path=endpoint,
            method=request.method,
            role="base44",
            resource_id=None,
            ip=get_client_ip(request),
            extra={"api_key_id": api_key_pseudo, "request_id": request_id, "endpoint": endpoint},
        )
        if __import__("os").environ.get("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true":
            if background_tasks is not None:
                background_tasks.add_task(_rotate_pqc_keys_on_storm_task)
            raise HTTPException(status_code=429, detail="Isla activada por tormenta de requests")

    if not check_rate_limit(api_key, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit superado")

    if not ip_in_whitelist(get_client_ip(request), None):
        raise HTTPException(status_code=403, detail="IP no autorizada")

    from backend.security.pq_crypto import PostQuantumCrypto as CoreCrypto

    core = CoreCrypto()
    public_key_b64 = core.dilithium_public_key_base64()
    fingerprint = core.dilithium_public_key_fingerprint()
    previous_public_key_b64 = core.dilithium_previous_public_key_base64()
    previous_fingerprint = core.dilithium_previous_public_key_fingerprint()
    previous_key_id = core.dilithium_previous_key_id()
    prev_expires_ts = core.dilithium_previous_expires_at_ts()
    grace_expires_at = None
    if prev_expires_ts:
        try:
            grace_expires_at = datetime.fromtimestamp(float(prev_expires_ts), tz=timezone.utc).isoformat()
        except Exception:
            grace_expires_at = None

    payload = {
        "algorithm": "ML-DSA-Dilithium5",
        # En este repo la “.pem” contiene bytes crudos codificados en base64 (sin cabecera PEM clásica).
        "public_key_b64": public_key_b64,
        "fingerprint_blake3": fingerprint,
        "key_id": f"dilithium5-{fingerprint[:10]}",
        # Compatibilidad A/B (rotación con grace window 24h por diseño).
        "previous_public_key_b64": previous_public_key_b64,
        "previous_fingerprint_blake3": previous_fingerprint,
        "previous_key_id": previous_key_id,
        "grace_expires_at": grace_expires_at,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    response.headers.update(_sign_response(payload))

    try:
        audit_log(
            event_type="educacion_public_key_bootstrap",
            path=endpoint,
            method=request.method,
            role="base44",
            resource_id=payload["key_id"],
            ip=get_client_ip(request),
            extra={
                "algorithm": payload["algorithm"],
                "request_id": request_id,
                "api_key_id": api_key_pseudo,
                "scenario_id": None,
            },
        )
    except Exception:
        # TRL9: no romper el servicio por auditoría secundaria.
        pass

    if background_tasks is not None:
        background_tasks.add_task(
            _log_to_gaia_chain_public_key_safe,
            request_id=request_id,
            api_key=api_key,
            payload=payload,
            core_event_type="educacion_public_key_bootstrap",
        )

    return payload

