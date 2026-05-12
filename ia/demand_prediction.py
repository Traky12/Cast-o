# -*- coding: utf-8 -*-
"""Predicción de demanda para materiales (fallback: promedio móvil; opcional: Mistral/Prophet)."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import logging
logger = logging.getLogger(__name__)


def simple_fallback_prediction(
    material_id: int,
    days_ahead: int = 7,
    history_kg_sold: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Predicción por promedio móvil de 7 días. history_kg_sold: [{'date': 'YYYY-MM-DD', 'kg': float}, ...]."""
    if not history_kg_sold or len(history_kg_sold) < 3:
        avg_demand = 10.0  # default
    else:
        kgs = [h["kg"] for h in history_kg_sold[-14:]]
        avg_demand = sum(kgs) / len(kgs) if kgs else 10.0

    base = datetime.now().date()
    predictions = [
        {"date": (base + timedelta(days=i)).strftime("%Y-%m-%d"), "kg": round(avg_demand, 2)}
        for i in range(1, days_ahead + 1)
    ]
    return {
        "material_id": material_id,
        "predictions": predictions,
        "method": "fallback",
        "avg_daily_kg": round(avg_demand, 2),
    }


def predict_demand(
    material_id: int,
    days_ahead: int = 7,
    history_kg_sold: Optional[List[Dict[str, Any]]] = None,
    use_ai: bool = False,
) -> Dict[str, Any]:
    """Predice demanda. use_ai=True intenta Mistral si está disponible."""
    if use_ai:
        try:
            from .mistral_demand import predict_with_mistral
            return predict_with_mistral(material_id, days_ahead, history_kg_sold or [])
        except Exception as e:
            logger.warning("Mistral demand prediction failed: %s", e)
    return simple_fallback_prediction(material_id, days_ahead, history_kg_sold)
