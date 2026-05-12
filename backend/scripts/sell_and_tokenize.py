#!/usr/bin/env python3
"""
Vender créditos en AirCarbon y registrar/tokenizar en GaiaChain (opcional con BioCoin).
Uso: python3 scripts/sell_and_tokenize.py <verra_project_id> <kg_co2> <price_per_kg_usd>
"""
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def sell_and_tokenize(verra_project_id: str, kg_co2: float, price_per_kg_usd: float):
    sale_result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, "sell_on_aircarbon.py"), verra_project_id, str(kg_co2), str(price_per_kg_usd)],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(SCRIPT_DIR),
    )
    sale_out = sale_result.stdout or sale_result.stderr or "{}"
    try:
        sale_result = json.loads(sale_out)
    except json.JSONDecodeError:
        sale_result = {"raw": sale_out}

    tx_hash = None
    if os.getenv("BIOCOIN_CARBON_MARKET_ADDRESS"):
        run_buy = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "sell_carbon_credits_biocoin.py"), str(int(kg_co2))],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(SCRIPT_DIR),
        )
        if run_buy.stdout:
            tx_hash = run_buy.stdout.strip()
    return {"sale_result": sale_result, "tx_hash": tx_hash}


def main():
    if len(sys.argv) < 4:
        print("Uso: sell_and_tokenize.py <verra_project_id> <kg_co2> <price_per_kg_usd>", file=sys.stderr)
        sys.exit(1)
    verra_project_id = sys.argv[1]
    kg_co2 = float(sys.argv[2])
    price_per_kg_usd = float(sys.argv[3])
    out = sell_and_tokenize(verra_project_id, kg_co2, price_per_kg_usd)
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
