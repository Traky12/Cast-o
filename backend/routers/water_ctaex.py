# -*- coding: utf-8 -*-
"""Análisis ORP/TDS/pH agua — umbrales de proyecto CASTÚO + texto opcional Ollama Cloud (API compatible OpenAI)."""

from __future__ import annotations

import hmac
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from backend.services.billing_utils import send_invoice_email
from backend.services.water_billing import (
    generate_certification_report,
    generate_invoices_for_month,
    get_invoice_by_number,
    monthly_billing_summary,
    register_billing_customer,
)
from backend.services.water_ctaex_plans import (
    PUBLIC_PLANS,
    append_usage_log,
    consume_quota_or_raise,
    db_path,
    get_usage_report,
    hash_api_key,
    plan_allows_ollama,
    quota_enforcement_enabled,
)

logger = logging.getLogger(__name__)

water_ctaex_router = APIRouter(
    prefix="/water/ctaex",
    tags=["water_ctaex"],
    responses={404: {"description": "Not found"}},
)

router = water_ctaex_router

_ai_account_manager = AIAccountManager()
_ai_financial_analyst = AIFinancialAnalyst()
_ai_technical_support = AITechnicalSupport()


def _require_ai_integration_key(x_ai_key: str | None) -> None:
    """Misma semántica que otros secretos internos: 404 si falla (no filtrar existencia)."""
    secret = os.getenv("AI_INTEGRATION_KEY", "").strip()
    got = (x_ai_key or "").strip()
    if not secret or not got:
        raise HTTPException(status_code=404, detail="Not found")
    a, b = got.encode("utf-8"), secret.encode("utf-8")
    if len(a) != len(b) or not hmac.compare_digest(a, b):
        raise HTTPException(status_code=404, detail="Not found")


def _enterprise_blueprint_path() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "castuo_enterprise_eu.json"


class WaterSensorData(BaseModel):
    sensor_type: str = Field(
        ...,
        example="orp",
        description="Tipo de sensor: orp, tds o ph",
    )
    sensor_value: float = Field(
        ...,
        example=620.5,
        description="Valor medido por el sensor",
    )
    historical_data: list[dict[str, Any]] | None = Field(
        None,
        example=[{"sensor_value": 650, "timestamp": "2026-03-28T10:00:00Z"}],
        description="Datos históricos opcionales para análisis de tendencias",
    )


class WaterAnalysisResponse(BaseModel):
    status: str = Field(..., example="success")
    sensor_type: str = Field(..., example="orp")
    current_value: float = Field(..., example=620.5)
    analysis: dict[str, Any] = Field(..., description="Análisis por umbrales de proyecto")
    ollama_analysis: dict[str, Any] = Field(
        ...,
        description="Salida Ollama Cloud (chat) o disabled/fallback",
    )
    recommendations: list[str] = Field(
        ...,
        description="Recomendaciones (umbrales + extracto opcional de IA)",
    )
    disclaimer: str = Field(..., description="Advertencias sobre el uso de los datos")
    timestamp: str = Field(..., example="2026-03-28T12:34:56.789Z")
    plan_used: str | None = Field(
        None,
        description="Plan SaaS si WATER_CTAEX_ENFORCE_QUOTA=1",
    )
    remaining_requests: int | None = Field(
        None,
        description="Requests restantes este mes (None si ilimitado o sin cuota)",
    )
    quota_enforced: bool = Field(False, description="True si la cuota por API key está activa")


class SubscriptionUpgradeBody(BaseModel):
    plan_type: str = Field(..., description="free | basic | pro | enterprise")


class BillingRegisterBody(BaseModel):
    api_key: str = Field(..., min_length=8, description="Clave que el cliente usará en X-API-KEY")
    plan_id: str = Field(..., description="free | basic | pro | enterprise")
    customer_name: str = Field(..., min_length=1)
    customer_email: str = Field(..., min_length=3)


