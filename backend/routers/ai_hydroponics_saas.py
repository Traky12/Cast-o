# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter

from backend.services.gaia_chain import GaiaChainService
from backend.services.mistral import analyze_with_mistral
from backend.database import is_postgres_available

router = APIRouter(prefix="/ai", tags=["AI Agents Hydroponics SaaS"])


AI_HYDRO_MONITORING_TOTAL = Counter(
    "ai_hydroponics_monitoring_total",
    "Total hydroponics AI monitoring agent calls",
    ["status"],
)
AI_HYDRO_CROPS_TOTAL = Counter(
    "ai_hydroponics_crops_total",
    "Total hydroponics AI crop management agent calls",
    ["stage_status"],
)


def _get_allowed_api_keys() -> List[str]:
    # Reutiliza la misma estrategia que hydroponics-saas para integraciones n8n.
    raw = os.getenv("HYDROPONICS_SAAS_API_KEYS", "").strip()
    if raw:
        return [x.strip() for x in raw.split(",") if x.strip()]

    k = os.getenv("N8N_API_KEY", "").strip()
    if k:
        return [k]

    return ["default_n8n_key_123"]


def _validate_api_key(x_api_key: Optional[str]) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-KEY")
    if x_api_key not in set(_get_allowed_api_keys()):
        raise HTTPException(status_code=403, detail="Invalid API key")


def _require_x_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    x_api_key_alt: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    key = x_api_key or x_api_key_alt or ""
    _validate_api_key(key)
    return key


def _try_parse_json_maybe(text: str) -> Optional[Dict[str, Any]]:
    """
    Intenta extraer JSON de respuestas LLM (a veces incluyen texto alrededor).
    No es perfecto, pero mantiene el flujo robusto para n8n.
    """
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    # Estricta: buscamos primer { ... último }.
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


def _extract_latest_sensor_value(
    history: List[Dict[str, Any]],
    sensor_type: str,
) -> Optional[float]:
    """
    Fallback: si `history` trae items con {sensor_type: "...", value: ...},
    tomamos el último valor disponible.
    """
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        st = item.get("sensor_type")
        if st == sensor_type:
            try:
                return float(item.get("value"))
            except Exception:
                return None
    return None


