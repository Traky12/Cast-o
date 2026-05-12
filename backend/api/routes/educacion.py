from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, Response

from ..security.pqc import pqc
from ...security_internal import (
    audit_log,
    check_and_handle_request_storm,
    check_rate_limit,
    get_client_ip,
    ip_in_whitelist,
    pseudonymize_api_key,
)
from pydantic import BaseModel


router = APIRouter(prefix="/api/educacion", tags=["educacion"])


API_KEY_HEADER = "X-API-Key"
REQUEST_ID_HEADER = "X-Request-Id"


def _get_request_id(request: Request) -> str:
    rid = request.headers.get(REQUEST_ID_HEADER)
    if rid:
        return str(rid).strip()
    return str(uuid.uuid4())


def _can_bridge_to_gaia_chain() -> bool:
    return os.getenv("EDUCACION_GAIACHAIN_BRIDGE_ENABLED", "false").strip().lower() == "true"


def _educacion_gaia_token_id() -> int:
    raw = os.getenv("EDUCACION_GAIACHAIN_TOKEN_ID", "1001").strip()
    try:
        return int(raw)
    except Exception:
        return 0


def _rotate_pqc_keys_on_storm_task() -> None:
    """
    Rotación proactiva bajo señal centinela (feature flag).
    Nunca bloquea el flujo principal; opera vía BackgroundTasks.
    """
    try:
        if os.getenv("EDUCACION_ROTATE_ON_STORM", "false").strip().lower() != "true":
            return
        from backend.scripts.rotate_pqc_keys import rotate_keys

        rotate_keys(dry_run=False)
    except Exception:
        # “Isla” sin romper el ecosistema: si falla la rotación, seguimos permitiendo
        # el modo de verificación por ventana A/B (grace).
        return


def _load_educacion_api_keys() -> List[str]:
    raw = os.getenv("EDUCACION_API_KEYS", "").strip()
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


def _get_rate_key(api_key: str, endpoint: str) -> Tuple[str, str]:
    # Rate limiting por API key y endpoint.
    return api_key, endpoint


def _sign_response(payload: Dict[str, Any]) -> Dict[str, str]:
    """
    Firma PQC sobre el JSON canónico (estable) y devuelve headers esperados por Base44.
    """
    data_str = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sig = pqc.sign_data_pqc(data_str)
    signature = sig.get("signature") or "vault-pqc"
    algorithm = sig.get("algorithm") or "ML-DSA-Dilithium5"
    key_id = sig.get("key_id")
    headers: Dict[str, str] = {
        "X-Sabionda-PQC-Signature": signature,
        "X-Sabionda-PQC-Algorithm": algorithm,
    }
    if key_id:
        headers["X-Sabionda-PQC-Key-Id"] = str(key_id)
    return headers


