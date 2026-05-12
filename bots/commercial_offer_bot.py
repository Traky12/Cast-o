from datetime import datetime
import json
import logging
import os
from typing import Any, Dict

import httpx
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.cluster import KMeans


app = FastAPI()
logging.basicConfig(level=logging.INFO)


OFFER_KNOWLEDGE = {
    "carbon_credits": {
        "current_price": 50,
        "historical_prices": [48, 50, 52, 55, 50],
        "demand": "high",
        "suggested_offer": 52,
    },
    "subsidies": {
        "pac_2040": {"base": 200, "bonus": {"pefc": 150, "fsc": 150, "red_natura": 300}},
        "decreto_45_2020": {"bonus": 150},
    },
    "wood_prices": {
        "oak": {"current": 80, "historical": [75, 78, 80, 82, 80]},
        "pine": {"current": 60, "historical": [58, 59, 60, 62, 60]},
    },
}


class OfferRequest(BaseModel):
    token_id: int
    parcel_data: Dict[str, Any]


class OfferResponse(BaseModel):
    carbon_credit_offer: Dict[str, Any]
    wood_sale_offer: Dict[str, Any]
    subsidy_optimization: Dict[str, Any]
    confidence: float
    feedback_request: str


@app.post("/generate-offer", response_model=OfferResponse)
async def generate_offer(request: OfferRequest) -> Dict[str, Any]:
    try:
        area_ha = request.parcel_data["area"] / 10000
        carbon_tonnes = request.parcel_data["carbon_sequestered"] / 1000

        carbon_offer = _generate_carbon_offer(carbon_tonnes)
        wood_offer = _generate_wood_offer(request.parcel_data)
        subsidy_opt = _optimize_subsidies(request.parcel_data, area_ha)
        confidence = _calculate_confidence(carbon_offer, wood_offer)

        return {
            "carbon_credit_offer": carbon_offer,
            "wood_sale_offer": wood_offer,
            "subsidy_optimization": subsidy_opt,
            "confidence": confidence,
            "feedback_request": (
                "¿Te parece adecuada esta oferta? "
                "Tu feedback nos ayuda a mejorar. (Responde con: sí/no/ajustar)"
            ),
        }
    except Exception as e:
        logging.error("Error generando oferta: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_carbon_offer(carbon_tonnes: float) -> Dict[str, Any]:
    current_price = OFFER_KNOWLEDGE["carbon_credits"]["current_price"]
    historical = OFFER_KNOWLEDGE["carbon_credits"]["historical_prices"]
    sma = sum(historical) / len(historical)
    if current_price > sma:
        trend = "up"
    elif current_price < sma:
        trend = "down"
    else:
        trend = "stable"
    suggested_price = current_price * 1.05 if trend == "up" else current_price * 0.98
    total_value = round(carbon_tonnes * suggested_price, 2)
    return {
        "tonnes": carbon_tonnes,
        "current_price": current_price,
        "suggested_price": round(suggested_price, 2),
        "total_value": total_value,
        "trend": trend,
        "confidence": 0.95,
    }


def _generate_wood_offer(parcel_data: Dict[str, Any]) -> Dict[str, Any]:
    offers: Dict[str, Any] = {}
    for species in parcel_data["tree_species"]:
        key = species.lower()
        if key in OFFER_KNOWLEDGE["wood_prices"]:
            price_data = OFFER_KNOWLEDGE["wood_prices"][key]
            current_price = price_data["current"]
            historical = price_data["historical"]
            sma = sum(historical) / len(historical)
            if current_price > sma:
                trend = "up"
            elif current_price < sma:
                trend = "down"
            else:
                trend = "stable"
            volume_per_ha = 10
            total_volume = volume_per_ha * (parcel_data["area"] / 10000)
            suggested_price = current_price * 1.03 if trend == "up" else current_price * 0.97
            total_value = round(total_volume * suggested_price, 2)
            offers[species] = {
                "volume_per_ha": volume_per_ha,
                "total_volume": round(total_volume, 2),
                "current_price": current_price,
                "suggested_price": round(suggested_price, 2),
                "total_value": total_value,
                "trend": trend,
            }
    return {
        "species_offers": offers,
        "total_wood_value": sum(offer["total_value"] for offer in offers.values()),
        "confidence": 0.9,
    }


def _optimize_subsidies(parcel_data: Dict[str, Any], area_ha: float) -> Dict[str, Any]:
    base_subsidy = OFFER_KNOWLEDGE["subsidies"]["pac_2040"]["base"]
    total_bonus = 0
    for cert in parcel_data["certifications"]:
        bonus_map = OFFER_KNOWLEDGE["subsidies"]["pac_2040"]["bonus"]
        total_bonus += bonus_map.get(cert.lower(), 0)
        if cert in ["PEFC", "FSC"] and "decreto_45_2020" in OFFER_KNOWLEDGE["subsidies"]:
            total_bonus += OFFER_KNOWLEDGE["subsidies"]["decreto_45_2020"]["bonus"]
    total_subsidy = (base_subsidy + total_bonus) * area_ha
    return {
        "base_subsidy": base_subsidy,
        "bonuses": {
            cert: OFFER_KNOWLEDGE["subsidies"]["pac_2040"]["bonus"].get(cert.lower(), 0)
            for cert in parcel_data["certifications"]
        },
        "total_per_ha": base_subsidy + total_bonus,
        "total_value": round(total_subsidy, 2),
        "area_ha": area_ha,
        "confidence": 1.0,
    }


def _calculate_confidence(carbon_offer: Dict[str, Any], wood_offer: Dict[str, Any]) -> float:
    carbon_conf = carbon_offer.get("confidence", 0.95)
    wood_conf = wood_offer.get("confidence", 0.9)
    return round((carbon_conf + wood_conf) / 2, 2)


@app.post("/update-knowledge")
async def update_knowledge(feedback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if feedback.get("user_response") == "ajustar":
            changes = feedback.get("suggested_changes", {})
            if "carbon_credits" in changes:
                new_price = changes["carbon_credits"]["suggested_price"]
                OFFER_KNOWLEDGE["carbon_credits"]["current_price"] = new_price
                hp = OFFER_KNOWLEDGE["carbon_credits"]["historical_prices"]
                hp.append(new_price)
                if len(hp) > 5:
                    hp.pop(0)
            if "wood_prices" in changes:
                for species, data in changes["wood_prices"].items():
                    if species in OFFER_KNOWLEDGE["wood_prices"]:
                        new_price = data["suggested_price"]
                        OFFER_KNOWLEDGE["wood_prices"][species]["current_price"] = new_price
                        hist = OFFER_KNOWLEDGE["wood_prices"][species]["historical"]
                        hist.append(new_price)
                        if len(hist) > 5:
                            hist.pop(0)
        feedback["timestamp"] = datetime.now().isoformat()
        log_path = os.getenv("OFFER_FEEDBACK_LOG", "feedback_log.json")
        with open(log_path, "a", encoding="utf-8") as f:
            json.dump(feedback, f)
            f.write("\n")
        return {
            "status": "success",
            "message": "Base de conocimiento actualizada con feedback.",
            "new_knowledge": OFFER_KNOWLEDGE,
        }
    except Exception as e:
        logging.error("Error actualizando conocimiento: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007, log_level="info")

