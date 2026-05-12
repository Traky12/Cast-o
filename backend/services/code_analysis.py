# -*- coding: utf-8 -*-
"""
Análisis de código según estándares CASTÚO-SYSTEM (SABIONDA_MASTER v4.1).

Referencia: docs/ai/Prompt-Guide-v4.1.md
Valida cumplimiento GDPR, AEMPS, GaiaChain, LIMS, AI Act y sugiere correcciones.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List


def _check_gdpr(code_snippet: str) -> bool:
    """Comprueba si el código referencia enmascaramiento GDPR o middleware."""
    patterns = [
        r"gdpr|GDPR|enmascarar|mask|middleware.*gdpr|user_data.*nif|user_data.*email",
        r"gdpr\.py|gdpr_middleware",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def _check_aemps(code_snippet: str, context: Dict[str, Any]) -> bool:
    """Comprueba si hay validación THC/certificación AEMPS cuando el contexto es cannabis."""
    if context.get("system") != "cannabis":
        return True
    patterns = [
        r"thc.*0\.3|0\.3.*thc|RD\s*903|903/2025",
        r"certify_aemps|certify.*aemps|aemps",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def _check_ai_act(code_snippet: str) -> bool:
    """Comprueba si hay validación de modelos IA (transparencia, precisión)."""
    patterns = [
        r"ai_compliance|AIModelValidation|accuracy|transparency",
        r"min_accuracy|0\.95",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def _check_sustainability(code_snippet: str) -> bool:
    """Comprueba si se considera sostenibilidad/huella de carbono."""
    patterns = [
        r"sustainability|co2|carbono|huella|ODS",
        r"carbon_footprint|renewable",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def _has_gaiachain_integration(code_snippet: str) -> bool:
    """Comprueba si hay registro en GaiaChain."""
    patterns = [
        r"gaia_chain|GaiaChainService|register_batch|register_batch\(",
        r"blockchain_tx|tx_hash",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def _has_calibration(code_snippet: str) -> bool:
    """Comprueba si se usa calibración de sensores (IoT)."""
    patterns = [
        r"calibration|SensorCalibration|calibrate\(\)",
        r"calibration\.py",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def _has_lims_validation(code_snippet: str) -> bool:
    """Comprueba si hay validación con LIMS (sync, THC/CBD)."""
    patterns = [
        r"lims_sync|sync_with_lims|LIMS",
        r"sync/lims",
    ]
    return any(re.search(p, code_snippet, re.IGNORECASE) for p in patterns)


def analyze_code(
    code_snippet: str,
    context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Analiza un fragmento de código según estándares CASTÚO-SYSTEM.

    Args:
        code_snippet: Código a analizar (Python, Solidity, etc.).
        context: Contexto adicional (ej: {"system": "cannabis", "action": "certify"}).

    Returns:
        dict: status, issues, suggestions, compliance, blockchain_tx (opcional).
    """
    context = context or {}
    issues: List[str] = []
    suggestions: List[str] = []

    # 1. Cumplimiento normativo
    compliance = {
        "gdpr": _check_gdpr(code_snippet),
        "aemps": _check_aemps(code_snippet, context),
        "ai_act": _check_ai_act(code_snippet) if "ai" in str(context).lower() else True,
        "sustainability": _check_sustainability(code_snippet),
    }

    if not compliance["gdpr"]:
        issues.append("Falta enmascaramiento de datos personales (GDPR Art. 25).")
        suggestions.append("Añadir middleware/gdpr.py o enmascarar user_data en respuestas JSON.")

    if not compliance["aemps"] and context.get("system") == "cannabis":
        issues.append("Falta validación con LIMS/AEMPS (THC < 0,3 %, RD 903/2025).")
        suggestions.append("Validar THC y usar lims_sync.py o cannabis/certify_aemps.")

    if not _has_gaiachain_integration(code_snippet) and context.get("system") in ("cannabis", "microgreens"):
        issues.append("La acción no se registra en GaiaChain. Usar gaia_chain.py.")
        suggestions.append("Llamar a GaiaChainService.register_batch() después de certificar.")

    if not _has_lims_validation(code_snippet) and context.get("system") == "cannabis":
        issues.append("Falta validación con LIMS de CTAEX. Usar lims_sync.py.")
        suggestions.append("Validar datos de laboratorio (THC, CBD) con LIMS antes de emitir certificado.")

    if context.get("system") == "iot" and not _has_calibration(code_snippet):
        issues.append("Falta calibración de sensores. Usar calibration.py.")
        suggestions.append("Aplicar SensorCalibration().calibrate() a valores crudos.")

    # blockchain_tx: en producción se podría registrar el análisis en GaiaChain
    blockchain_tx = None

    if issues:
        return {
            "status": "error",
            "issues": issues,
            "suggestions": suggestions,
            "compliance": compliance,
            "blockchain_tx": blockchain_tx,
        }
    return {
        "status": "success",
        "issues": [],
        "suggestions": ["Código alineado con CASTÚO. ¿Desplegar en staging?"],
        "compliance": compliance,
        "blockchain_tx": blockchain_tx,
    }