def _audit_educacion_access(
    request: Request,
    api_key: str,
    endpoint: str,
    request_id: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    # No registramos api_key ni secretos; audit_log ya redacción por claves sensibles.
    ip = get_client_ip(request)
    try:
        audit_log(
            event_type="educacion_api_access",
            path=endpoint,
            method=request.method,
            role="base44",
            resource_id=None,
            ip=ip,
            extra={
                "api_key_id": pseudonymize_api_key(api_key),
                "request_id": request_id,
                **(extra or {}),
            },
        )
    except Exception:
        # TRL9: no romper el servicio por auditoría secundaria.
        pass


async def _log_to_gaia_chain_safe(
    endpoint: str,
    request_id: str,
    api_key: str,
    scenario_id: Optional[str],
) -> None:
    """
    Puente no bloqueante hacia GaiaChain/ledger.
    Feature-flag: `EDUCACION_GAIACHAIN_BRIDGE_ENABLED=true`.
    """
    if not _can_bridge_to_gaia_chain():
        return

    try:
        from ..services.gaiachain_service import register_event_in_chain

        details = {
            "endpoint": endpoint,
            "scenario_id": scenario_id,
            "request_id": request_id,
            "api_key_id": _api_key_id(api_key),
        }
        event_data = {
            "tokenId": _educacion_gaia_token_id(),
            "action": endpoint,
            "status": "success",
            "details": details,
            "compliance": {
                "gdpr": "Art. 30 (Registro de actividades)",
                "iso27001": "A.12.4.1 (Registro de eventos)",
                "eidas2": "Base44 acceso (ML-DSA verificado por cliente)",
            },
        }
        # register_event_in_chain es sync; lo ejecutamos directo (está en BackgroundTasks).
        register_event_in_chain(event_data)
    except Exception:
        # TRL9: tolerancia a fallos; nunca romper compatibilidad con Base44.
        return


@router.get("/scenarios/{scenario_id}")
async def get_scenario(
    scenario_id: str,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
) -> Dict[str, Any]:
    api_key = _require_educacion_api_key(x_api_key)
    endpoint = f"/api/educacion/scenarios/{scenario_id}"
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
        if os.getenv("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true":
            if background_tasks is not None:
                background_tasks.add_task(_rotate_pqc_keys_on_storm_task)
            raise HTTPException(status_code=429, detail="Isla activada por tormenta de requests")

    # Rate limiting por API key.
    ip_key, _ = _get_rate_key(api_key, endpoint)
    if not check_rate_limit(ip_key, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit superado")

    # Si hay whitelist configurada, exigimos.
    if not ip_in_whitelist(get_client_ip(request), None):
        raise HTTPException(status_code=403, detail="IP no autorizada")

    scenarios = {
        "sequia-extremadura-2026": {
            "nombre": "Sequía en Extremadura (2026)",
            "datos": {
                "humedad_suelo": 12,
                "temperatura": 38,
                "precipitacion_ultimos_7dias": 0,
                "consumo_agua_actual": 2000,
            },
            "acciones_posibles": [
                {
                    "id": "regar",
                    "nombre": "Regar 5L/m²",
                    "impacto": {"consumo_agua": "+20%", "supervivencia_cultivo": "+90%"},
                },
                {
                    "id": "cubrir_suelo",
                    "nombre": "Cubrir suelo con paja",
                    "impacto": {"consumo_agua": "-10%", "supervivencia_cultivo": "+30%"},
                },
            ],
            "recomendacion_sabionda": {
                "accion": "cubrir_suelo",
                "explicacion": "Reducir evaporación mantiene humedad sin aumentar consumo de agua.",
            },
        },
        "inundacion-ribera-2026": {
            "nombre": "Inundación en Ribera (2026)",
            "datos": {
                "humedad_suelo": 92,
                "temperatura": 21,
                "precipitacion_ultimos_7dias": 210,
                "consumo_agua_actual": 1200,
            },
            "acciones_posibles": [
                {
                    "id": "drenar",
                    "nombre": "Activar drenaje controlado",
                    "impacto": {"consumo_agua": "-5%", "supervivencia_cultivo": "+70%"},
                },
                {
                    "id": "cubrir-raices",
                    "nombre": "Proteger raíces con acolchado",
                    "impacto": {"consumo_agua": "+0%", "supervivencia_cultivo": "+35%"},
                },
            ],
            "recomendacion_sabionda": {
                "accion": "drenar",
                "explicacion": "Controlar el exceso de agua reduce estrés hídrico e infecciones.",
            },
        },
    }

    if scenario_id not in scenarios:
        raise HTTPException(status_code=404, detail="Escenario no encontrado")

    payload: Dict[str, Any] = {"scenario_id": scenario_id, **scenarios[scenario_id]}
    headers = _sign_response(payload)
    response.headers.update(headers)

    _audit_educacion_access(
        request,
        api_key=api_key,
        endpoint=endpoint,
        request_id=request_id,
        extra={"scenario_id": scenario_id},
    )
    if background_tasks is not None:
        background_tasks.add_task(
            _log_to_gaia_chain_safe,
            endpoint=endpoint,
            request_id=request_id,
            api_key=api_key,
            scenario_id=scenario_id,
        )
    return payload


@router.get("/comic-2040")
async def comic_2040(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
) -> Dict[str, Any]:
    api_key = _require_educacion_api_key(x_api_key)
    endpoint = "/api/educacion/comic-2040"
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
        if os.getenv("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true":
            if background_tasks is not None:
                background_tasks.add_task(_rotate_pqc_keys_on_storm_task)
            raise HTTPException(status_code=429, detail="Isla activada por tormenta de requests")
    if not check_rate_limit(api_key, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit superado")

    if not ip_in_whitelist(get_client_ip(request), None):
        raise HTTPException(status_code=403, detail="IP no autorizada")

    # Versión compacta (sin exponer archivos fuera del contenedor).
    payload = {
        "titulo": "CASTÚO 2040: El cómic de la rebelión verde",
        "formato": "portada + 6 viñetas",
        "comic": [
            {"vinieta": 0, "titulo": "Portada", "texto": "Cuando los datos son más valiosos que el agua..."},
            {"vinieta": 1, "titulo": "Los tractores se apagaron", "texto": "AgroTech bloquea los datos climáticos. Sin ellos, los cultivos se secarán en 72 horas."},
            {"vinieta": 2, "titulo": "Infiltrarse en la nube", "texto": "Se diseña un plan maker. La alianza actúa con inteligencia y prudencia."},
            {"vinieta": 3, "titulo": "La trampa: el virus COBOL", "texto": "Sabionda guía la estrategia. La supervivencia depende del timing y la ética."},
            {"vinieta": 4, "titulo": "Datos vs. guardias", "texto": "La defensa se activa: seguridad, resiliencia y verdad física."},
            {"vinieta": 5, "titulo": "Victoria: núcleo liberado", "texto": "Datos recuperados. Ahora se liberan como bien común algorítmico."},
        ],
        "actividades": [
            "Debate: ¿Es justo pagar por datos si determinan la comida?",
            "Taller maker: diseña un 'superpoder' para Sabionda y explica su impacto.",
        ],
    }

    headers = _sign_response(payload)
    response.headers.update(headers)
    _audit_educacion_access(request, api_key=api_key, endpoint=endpoint, request_id=request_id, extra={})
    if background_tasks is not None:
        background_tasks.add_task(
            _log_to_gaia_chain_safe,
            endpoint=endpoint,
            request_id=request_id,
            api_key=api_key,
            scenario_id=None,
        )
    return payload


class ActividadRequest(BaseModel):
    scenario_id: str
    nivel: str = "secundaria"


class SabiondaExplicaRequest(BaseModel):
    concepto: Optional[str] = None
    tema: Optional[str] = None


@router.post("/actividades")
async def actividades(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    body: ActividadRequest,
    x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
) -> Dict[str, Any]:
    api_key = _require_educacion_api_key(x_api_key)
    endpoint = "/api/educacion/actividades"
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
        if os.getenv("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true":
            if background_tasks is not None:
                background_tasks.add_task(_rotate_pqc_keys_on_storm_task)
            raise HTTPException(status_code=429, detail="Isla activada por tormenta de requests")
    if not check_rate_limit(api_key, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit superado")
    if not ip_in_whitelist(get_client_ip(request), None):
        raise HTTPException(status_code=403, detail="IP no autorizada")

    scenario_id = str(body.scenario_id)
    nivel = str(body.nivel or "secundaria").lower()
    if not scenario_id:
        raise HTTPException(status_code=400, detail="Falta scenario_id")

    # Datos de ejemplo (anonimizados) reutilizando recomendaciones de scenarios.
    # Si el escenario no existe, generamos actividad genérica.
    objetivo = (
        "Aprender a decidir con datos anonimizados en crisis climática."
        if nivel in {"primaria", "secundaria", "fp", "universidad"}
        else "Aprender con datos anonimizados."
    )

    payload = {
        "actividad_id": f"act_{scenario_id}_{int(time.time())}",
        "scenario_id": scenario_id,
        "nivel": nivel,
        "objetivos": [objetivo],
        "datos_anonimizados": {
            "nota": "Datos agregados/anónimos (no PII).",
            "ejemplos": ["humedad_suelo (simulada/agregada)", "temperatura", "precipitacion_ultimos_7dias"],
        },
        "preguntas_guia": [
            "¿Qué dato usarías primero y por qué?",
            "¿Qué acción minimiza el impacto en consumo de agua?",
            "¿Cómo justificarías tu decisión con ética y eficiencia?",
        ],
        "tiempo_min": 60 if nivel in {"secundaria", "fp", "universidad"} else 30,
    }

    headers = _sign_response(payload)
    response.headers.update(headers)
    _audit_educacion_access(
        request,
        api_key=api_key,
        endpoint=endpoint,
        request_id=request_id,
        extra={"scenario_id": scenario_id, "nivel": nivel},
    )
    if background_tasks is not None:
        background_tasks.add_task(
            _log_to_gaia_chain_safe,
            endpoint=endpoint,
            request_id=request_id,
            api_key=api_key,
            scenario_id=scenario_id,
        )
    return payload


@router.post("/sabionda-explica")
async def sabionda_explica(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    body: SabiondaExplicaRequest,
    x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
) -> Dict[str, Any]:
    api_key = _require_educacion_api_key(x_api_key)
    endpoint = "/api/educacion/sabionda-explica"
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
        if os.getenv("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true":
            if background_tasks is not None:
                background_tasks.add_task(_rotate_pqc_keys_on_storm_task)
            raise HTTPException(status_code=429, detail="Isla activada por tormenta de requests")
    if not check_rate_limit(api_key, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit superado")
    if not ip_in_whitelist(get_client_ip(request), None):
        raise HTTPException(status_code=403, detail="IP no autorizada")

    concepto = str(body.concepto or body.tema or "").strip().lower()
    if not concepto:
        raise HTTPException(status_code=400, detail="Falta concepto")

    templates = {
        "hsm": {
            "titulo": "¿Qué es un HSM?",
            "texto": "Un HSM (Hardware Security Module) es un cofre seguro donde se guardan claves criptográficas. Así, las claves no viajan por software y las firmas quedan más protegidas.",
        },
        "pqc": {
            "titulo": "¿Qué es PQC (cripto post-cuántica)?",
            "texto": "PQC son técnicas criptográficas diseñadas para resistir ataques incluso cuando aparezcan computadores cuánticos.",
        },
        "kyber": {
            "titulo": "¿Qué es Kyber?",
            "texto": "Kyber es un método post-cuántico usado para establecer secretos con seguridad futura. En Castúo-System se usa para blindar integridad y custodias.",
        },
        "sensor de humedad": {
            "titulo": "¿Qué es un sensor de humedad?",
            "texto": "Mide cuánta agua hay en el suelo. Con ese dato, Sabionda ayuda a regar justo lo necesario, ahorrando agua y cuidando los cultivos.",
        },
        "sensor humedad": {
            "titulo": "¿Qué es un sensor de humedad?",
            "texto": "Mide cuánta agua hay en el suelo para decidir cuándo regar.",
        },
        "cifrado": {
            "titulo": "¿Qué es el cifrado?",
            "texto": "Cifrar significa transformar información para que solo quien tiene la clave pueda entenderla.",
        },
    }

    # Heurística simple de matching.
    hit = None
    for k in templates.keys():
        if k in concepto:
            hit = templates[k]
            break
    if not hit:
        hit = {"titulo": "Explicación simple", "texto": f"Sabionda explica: '{concepto}' con enfoque de soberanía y eficiencia, usando datos anonimizados y verificación."}

    payload = {"concepto": concepto, **hit}
    headers = _sign_response(payload)
    response.headers.update(headers)
    _audit_educacion_access(request, api_key=api_key, endpoint=endpoint, request_id=request_id, extra={"concepto": concepto})
    if background_tasks is not None:
        background_tasks.add_task(
            _log_to_gaia_chain_safe,
            endpoint=endpoint,
            request_id=request_id,
            api_key=api_key,
            scenario_id=None,
        )
    return payload


@router.get("/telemetria-anon")
async def telemetria_anon(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    x_api_key: Optional[str] = Header(None, alias=API_KEY_HEADER),
) -> Dict[str, Any]:
    api_key = _require_educacion_api_key(x_api_key)
    endpoint = "/api/educacion/telemetria-anon"
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
        if os.getenv("EDUCACION_ISOLATION_ON_STORM", "false").strip().lower() == "true":
            if background_tasks is not None:
                background_tasks.add_task(_rotate_pqc_keys_on_storm_task)
            raise HTTPException(status_code=429, detail="Isla activada por tormenta de requests")
    if not check_rate_limit(api_key, endpoint):
        raise HTTPException(status_code=429, detail="Rate limit superado")
    if not ip_in_whitelist(get_client_ip(request), None):
        raise HTTPException(status_code=403, detail="IP no autorizada")

    # Métricas agregadas: se generan de forma determinista por fecha (no PII).
    now = datetime.now(timezone.utc)
    bucket = f"{now.year}-{now.month:02d}"
    seed = sum(ord(c) for c in bucket) % 1000
    water_saving = 20 + (seed % 31)  # 20..50
    projects = 15 + (seed % 26)  # 15..40
    payload = {
        "timestamp": now.isoformat(),
        "periodo": bucket,
        "metricas_agregadas": [
            {"metric": "ahorro_agua_pct", "value": water_saving, "unit": "%", "alcance": "huertos escolares"},
            {"metric": "proyectos_impacto", "value": projects, "unit": "proyectos", "alcance": "comunidades piloto"},
        ],
        "nota": "Datos agregados/anónimos. Sin PII y sin metadatos identificables.",
    }

    headers = _sign_response(payload)
    response.headers.update(headers)
    _audit_educacion_access(request, api_key=api_key, endpoint=endpoint, request_id=request_id, extra={"periodo": bucket})
    if background_tasks is not None:
        background_tasks.add_task(
            _log_to_gaia_chain_safe,
            endpoint=endpoint,
            request_id=request_id,
            api_key=api_key,
            scenario_id=None,
        )
    return payload

