# -*- coding: utf-8 -*-
"""Predicción de demanda con Mistral (opcional)."""
from typing import Any, Dict, List, Optional


def predict_with_mistral(
    material_id: int,
    days_ahead: int,
    history_kg_sold: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Stub: en producción usar transformers/API Mistral con prompt de predicción."""
    from .demand_prediction import simple_fallback_prediction
    return simple_fallback_prediction(material_id, days_ahead, history_kg_sold)
