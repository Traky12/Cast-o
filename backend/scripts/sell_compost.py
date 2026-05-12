#!/usr/bin/env python3
"""
Vende compost tokenizado en Biofertilizantes.org (API externa).
Certificación apunta a GaiaChain para trazabilidad.
Uso: python3 scripts/sell_compost.py <token_id> <amount_kg> [price_per_kg]
Ejemplo: python3 scripts/sell_compost.py compost-extremadura-batch-1 100 0.8
Variables: BIOFERTILIZANTES_API_URL, BIOFERTILIZANTES_API_KEY
           GAIA_EXPLORER_URL (opcional, para certification URL)
"""
import os
import sys


def sell_compost(token_id: str, amount_kg: float, price_per_kg: float = 0.8) -> dict:
    url = os.getenv(
        "BIOFERTILIZANTES_API_URL", "https://api.biofertilizantes.org/v1/sell"
    )
    api_key = os.getenv("BIOFERTILIZANTES_API_KEY", "")
    explorer = os.getenv(
        "GAIA_EXPLORER_URL", "https://explorer.gaiachain.castuo-system.com"
    )
    if not api_key:
        print(
            "Definir BIOFERTILIZANTES_API_KEY (y opcional BIOFERTILIZANTES_API_URL)",
            file=sys.stderr,
        )
        return {}
    certification = f"{explorer}/tx/{token_id}" if token_id else ""
    payload = {
        "token_id": token_id,
        "amount_kg": amount_kg,
        "price_per_kg": price_per_kg,
        "certification": certification,
    }
    try:
        import requests
    except ImportError:
        print("Instalar requests: pip install requests", file=sys.stderr)
        return {}
    resp = requests.post(
        url,
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) < 3:
        print(
            "Uso: sell_compost.py <token_id> <amount_kg> [price_per_kg]",
            file=sys.stderr,
        )
        sys.exit(1)
    token_id = sys.argv[1]
    amount_kg = float(sys.argv[2])
    price_per_kg = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    result = sell_compost(token_id, amount_kg, price_per_kg)
    if result:
        print(result)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