def _rule_based_monitoring(
    sensors: Dict[str, Any],
    history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    ph = sensors.get("ph")
    ec = sensors.get("ec")
    temperature = sensors.get("temperature")
    humidity = sensors.get("humidity")
    light = sensors.get("light")

    # Si no viene snapshot, intentamos sacar de history.
    ph = ph if ph is not None else _extract_latest_sensor_value(history, "ph")
    ec = ec if ec is not None else _extract_latest_sensor_value(history, "ec")
    temperature = temperature if temperature is not None else _extract_latest_sensor_value(history, "temperature")
    humidity = humidity if humidity is not None else _extract_latest_sensor_value(history, "humidity")
    light = light if light is not None else _extract_latest_sensor_value(history, "light")

    predicted_issues: List[Dict[str, Any]] = []
    recommendations: List[str] = []

    def _add_issue(type_name: str, prob: float, timeframe: str, rec: str, critical: bool) -> None:
        predicted_issues.append(
            {"type": type_name, "probability": float(prob), "timeframe": timeframe}
        )
        if rec:
            recommendations.append(rec)

    # Heurísticas de seguridad (fallback). En producción, el modelo (Mistral) debe reemplazar esto.
    status = "optimal"

    if isinstance(ph, (int, float)):
        if ph < 5.5 or ph > 6.8:
            status = "critical"
            _add_issue("ph_high_or_low", 0.85, "12h", "Ajustar pH y verificar calibración de sonda.", True)
        elif ph < 5.7 or ph > 6.6:
            if status != "critical":
                status = "warning"
            _add_issue("ph_drift", 0.7, "24h", "Verificar tendencia de pH y corregir en ventana corta.", False)

    if isinstance(temperature, (int, float)):
        if temperature < 16.0 or temperature > 28.0:
            status = "critical"
            _add_issue("temperature_out_of_range", 0.8, "24h", "Revisar enfriamiento/calefacción y ventilación.", True)
        elif temperature < 18.0 or temperature > 26.0:
            if status != "critical":
                status = "warning"
            _add_issue("temperature_drift", 0.65, "24h", "Ajustar control térmico para estabilizar temperatura.", False)

    if isinstance(humidity, (int, float)):
        if humidity < 40.0 or humidity > 80.0:
            if status != "critical":
                status = "critical"
            _add_issue("humidity_out_of_range", 0.75, "24h", "Ajustar deshumidificación/ventilación y humidificación.", True)
        elif humidity < 45.0 or humidity > 75.0:
            if status not in ("critical",):
                status = "warning"
            _add_issue("humidity_drift", 0.6, "24h", "Mantener humedad en rango con ciclos de aire.", False)

    if isinstance(ec, (int, float)):
        if ec < 0.9 or ec > 3.2:
            status = "critical"
            _add_issue("ec_out_of_range", 0.8, "24h", "Revisar dosificación A/B y concentración de sales.", True)
        elif ec < 1.1 or ec > 2.6:
            if status != "critical":
                status = "warning"
            _add_issue("ec_drift", 0.65, "24h", "Calibrar bomba dosificadora y estabilizar EC.", False)

    if light is not None and isinstance(light, (int, float)):
        # Heurística liviana (sin umbrales por cultivo).
        if light < 1000:
            if status != "critical":
                status = "warning"
            _add_issue("light_low", 0.6, "24h", "Verificar lámparas/LED y uniformidad de iluminación.", False)

    if not predicted_issues:
        recommendations.append("Parámetros estables. Mantener control y registrar evidencia cada 4 horas.")

    return {
        "status": status,
        "predicted_issues": predicted_issues,
        "recommendations": recommendations,
        "source": "rule_based_fallback",
    }


def _rule_based_crop_management(payload: Dict[str, Any]) -> Dict[str, Any]:
    growth_stage = str(payload.get("growth_stage") or "").lower()
    age_days = payload.get("age_days")
    plant_type = str(payload.get("plant_type") or "").lower()

    if "veget" in growth_stage or not growth_stage:
        stage_status = "on_track"
        nutrient_recommendations = {"N": 120, "P": 70, "K": 110, "Ca": 60}
        light_cycle = "16/8"
    elif "flow" in growth_stage or "flower" in growth_stage or "repro" in growth_stage:
        stage_status = "on_track"
        nutrient_recommendations = {"N": 95, "P": 85, "K": 140, "Ca": 65}
        light_cycle = "14/10"
    else:
        stage_status = "on_track" if isinstance(age_days, (int, float)) else "on_track"
        nutrient_recommendations = {"N": 105, "P": 80, "K": 125, "Ca": 62}
        light_cycle = "15/9"

    # Evitamos simular fechas sin planting_date real: retornamos TBD si no existe.
    expected_harvest = payload.get("expected_harvest") or "TBD"
    yield_prediction = payload.get("yield_prediction") or 0

    return {
        "growth_stage_status": stage_status,
        "nutrient_recommendations": nutrient_recommendations,
        "light_cycle": light_cycle,
        "expected_harvest": expected_harvest,
        "yield_prediction": yield_prediction,
        "source": "rule_based_fallback",
        "plant_type": plant_type,
    }


class HydroMonitoringRequest(BaseModel):
    zone_id: str
    sensors: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    timeframe_hours: int = 24
    crop_context: Dict[str, Any] = Field(default_factory=dict)


class HydroCropManagementRequest(BaseModel):
    zone_id: str
    crop_id: Optional[str] = None
    plant_type: str = "unknown"
    growth_stage: str = "vegetative"
    age_days: Optional[int] = None
    current_conditions: Dict[str, Any] = Field(default_factory=dict)
    history: List[Dict[str, Any]] = Field(default_factory=list)


@router.post("/monitoring")
async def monitoring_agent(
    body: HydroMonitoringRequest,
    _: str = Depends(_require_x_api_key),
) -> Dict[str, Any]:
    """
    Agente de Monitoreo Continuo (SaaS).
    Retorna estructura estable para n8n, aunque el modelo LLM no esté disponible.
    """
    # 1) Fallback determinista (si no hay API key, o si el LLM no retorna JSON usable).
    fallback = _rule_based_monitoring(body.sensors, body.history)

    # 2) Si hay clave, intentamos enriquecer con Mistral (y parsear JSON).
    mistral_out: Optional[Dict[str, Any]] = None
    if os.getenv("MISTRAL_API_KEY"):
        prompt = (
            "Eres un experto en monitoreo de cultivos hidroponicos.\n"
            "Devuelve SOLO JSON estricto con llaves:\n"
            "{\n"
            "  \"status\": \"optimal|warning|critical\",\n"
            "  \"predicted_issues\": [{\"type\": \"...\", \"probability\": 0.0, \"timeframe\": \"12h|24h\"}],\n"
            "  \"recommendations\": [\"...\"],\n"
            "  \"timeframe_hours\": 24\n"
            "}\n"
            "Reglas: usa evidencia del input; no inventes valores numéricos.\n\n"
            f"zone_id: {body.zone_id}\n"
            f"sensors: {json.dumps(body.sensors, ensure_ascii=False)}\n"
            f"history: {json.dumps(body.history[-50:], ensure_ascii=False)}\n"
        )
        try:
            analysis = await analyze_with_mistral(prompt=prompt, model="mistral-small-latest")
            raw_summary = str(analysis.get("summary") or "")
            parsed = _try_parse_json_maybe(raw_summary)
            if parsed and "status" in parsed:
                parsed.setdefault("source", "mistral_json")
                mistral_out = parsed
        except Exception:
            mistral_out = None

    agent_output = mistral_out or fallback
    status = str(agent_output.get("status") or "optimal")
    AI_HYDRO_MONITORING_TOTAL.labels(status=status).inc()

    # 3) Evidencia minimizada en GaiaChain (no requiere Postgres).
    tx_hash: Optional[str] = None
    try:
        if is_postgres_available():
            payload = {
                "zone_id": body.zone_id,
                "status": status,
                "predicted_issues": agent_output.get("predicted_issues", []),
                "recommendations": agent_output.get("recommendations", []),
                "timeframe_hours": body.timeframe_hours,
                "context": body.crop_context,
                "timestamp": int(datetime.utcnow().timestamp()),
            }
            tx = await GaiaChainService().register_batch(
                {
                    "batch_id": f"ai-monitoring-{body.zone_id}-{int(datetime.utcnow().timestamp())}",
                    "strain_id": f"ai_zone:{body.zone_id}",
                    "thc_percentage": 0,
                    "cbd_percentage": 0,
                    "weight_kg": 0,
                    "lab_results": {
                        "event_type": "HYDROPONICS_AI_MONITORING",
                        "data": payload,
                        "status": status,
                    },
                    "account_id": os.getenv("HYDROPONICS_SAAS_ACCOUNT_ID", "hydroponics-saas"),
                }
            )
            tx_hash = tx.get("transaction_hash") if isinstance(tx, dict) else None
    except Exception:
        tx_hash = None

    return {
        "status": "success",
        "agent": "Agente_Monitoreo",
        "agent_output": agent_output,
        "gaiachain_tx": tx_hash,
    }


@router.post("/crops")
async def crops_agent(
    body: HydroCropManagementRequest,
    _: str = Depends(_require_x_api_key),
) -> Dict[str, Any]:
    """
    Agente de Gestión de Cultivos (SaaS).
    Retorna estructura estable para que el workflow decida si crea/actualiza cultivos.
    """
    fallback = _rule_based_crop_management(body.model_dump(mode="json"))

    mistral_out: Optional[Dict[str, Any]] = None
    if os.getenv("MISTRAL_API_KEY"):
        prompt = (
            "Eres un agrónomo especializado en hidroponía.\n"
            "Devuelve SOLO JSON estricto con llaves:\n"
            "{\n"
            "  \"growth_stage_status\": \"on_track|delayed|accelerated\",\n"
            "  \"nutrient_recommendations\": {\"N\":0,\"P\":0,\"K\":0,\"Ca\":0},\n"
            "  \"light_cycle\": \"16/8|14/10|12/12|...\",\n"
            "  \"expected_harvest\": \"YYYY-MM-DD|TBD\",\n"
            "  \"yield_prediction\": 0\n"
            "}\n"
            "Regla: no inventes fechas si no se proporcionan datos suficientes.\n\n"
            f"zone_id: {body.zone_id}\n"
            f"crop_id: {body.crop_id}\n"
            f"plant_type: {body.plant_type}\n"
            f"growth_stage: {body.growth_stage}\n"
            f"age_days: {body.age_days}\n"
            f"current_conditions: {json.dumps(body.current_conditions, ensure_ascii=False)}\n"
            f"history: {json.dumps(body.history[-50:], ensure_ascii=False)}\n"
        )
        try:
            analysis = await analyze_with_mistral(prompt=prompt, model="mistral-small-latest")
            raw_summary = str(analysis.get("summary") or "")
            parsed = _try_parse_json_maybe(raw_summary)
            if parsed and "growth_stage_status" in parsed:
                parsed.setdefault("source", "mistral_json")
                mistral_out = parsed
        except Exception:
            mistral_out = None

    agent_output = mistral_out or fallback
    stage_status = str(agent_output.get("growth_stage_status") or "on_track")
    AI_HYDRO_CROPS_TOTAL.labels(stage_status=stage_status).inc()

    tx_hash: Optional[str] = None
    try:
        if is_postgres_available():
            payload = {
                "zone_id": body.zone_id,
                "crop_id": body.crop_id,
                "plant_type": body.plant_type,
                "growth_stage": body.growth_stage,
                "age_days": body.age_days,
                "agent_output": agent_output,
                "timestamp": int(datetime.utcnow().timestamp()),
            }
            tx = await GaiaChainService().register_batch(
                {
                    "batch_id": f"ai-crops-{body.zone_id}-{int(datetime.utcnow().timestamp())}",
                    "strain_id": f"ai_crop:{body.crop_id or body.plant_type}",
                    "thc_percentage": 0,
                    "cbd_percentage": 0,
                    "weight_kg": 0,
                    "lab_results": {
                        "event_type": "HYDROPONICS_AI_CROP_MANAGEMENT",
                        "data": payload,
                        "status": stage_status,
                    },
                    "account_id": os.getenv("HYDROPONICS_SAAS_ACCOUNT_ID", "hydroponics-saas"),
                }
            )
            tx_hash = tx.get("transaction_hash") if isinstance(tx, dict) else None
    except Exception:
        tx_hash = None

    return {
        "status": "success",
        "agent": "Agente_Cultivos",
        "agent_output": agent_output,
        "gaiachain_tx": tx_hash,
    }

