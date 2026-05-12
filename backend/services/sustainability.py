# -*- coding: utf-8 -*-
"""
Sostenibilidad y huella de carbono — CASTÚO (SABIONDA_MASTER v4.1).

Referencia: docs/ai/Prompt-Guide-v4.1.md — Reglas de negocio para IA.
Cada decisión puede considerar reducción de huella (riego, energía, agrovoltaica).
"""
from __future__ import annotations

from typing import Any, Dict


def estimate_carbon_impact(
    action: str,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Estima el impacto en huella de carbono de una acción (ej. riego, energía).

    Args:
        action: Tipo de acción (ej. "irrigation", "lighting", "heating").
        params: Parámetros (duración, kWh, m³ agua, etc.).

    Returns:
        dict: co2_kg_equivalent, recommendation, ods_related.
    """
    params = params or {}
    # Placeholder: en producción integrar con datos reales (sensores, factores de emisión)
    co2_kg = 0.0
    recommendation = "Sin datos específicos; revisar factores de emisión por actividad."
    ods_related = ["ODS 7", "ODS 13"]

    if action == "irrigation":
        volume_m3 = params.get("volume_m3", 0)
        co2_kg = volume_m3 * 0.2  # Factor simplificado (bombeo, tratamiento)
        recommendation = "Optimizar riego con sensores de humedad para reducir volumen."
    elif action == "lighting" or action == "energy":
        kwh = params.get("kwh", 0)
        co2_kg = kwh * 0.3  # Factor simplificado (mix eléctrico)
        recommendation = "Priorizar energía solar (agrovoltaica) para reducir emisiones."

    return {
        "action": action,
        "co2_kg_equivalent": round(co2_kg, 2),
        "recommendation": recommendation,
        "ods_related": ods_related,
    }
