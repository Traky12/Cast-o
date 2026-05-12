#!/usr/bin/env python3
"""
Vender créditos de carbono en AirCarbon Exchange (API de ejemplo).
Uso: python3 scripts/sell_on_aircarbon.py <verra_project_id> <kg_co2> <price_per_kg_usd>
"""
import json
import os
import sys

import requests

AIRCARBON_API_URL = os.getenv("AIRCARBON_API_URL", "https://api.aircarbon.co/v1/credits/sell")


def sell_credits_on_aircarbon(verra_project_id: str, kg_co2: float, price_per_kg_usd: float) -> dict:
    api_key = os.getenv("AIRCARBON_API_KEY", "")
    if not api_key:
        return {"error": "Definir AIRCARBON_API_KEY"}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "project_id": verra_project_id,
        "amount_kg": kg_co2,
        "price_per_kg_usd": price_per_kg_usd,
        "currency": "USD",
    }
    response = requests.post(AIRCARBON_API_URL, headers=headers, data=json.dumps(payload), timeout=30)
    return response.json()


def main():
    if len(sys.argv) < 4:
        print("Uso: sell_on_aircarbon.py <verra_project_id> <kg_co2> <price_per_kg_usd>", file=sys.stderr)
        sys.exit(1)
    verra_project_id = sys.argv[1]
    kg_co2 = float(sys.argv[2])
    price_per_kg_usd = float(sys.argv[3])
    result = sell_credits_on_aircarbon(verra_project_id, kg_co2, price_per_kg_usd)
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
