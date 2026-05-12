from datetime import datetime
import json
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.cluster import KMeans


app = FastAPI()
logging.basicConfig(level=logging.INFO)


CLIENT_DATA: List[Dict[str, Any]] = [
    {
        "client_id": "CLI-001",
        "transactions": 5,
        "avg_value": 1200,
        "last_transaction": "2026-01-15",
        "certifications": ["PEFC"],
    },
    {
        "client_id": "CLI-002",
        "transactions": 12,
        "avg_value": 2500,
        "last_transaction": "2026-03-20",
        "certifications": ["PEFC", "FSC"],
    },
    {
        "client_id": "CLI-003",
        "transactions": 2,
        "avg_value": 800,
        "last_transaction": "2025-11-10",
        "certifications": [],
    },
]


class LoyaltyRequest(BaseModel):
    client_id: str
    recent_activity: Dict[str, Any]


class LoyaltyResponse(BaseModel):
    client_segment: str
    recommended_actions: List[Dict[str, Any]]
    confidence: float
    feedback_request: str


def _load_client_data() -> pd.DataFrame:
    df = pd.DataFrame(CLIENT_DATA)
    df["days_since_last"] = (
        datetime.now() - pd.to_datetime(df["last_transaction"])
    ).dt.days
    df["certification_count"] = df["certifications"].apply(len)
    return df[
        ["transactions", "avg_value", "days_since_last", "certification_count"]
    ]


def _cluster_clients(df: pd.DataFrame) -> Dict[int, int]:
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(df)
    return dict(zip(df.index, clusters))


CLIENT_SEGMENTS = _cluster_clients(_load_client_data())


def _generate_recommendations(
    segment: int, recent_activity: Dict[str, Any]
) -> List[Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []
    if segment == 0:
        recommendations.extend(
            [
                {
                    "action": "offer_premium_support",
                    "description": (
                        "Ofrecer soporte prioritario para talas legales y gestión de "
                        "certificaciones."
                    ),
                    "expected_impact": "Aumentar retención en un 15%.",
                },
                {
                    "action": "carbon_credit_bundle",
                    "description": (
                        "Paquete de créditos de carbono con descuento del 10% "
                        f"(valor: ~€{recent_activity.get('purchase_value', 0) * 0.3})."
                    ),
                    "expected_impact": "Aumentar ingresos por carbono en un 20%.",
                },
            ]
        )
    elif segment == 1:
        recommendations.extend(
            [
                {
                    "action": "certification_upsell",
                    "description": (
                        "Recomendar obtener certificación FSC (coste: ~€500, ROI: 2 años)."
                    ),
                    "expected_impact": "Aumentar subvenciones en €150/ha/año.",
                },
                {
                    "action": "seasonal_discount",
                    "description": (
                        "Descuento del 5% en venta de madera si se realiza antes de junio 2026."
                    ),
                    "expected_impact": "Anticipar ingresos en Q2 2026.",
                },
            ]
        )
    else:
        recommendations.extend(
            [
                {
                    "action": "reactivation_campaign",
                    "description": (
                        "Campaña de reactivación con oferta de análisis gratuito de carbono."
                    ),
                    "expected_impact": "Aumentar actividad en un 30%.",
                },
                {
                    "action": "subsidy_reminder",
                    "description": (
                        "Recordatorio de subvenciones no reclamadas (ej: Decreto 45/2020)."
                    ),
                    "expected_impact": "Recuperar €300/ha en subvenciones no cobradas.",
                },
            ]
        )
    if recent_activity.get("interaction_type") == "subsidy_claim":
        recommendations.append(
            {
                "action": "cross_sell_carbon",
                "description": (
                    "Ofrecer tokenizar créditos de carbono por "
                    f"{recent_activity.get('purchase_value', 0) * 0.2}€ adicionales."
                ),
                "expected_impact": "Aumentar ingresos por carbono en un 25%.",
            }
        )
    return recommendations


@app.post("/recommend-actions", response_model=LoyaltyResponse)
async def recommend_actions(request: LoyaltyRequest) -> Dict[str, Any]:
    try:
        client_index = next(
            i
            for i, client in enumerate(CLIENT_DATA)
            if client["client_id"] == request.client_id
        )
        segment = CLIENT_SEGMENTS[client_index]
        recommendations = _generate_recommendations(
            segment, request.recent_activity
        )
        confidence = 0.95 if segment in (0, 1) else 0.8
        return {
            "client_segment": f"Segmento {segment}",
            "recommended_actions": recommendations,
            "confidence": confidence,
            "feedback_request": (
                "¿Te parecen útiles estas recomendaciones? "
                "Tu feedback (sí/no/ajustar) nos ayuda a mejorar."
            ),
        }
    except Exception as e:
        logging.error("Error generando recomendaciones: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-loyalty-model")
async def update_loyalty_model(feedback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        feedback["timestamp"] = datetime.now().isoformat()
        log_path = "loyalty_feedback.json"
        with open(log_path, "a", encoding="utf-8") as f:
            json.dump(feedback, f)
            f.write("\n")
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
        if len(lines) and len(lines) % 100 == 0:
            global CLIENT_SEGMENTS
            CLIENT_SEGMENTS = _cluster_clients(_load_client_data())
        return {
            "status": "success",
            "message": "Modelo de fidelización actualizado con nuevo feedback.",
            "next_retraining": "2026-05-01",
        }
    except Exception as e:
        logging.error("Error actualizando modelo de fidelización: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8009, log_level="info")

