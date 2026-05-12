# -*- coding: utf-8 -*-
"""API de IA: predicción de demanda."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ia", tags=["ia"])


class PredictDemandBody(BaseModel):
    material_id: int
    days_ahead: int = 7
    use_ai: bool = False
    history_kg_sold: Optional[List[Dict[str, Any]]] = None


def _fallback_predict(material_id: int, days_ahead: int, history: Optional[List[Dict]] = None) -> Dict:
    if not history or len(history) < 3:
        avg = 10.0
    else:
        kgs = [h.get("kg", 0) for h in history[-14:]]
        avg = sum(kgs) / len(kgs) if kgs else 10.0
    base = datetime.now().date()
    predictions = [
        {"date": (base + timedelta(days=i)).strftime("%Y-%m-%d"), "kg": round(avg, 2)}
        for i in range(1, days_ahead + 1)
    ]
    return {
        "material_id": material_id,
        "predictions": predictions,
        "method": "fallback",
        "avg_daily_kg": round(avg, 2),
    }


@router.post("/predict_demand")
async def predict_demand(body: PredictDemandBody):
    """Predice demanda para un material (fallback: promedio móvil)."""
    try:
        from ia.demand_prediction import predict_demand as _predict
        result = _predict(
            body.material_id,
            body.days_ahead,
            body.history_kg_sold,
            body.use_ai,
        )
    except ImportError:
        result = _fallback_predict(
            body.material_id,
            body.days_ahead,
            body.history_kg_sold,
        )
    return result
