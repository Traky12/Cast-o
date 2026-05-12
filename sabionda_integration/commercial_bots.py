from datetime import datetime
import logging
from typing import Any, Dict

import httpx
from fastapi import FastAPI, HTTPException


app = FastAPI()
logging.basicConfig(level=logging.INFO)


COMMERCIAL_BOTS = {
    "offer_bot": "http://localhost:8007",
    "negotiation_bot": "http://localhost:8008",
    "loyalty_bot": "http://localhost:8009",
}


async def call_commercial_bot(
    bot_name: str, endpoint: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{COMMERCIAL_BOTS[bot_name]}/{endpoint}",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logging.error("Error al llamar al bot %s: %s", bot_name, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/orchestrate/commercial-offer")
async def orchestrate_commercial_offer(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        offer = await call_commercial_bot(
            "offer_bot",
            "generate-offer",
            {
                "token_id": data["token_id"],
                "parcel_data": data["parcel_data"],
            },
        )
        negotiation = await call_commercial_bot(
            "negotiation_bot",
            "negotiate",
            {
                "token_id": data["token_id"],
                "wood_offer": offer["wood_sale_offer"],
                "buyer_profile": data.get("buyer_profile", "equilibrado"),
            },
        )
        offer["wood_sale_offer"] = negotiation["optimized_offer"]
        loyalty = await call_commercial_bot(
            "loyalty_bot",
            "recommend-actions",
            {
                "client_id": data["client_id"],
                "recent_activity": {
                    "last_purchase": datetime.utcnow().strftime("%Y-%m-%d"),
                    "purchase_value": offer["wood_sale_offer"]["total_wood_value"],
                    "interaction_type": "commercial_offer",
                },
            },
        )
        confidence = round(
            (
                offer.get("confidence", 0.95)
                + negotiation.get("confidence", 0.9)
                + loyalty.get("confidence", 0.9)
            )
            / 3,
            2,
        )
        return {
            "carbon_credit_offer": offer["carbon_credit_offer"],
            "wood_sale_offer": offer["wood_sale_offer"],
            "subsidy_optimization": offer["subsidy_optimization"],
            "loyalty_recommendations": loyalty["recommended_actions"],
            "confidence": confidence,
            "feedback_request": (
                "¿Te parece adecuado este paquete comercial? "
                "Tu feedback (sí/no/ajustar) nos ayuda a mejorar. "
                f"(ID: COM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')})"
            ),
        }
    except Exception as e:
        logging.error("Error en orquestación comercial: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-commercial-knowledge")
async def update_commercial_knowledge(feedback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if "offer_bot" in feedback.get("bot_responses", {}):
            await call_commercial_bot(
                "offer_bot",
                "update-knowledge",
                {
                    "offer_id": feedback.get("feedback_id"),
                    "user_response": feedback.get("offer_response"),
                    "suggested_changes": feedback["bot_responses"]["offer_bot"].get(
                        "changes", {}
                    ),
                },
            )
        if "negotiation_bot" in feedback.get("bot_responses", {}):
            await call_commercial_bot(
                "negotiation_bot",
                "update-negotiation-knowledge",
                {
                    "negotiation_id": feedback.get("feedback_id"),
                    "accepted": feedback["bot_responses"]["negotiation_bot"].get(
                        "accepted", False
                    ),
                    "final_offer": feedback.get("final_offer", {}),
                },
            )
        if "loyalty_bot" in feedback.get("bot_responses", {}):
            await call_commercial_bot(
                "loyalty_bot",
                "update-loyalty-model",
                {
                    "client_id": feedback.get("client_id"),
                    "recommendation_id": "loyalty_recommendations",
                    "user_response": (
                        "accepted"
                        if feedback["bot_responses"]["loyalty_bot"].get("useful")
                        else "rejected"
                    ),
                    "notes": feedback.get("notes", ""),
                },
            )
        return {
            "status": "success",
            "message": "Conocimiento comercial actualizado con feedback.",
            "bots_updated": list(feedback.get("bot_responses", {}).keys()),
        }
    except Exception as e:
        logging.error("Error actualizando conocimiento comercial: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010, log_level="info")