def _hist_values(historical: list[dict[str, Any]] | None) -> list[float]:
    if not historical:
        return []
    out: list[float] = []
    for h in historical:
        if not isinstance(h, dict) or "sensor_value" not in h:
            continue
        try:
            out.append(float(h["sensor_value"]))
        except (TypeError, ValueError):
            continue
    return out


def _analyze_orp(current: float, historical: list[dict[str, Any]] | None) -> dict[str, Any]:
    historical_values = _hist_values(historical)
    avg = sum(historical_values) / len(historical_values) if historical_values else 0.0

    status = "optimal"
    if current < 600:
        status = "critical"
    elif current < 650:
        status = "warning"

    trend = "stable"
    if len(historical_values) > 1:
        last = historical_values[-1]
        if last and current > last * 1.1:
            trend = "rising"
        elif last and current < last * 0.9:
            trend = "falling"

    return {
        "status": status,
        "current_value": current,
        "historical_avg": avg,
        "trend": trend,
        "project_thresholds": {
            "critical": 600,
            "warning": 650,
            "optimal_min": 650,
            "optimal_max": 750,
        },
        "ctaex_reference": {
            "min_recommended": 600,
            "optimal_range": [650, 750],
        },
    }


def _analyze_tds(current: float, historical: list[dict[str, Any]] | None) -> dict[str, Any]:
    historical_values = _hist_values(historical)
    avg = sum(historical_values) / len(historical_values) if historical_values else 0.0

    status = "optimal"
    if current > 50:
        status = "critical"
    elif current > 40:
        status = "warning"

    return {
        "status": status,
        "current_value": current,
        "historical_avg": avg,
        "project_thresholds": {
            "critical": 50,
            "warning": 40,
            "optimal_max": 40,
        },
        "ctaex_reference": {
            "max_recommended": 50,
            "ideal": "<40",
        },
    }


def _analyze_ph(current: float, historical: list[dict[str, Any]] | None) -> dict[str, Any]:
    historical_values = _hist_values(historical)
    avg = sum(historical_values) / len(historical_values) if historical_values else 0.0

    status = "optimal"
    if current < 5.5 or current > 6.5:
        status = "critical"
    elif current < 5.8 or current > 6.2:
        status = "warning"

    return {
        "status": status,
        "current_value": current,
        "historical_avg": avg,
        "project_thresholds": {
            "critical_low": 5.5,
            "critical_high": 6.5,
            "optimal_min": 5.8,
            "optimal_max": 6.2,
        },
        "ctaex_reference": {
            "recommended_range": [5.5, 6.5],
            "optimal_range": [5.8, 6.2],
        },
    }


