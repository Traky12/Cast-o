# -*- coding: utf-8 -*-
"""Endpoints para calibración UE, cumplimiento normativo y usabilidad (Etapas 1 y 5)."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.services.calibration import SensorCalibration
from backend.services.ai_compliance import AIModelValidation
from backend.services.ai_transparency import AITransparencyReport
from backend.services.compliance_check import ComplianceCheck
from backend.models.usability import UsabilityFeedback

router = APIRouter()


# --- Calibración sensores (Etapa 1) ---
@router.post("/calibrate")
async def calibrate_sensor(cal: SensorCalibration):
    """Calibra un valor de sensor según estándares UE (ISO 17025, Reglamento 2018/848)."""
    try:
        return cal.calibrate().model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Validación modelos IA (AI Act) ---
@router.post("/ai/validate")
async def validate_ai_model(body: AIModelValidation):
    """Valida un modelo de IA según AI Act UE 2024/1689."""
    return body.validate()


# --- Informe transparencia AI Act Art. 13 ---
@router.post("/ai/transparency")
async def ai_transparency_report(body: AITransparencyReport):
    """Genera informe de transparencia según Art. 13 AI Act."""
    return body.generate_report()


# --- Checklist cumplimiento normativo (Etapa 5) ---
@router.post("/compliance/check")
async def compliance_check(system_data: Dict[str, Any]):
    """Ejecuta checklist de cumplimiento GDPR, AI Act, PAC 2026, GlobalGAP, AEMPS."""
    check = ComplianceCheck()
    return check.check_all(system_data)


# --- Feedback usabilidad (pruebas usuarios europeos) ---
@router.post("/usability/feedback")
async def usability_feedback(feedback: UsabilityFeedback):
    """Registra feedback de usabilidad (España, Francia, Alemania)."""
    return {
        "status": "recorded",
        "user_id": feedback.user_id,
        "country": feedback.country,
        "task": feedback.task,
        "success": feedback.success,
        "time_seconds": feedback.time_seconds,
    }


# --- Análisis de código (SABIONDA_MASTER v4.1) ---
@router.post("/code/analyze")
async def analyze_code_endpoint(payload: Dict[str, Any]):
    """
    Analiza un fragmento de código según estándares CASTÚO (GDPR, GaiaChain, LIMS, AI Act).
    Body: {"code_snippet": "...", "context": {"system": "cannabis"|"iot"|"microgreens", ...}}
    """
    from backend.services.code_analysis import analyze_code
    code_snippet = payload.get("code_snippet", "")
    context = payload.get("context") or {}
    return analyze_code(code_snippet, context)
