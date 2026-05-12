from datetime import datetime
import json
import logging
from typing import Any, Dict, List

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()
logging.basicConfig(level=logging.INFO)


Q_TABLE: Dict[str, Dict[str, Dict[str, float]]] = {}
DEFAULT_Q_VALUE = 0.5
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
EXPLORATION_RATE = 0.2


class NegotiationRequest(BaseModel):
    token_id: int
    wood_offer: Dict[str, Any]
    buyer_profile: str


class NegotiationResponse(BaseModel):
    optimized_offer: Dict[str, Any]
    negotiation_steps: List[Dict[str, Any]]
    final_price: float
    accepted: bool
    confidence: float


def _init_q_table(offer: Dict[str, Any]) -> None:
    state_key = json.dumps(offer, sort_keys=True)
    if state_key in Q_TABLE:
        return
    species = list(offer["species_offers"].keys())
    actions = ["increase_5%", "increase_2%", "keep", "decrease_2%", "decrease_5%"]
    Q_TABLE[state_key] = {}
    for sp in species:
        Q_TABLE[state_key][sp] = {act: DEFAULT_Q_VALUE for act in actions}


def _state_key(offer: Dict[str, Any]) -> str:
    return json.dumps(offer, sort_keys=True)


def _choose_action(offer: Dict[str, Any], buyer_profile: str) -> str:
    global EXPLORATION_RATE
    state = _state_key(offer)
    if np.random.random() < EXPLORATION_RATE:
        actions = list(
            Q_TABLE[state][list(offer["species_offers"].keys())[0]].keys()
        )
        return np.random.choice(actions)
    species = np.random.choice(list(offer["species_offers"].keys()))
    q_values = Q_TABLE[state][species]
    return max(q_values, key=q_values.get)


def _apply_action(offer: Dict[str, Any], action: str) -> Dict[str, Any]:
    new_offer = json.loads(json.dumps(offer))
    for species, data in new_offer["species_offers"].items():
        current_price = data["suggested_price"]
        if action == "increase_5%":
            data["suggested_price"] = round(current_price * 1.05, 2)
        elif action == "increase_2%":
            data["suggested_price"] = round(current_price * 1.02, 2)
        elif action == "decrease_2%":
            data["suggested_price"] = round(current_price * 0.98, 2)
        elif action == "decrease_5%":
            data["suggested_price"] = round(current_price * 0.95, 2)
        data["total_value"] = round(
            data["total_volume"] * data["suggested_price"],
            2,
        )
    new_offer["total_wood_value"] = sum(
        s["total_value"] for s in new_offer["species_offers"].values()
    )
    return new_offer


def _calculate_reward(
    new_offer: Dict[str, Any], buyer_profile: str, is_final: bool
) -> float:
    base_reward = {
        "conservador": 0.3,
        "equilibrado": 0.5,
        "agresivo": 0.7,
    }.get(buyer_profile, 0.5)
    current_cost = sum(
        s["current_price"] * s["total_volume"]
        for s in new_offer["species_offers"].values()
    )
    margin = (
        new_offer["total_wood_value"] - current_cost
    ) / max(new_offer["total_wood_value"], 1e-6)
    if is_final:
        return base_reward + (0.3 if margin > 0 else -0.2)
    return base_reward + margin


def _update_q_table(
    state: str, action: str, reward: float, new_state: Dict[str, Any]
) -> None:
    next_state = _state_key(new_state)
    species = list(new_state["species_offers"].keys())[0]
    old_q = Q_TABLE[state][species][action]
    max_future_q = (
        max(Q_TABLE[next_state][species].values())
        if next_state in Q_TABLE
        else 0.0
    )
    new_q = old_q + LEARNING_RATE * (reward + DISCOUNT_FACTOR * max_future_q - old_q)
    Q_TABLE[state][species][action] = new_q


@app.post("/negotiate", response_model=NegotiationResponse)
async def negotiate(request: NegotiationRequest) -> Dict[str, Any]:
    try:
        _init_q_table(request.wood_offer)
        initial_state = _state_key(request.wood_offer)
        current_offer = json.loads(json.dumps(request.wood_offer))
        steps: List[Dict[str, Any]] = []
        accepted = False
        for round_idx in range(3):
            action = _choose_action(current_offer, request.buyer_profile)
            new_offer = _apply_action(current_offer, action)
            reward = _calculate_reward(
                new_offer, request.buyer_profile, is_final=(round_idx == 2)
            )
            steps.append(
                {
                    "round": round_idx + 1,
                    "action": action,
                    "previous_offer": current_offer["species_offers"],
                    "new_offer": new_offer["species_offers"],
                    "reward": reward,
                }
            )
            _update_q_table(initial_state, action, reward, new_offer)
            current_offer = new_offer
            if reward > 0.8:
                accepted = True
        confidence = 0.95 if accepted else 0.7
        final_price = sum(
            s["total_value"] for s in current_offer["species_offers"].values()
        )
        return {
            "optimized_offer": current_offer,
            "negotiation_steps": steps,
            "final_price": final_price,
            "accepted": accepted,
            "confidence": confidence,
        }
    except Exception as e:
        logging.error("Error en negociación: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-negotiation-knowledge")
async def update_negotiation_knowledge(feedback: Dict[str, Any]) -> Dict[str, Any]:
    global EXPLORATION_RATE
    try:
        feedback["timestamp"] = datetime.now().isoformat()
        log_path = "negotiation_feedback.json"
        with open(log_path, "a", encoding="utf-8") as f:
            json.dump(feedback, f)
            f.write("\n")
        if feedback.get("accepted"):
            EXPLORATION_RATE = max(0.05, EXPLORATION_RATE * 0.99)
        else:
            EXPLORATION_RATE = min(0.3, EXPLORATION_RATE * 1.05)
        return {
            "status": "success",
            "message": "Modelo de negociación actualizado.",
            "new_exploration_rate": EXPLORATION_RATE,
        }
    except Exception as e:
        logging.error("Error actualizando modelo de negociación: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008, log_level="info")