def _rule_recommendations(sensor_type: str, analysis: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []
    st = sensor_type.lower().strip()

    if st == "orp":
        if analysis["status"] == "critical":
            recommendations.append(
                f"Activar generador de ozono (ORP actual: {analysis['current_value']}mV < 600mV)"
            )
            recommendations.append("Verificar funcionamiento del generador de ozono")
        elif analysis["status"] == "warning":
            recommendations.append(
                f"Monitorear ORP cada 15 minutos (actual: {analysis['current_value']}mV)"
            )
        if analysis.get("trend") == "falling":
            recommendations.append("Investigar posible contaminación en el sistema")

    elif st == "tds":
        if analysis["status"] == "critical":
            recommendations.append(
                f"Activar sistema de ósmosis inversa (TDS actual: {analysis['current_value']}ppm > 50ppm)"
            )
            recommendations.append("Verificar membranas de ósmosis inversa")
        elif analysis["status"] == "warning":
            recommendations.append(
                f"Preparar activación de ósmosis si TDS sigue subiendo (actual: {analysis['current_value']}ppm)"
            )

    elif st == "ph":
        if analysis["status"] == "critical":
            recommendations.append(
                f"Ajustar pH a rango 5.8-6.2 (actual: {analysis['current_value']})"
            )
            recommendations.append("Verificar calibración del sensor de pH")
        elif analysis["status"] == "warning":
            recommendations.append("Monitorear pH cada 30 minutos")

    if analysis["status"] != "optimal":
        recommendations.append("Revisar registros históricos para identificar patrones")
        recommendations.append("Notificar al equipo de mantenimiento si persiste")

    return recommendations


def _merge_recommendations(
    sensor_type: str,
    basic_analysis: dict[str, Any],
    ollama_analysis: dict[str, Any],
) -> list[str]:
    out = _rule_recommendations(sensor_type, basic_analysis)
    mu = ollama_analysis.get("model_used")
    text = (ollama_analysis.get("analysis") or "").strip()
    if mu not in ("disabled", "fallback") and text:
        snippet = " ".join(text.split())[:400]
        if len(text) > 400:
            snippet += "…"
        out.append(f"IA (Ollama, resumen): {snippet}")
    return out


_DISCLAIMER_BASE = (
    "Este análisis se basa en umbrales configurados para el proyecto CASTÚO. "
    "Para certificación oficial CTAEX, consulte con un laboratorio acreditado. "
    "Los valores umbral pueden variar según condiciones específicas de cultivo. "
    "No constituye garantía de calidad microbiológica ni certificación oficial."
)

_OLLAMA_EXTRA = (
    " Si OLLAMA_API_KEY está definida, se añade texto generado por modelo remoto (Ollama Cloud); "
    "revise la política de tratamiento de datos del proveedor. Ese texto no sustituye criterio agronómico ni auditoría."
)


async def _analyze_with_ollama_cloud(data: WaterSensorData, basic: dict[str, Any]) -> dict[str, Any]:
    key = os.getenv("OLLAMA_API_KEY", "").strip()
    base = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com/v1").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip()
    ts = datetime.now(timezone.utc).isoformat()

    if not key:
        return {
            "model_used": "disabled",
            "analysis": "",
            "timestamp": ts,
        }

    prompt = (
        f"Eres ingeniero agrícola en hidroponía de invernadero (referencia de proyecto, no prescripción médica).\n"
        f"Sensor: {data.sensor_type}. Valor actual: {data.sensor_value}. "
        f"Estado por umbrales (proyecto): {basic.get('status')}. "
        f"Resume en español: causas posibles si está fuera de rango, 3 acciones concretas de revisión de equipo, "
        f"y una frase sobre impacto en cultivo de hoja (sin diagnóstico patológico). Máximo ~250 palabras."
    )

    url = f"{base}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            r.raise_for_status()
            body = r.json()
            choices = body.get("choices") or []
            if not choices:
                raise ValueError("Respuesta sin choices")
            content = (choices[0].get("message") or {}).get("content") or ""
            return {
                "model_used": model,
                "analysis": str(content).strip(),
                "timestamp": ts,
            }
    except Exception as e:
        logger.warning("Ollama Cloud no disponible o error HTTP: %s", e)
        return {
            "model_used": "fallback",
            "analysis": "Análisis por IA no disponible; se usan solo umbrales de proyecto.",
            "error": str(e),
            "timestamp": ts,
        }


def _disclaimer(ollama_active: bool) -> str:
    if ollama_active:
        return _DISCLAIMER_BASE + _OLLAMA_EXTRA
    return _DISCLAIMER_BASE


@water_ctaex_router.get("/subscription/plans")
async def list_subscription_plans() -> dict[str, Any]:
    """Catálogo público de planes (precios orientativos; cobro vía Stripe u operador)."""
    plans_out = []
    for pid, cfg in PUBLIC_PLANS.items():
        plans_out.append(
            {
                "id": pid,
                "name": cfg.get("name", pid),
                "description": cfg.get("description", ""),
                "price_eur_month": cfg.get("price_eur_month"),
                "max_requests": cfg["max_requests"],
                "features": list(cfg.get("features", [])),
                "ollama_included": cfg.get("ollama", False),
                "automaton_included": cfg.get("automaton", False),
            }
        )
    return {
        "currency": "EUR",
        "billing_cycle": "monthly",
        "plans": plans_out,
        "contact": os.getenv("CASTUO_SALES_EMAIL", "sales@castuo-system.es"),
    }


@water_ctaex_router.post("/subscription/register")
async def subscription_register_customer(
    body: BillingRegisterBody,
    x_billing_register_key: str | None = Header(None, alias="X-BILLING-REGISTER-KEY"),
) -> dict[str, Any]:
    """Registra cliente de facturación (solo hash en BD). Requiere WATER_BILLING_REGISTER_KEY."""
    secret = os.getenv("WATER_BILLING_REGISTER_KEY", "").strip()
    if not secret or (x_billing_register_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        row = register_billing_customer(
            api_key=body.api_key.strip(),
            plan_id=body.plan_id.strip().lower(),
            customer_name=body.customer_name,
            customer_email=body.customer_email,
        )
        return {
            "status": "success",
            "api_key_hash": hash_api_key(body.api_key.strip()),
            **row,
        }
    except ValueError as e:
        if str(e) == "invalid_plan":
            raise HTTPException(status_code=400, detail="plan_id inválido") from e
        raise HTTPException(status_code=400, detail=str(e)) from e


@water_ctaex_router.get("/subscription/billing-summary")
async def subscription_billing_summary(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    x_usage_report_key: str | None = Header(None, alias="X-USAGE-REPORT-KEY"),
) -> dict[str, Any]:
    secret = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    if not secret or (x_usage_report_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        data = monthly_billing_summary(year, month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"year": year, "month": month, **data}


@water_ctaex_router.post("/subscription/generate-invoices")
async def subscription_generate_invoices(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    x_usage_report_key: str | None = Header(None, alias="X-USAGE-REPORT-KEY"),
) -> dict[str, Any]:
    secret = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    if not secret or (x_usage_report_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        created = generate_invoices_for_month(year, month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    period_yyyymm = f"{year}{month:02d}"
    ts = datetime.now(timezone.utc).isoformat()
    return {
        "status": "success",
        "period": f"{year}-{month:02d}",
        "period_yyyymm": period_yyyymm,
        "invoices_generated": len(created),
        "generated": len(created),
        "invoices": created,
        "timestamp": ts,
    }


@water_ctaex_router.get("/subscription/certification")
async def subscription_certification(
    year: int | None = Query(None, ge=2020, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    x_usage_report_key: str | None = Header(None, alias="X-USAGE-REPORT-KEY"),
) -> dict[str, Any]:
    """Informe certificable (JSON) para un mes; mismo secreto que usage-report."""
    secret = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    if not secret or (x_usage_report_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    now = datetime.now(timezone.utc)
    y = year if year is not None else now.year
    mo = month if month is not None else now.month
    try:
        return generate_certification_report(y, mo)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@water_ctaex_router.get("/subscription/ai/enterprise-blueprint")
async def subscription_ai_enterprise_blueprint(
    x_ai_key: str | None = Header(None, alias="X-AI-KEY"),
) -> dict[str, Any]:
    """Blueprint organizativo EU (JSON estático en `config/castuo_enterprise_eu.json`)."""
    _require_ai_integration_key(x_ai_key)
    p = _enterprise_blueprint_path()
    if not p.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return json.loads(p.read_text(encoding="utf-8"))


@water_ctaex_router.post("/subscription/ai/register")
async def subscription_ai_register_customer(
    body: BillingRegisterBody,
    x_ai_key: str | None = Header(None, alias="X-AI-KEY"),
) -> dict[str, Any]:
    """Registro de facturación vía agente (habilitar con AI_ACCOUNT_MANAGER_ENABLED=1)."""
    _require_ai_integration_key(x_ai_key)
    return _ai_account_manager.register_customer(
        api_key=body.api_key,
        plan_id=body.plan_id,
        customer_name=body.customer_name,
        customer_email=body.customer_email,
    )


@water_ctaex_router.get("/subscription/ai/monitoring")
async def subscription_ai_monitoring(
    year: int | None = Query(None, ge=2020, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    x_ai_key: str | None = Header(None, alias="X-AI-KEY"),
) -> dict[str, Any]:
    """Informe mensual + certificación para el mes indicado (por defecto UTC actual)."""
    _require_ai_integration_key(x_ai_key)
    now = datetime.now(timezone.utc)
    y = year if year is not None else now.year
    mo = month if month is not None else now.month
    return _ai_financial_analyst.generate_monthly_report(y, mo)


@water_ctaex_router.get("/subscription/ai/health")
async def subscription_ai_health(
    x_ai_key: str | None = Header(None, alias="X-AI-KEY"),
) -> dict[str, Any]:
    """Health vía HTTP interno (API_BASE_URL); para agentes de soporte."""
    _require_ai_integration_key(x_ai_key)
    return _ai_technical_support.check_health()


@water_ctaex_router.post("/subscription/send-invoice")
async def subscription_send_invoice(
    invoice_number: str = Query(..., min_length=4, description="Número devuelto al generar o patrón INV-YYYYMM-…"),
    x_usage_report_key: str | None = Header(None, alias="X-USAGE-REPORT-KEY"),
) -> dict[str, Any]:
    """Envía la factura por SMTP (plantilla HTML). Requiere credenciales SMTP en el servidor."""
    secret = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    if not secret or (x_usage_report_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    inv = get_invoice_by_number(invoice_number.strip())
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    sent = send_invoice_email(inv)
    return {
        "status": "success",
        "invoice_number": invoice_number.strip(),
        "sent": sent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@water_ctaex_router.get("/subscription/invoice/{invoice_number}")
async def subscription_get_invoice(
    invoice_number: str,
    x_usage_report_key: str | None = Header(None, alias="X-USAGE-REPORT-KEY"),
) -> dict[str, Any]:
    secret = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    if not secret or (x_usage_report_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    inv = get_invoice_by_number(invoice_number)
    if not inv:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return inv


@water_ctaex_router.get("/subscription/usage-report")
async def subscription_usage_report(
    limit: int = Query(100, ge=1, le=2000),
    plan_id: str | None = None,
    x_usage_report_key: str | None = Header(None, alias="X-USAGE-REPORT-KEY"),
) -> dict[str, Any]:
    """Trazas recientes (key_hash, no clave). Requiere WATER_USAGE_REPORT_KEY en servidor y cabecera coincidente."""
    secret = os.getenv("WATER_USAGE_REPORT_KEY", "").strip()
    if not secret or (x_usage_report_key or "").strip() != secret:
        raise HTTPException(status_code=404, detail="Not found")
    items = get_usage_report(limit=limit, plan_id=plan_id)
    return {
        "items": items,
        "report": items,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path()),
    }


@water_ctaex_router.post("/subscription/upgrade")
async def subscription_upgrade(body: SubscriptionUpgradeBody) -> dict[str, Any]:
    """Puente comercial: enterprise → presupuesto; resto → Stripe/checkout externo (ver CTAEX /ecommerce)."""
    if body.plan_type not in PUBLIC_PLANS:
        raise HTTPException(status_code=400, detail="plan_type inválido")
    sales = os.getenv("CASTUO_SALES_EMAIL", "sales@castuo-system.es")
    if body.plan_type == "enterprise":
        return {
            "status": "quote_required",
            "contact": sales,
            "message": "Enterprise requiere presupuesto y acuerdo de nivel de servicio.",
        }
    price = PUBLIC_PLANS[body.plan_type].get("price_eur_month")
    return {
        "status": "checkout_pending",
        "message": (
            "Tras el pago, asigna la clave del cliente en WATER_API_KEY_TO_PLAN o integra Stripe "
            "con webhook propio. Checkout CTAEX existente: POST /ecommerce/create-checkout (roles admin/ecommerce)."
        ),
        "requested_plan": body.plan_type,
        "reference_price_eur_month": price,
        "contact": sales,
    }


@water_ctaex_router.post("/analyze", response_model=WaterAnalysisResponse)
async def analyze_water_data(
    data: WaterSensorData,
    x_api_key: str | None = Header(None, alias="X-API-KEY"),
) -> WaterAnalysisResponse:
    """
    Umbrales de proyecto + texto opcional vía Ollama Cloud (OPENAI-compatible /v1/chat/completions).
    Si WATER_CTAEX_ENFORCE_QUOTA=1: exige X-API-KEY, aplica límites y gating de Ollama por plan.
    """
    st = data.sensor_type.lower().strip()
    enforce = quota_enforcement_enabled()
    plan_id: str | None = None
    remaining: int | None = None

    try:
        if st not in ("orp", "tds", "ph"):
            raise HTTPException(
                status_code=400,
                detail="Tipo de sensor no soportado. Use: orp, tds o ph",
            )

        if enforce:
            if not x_api_key or not x_api_key.strip():
                raise HTTPException(
                    status_code=401,
                    detail="X-API-KEY requerida cuando WATER_CTAEX_ENFORCE_QUOTA está activo",
                )
            try:
                plan_id, _, remaining = consume_quota_or_raise(x_api_key.strip())
            except ValueError:
                raise HTTPException(
                    status_code=403,
                    detail="API key no reconocida. Configure WATER_API_KEY_TO_PLAN.",
                ) from None
            except OverflowError:
                raise HTTPException(
                    status_code=429,
                    detail="Límite mensual de requests alcanzado para este plan.",
                ) from None

        if st == "orp":
            analysis = _analyze_orp(data.sensor_value, data.historical_data)
        elif st == "tds":
            analysis = _analyze_tds(data.sensor_value, data.historical_data)
        else:
            analysis = _analyze_ph(data.sensor_value, data.historical_data)

        use_ollama = True
        if enforce and plan_id:
            use_ollama = plan_allows_ollama(plan_id)

        if use_ollama:
            ollama_analysis = await _analyze_with_ollama_cloud(data, analysis)
        else:
            ollama_analysis = {
                "model_used": "disabled",
                "analysis": "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": "plan_does_not_include_ollama",
            }

        ollama_key_set = bool(os.getenv("OLLAMA_API_KEY", "").strip()) and use_ollama

        if enforce and plan_id and x_api_key and x_api_key.strip():
            append_usage_log(
                api_key=x_api_key.strip(),
                plan_id=plan_id,
                endpoint="/water/ctaex/analyze",
                input_payload={
                    "sensor_type": st,
                    "sensor_value": data.sensor_value,
                    "historical_points": len(data.historical_data or []),
                },
                http_status=200,
            )

        return WaterAnalysisResponse(
            status="success",
            sensor_type=st,
            current_value=data.sensor_value,
            analysis=analysis,
            ollama_analysis=ollama_analysis,
            recommendations=_merge_recommendations(st, analysis, ollama_analysis),
            disclaimer=_disclaimer(ollama_key_set),
            timestamp=datetime.now(timezone.utc).isoformat(),
            plan_used=plan_id,
            remaining_requests=remaining,
            quota_enforced=enforce,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en análisis de agua: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e!s}") from e


@water_ctaex_router.get("/health")
async def health_check() -> dict[str, Any]:
    """Endpoint de salud para monitoreo del servicio."""
    ollama_key = bool(os.getenv("OLLAMA_API_KEY", "").strip())
    return {
        "status": "healthy",
        "endpoints": [
            {
                "path": "/water/ctaex/analyze",
                "method": "POST",
                "description": "Analiza datos de sensores de agua (ORP/TDS/pH); opcional Ollama Cloud",
                "parameters": {
                    "sensor_type": ["orp", "tds", "ph"],
                    "sensor_value": "float",
                    "historical_data": "opcional (lista de valores históricos)",
                },
            }
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.7",
        "ollama_configured": ollama_key,
        "water_quota_enforcement": quota_enforcement_enabled(),
        "subscription_plans": "/water/ctaex/subscription/plans",
        "water_quota_db": str(db_path()),
    }
