#!/usr/bin/env python3
"""
Verificación de batches de residuos en GaiaChain (Decreto 123/2023 — Economía Circular).
Comprueba que un batch tiene el kg de compost esperado.
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    from web3 import Web3
except ImportError:
    print("Instalar: pip install web3", file=sys.stderr)
    sys.exit(1)

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
CIRCULAR_ECONOMY_TOKEN_ADDRESS = os.getenv("CIRCULAR_ECONOMY_TOKEN_ADDRESS", "")

CIRCULAR_ECONOMY_ABI = [
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "getBatch",
        "outputs": [
            {"name": "farmId", "type": "string"},
            {"name": "residueKg", "type": "uint256"},
            {"name": "compostKg", "type": "uint256"},
            {"name": "co2Saved", "type": "uint256"},
            {"name": "ipfsHash", "type": "string"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


def verify_residue_batch(token_id: int, expected_compost_kg: int) -> bool:
    if not CIRCULAR_ECONOMY_TOKEN_ADDRESS:
        raise ValueError("CIRCULAR_ECONOMY_TOKEN_ADDRESS es obligatorio")
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CIRCULAR_ECONOMY_TOKEN_ADDRESS),
        abi=CIRCULAR_ECONOMY_ABI,
    )
    batch = contract.functions.getBatch(token_id).call()
    compost_kg = batch[2] if isinstance(batch, (list, tuple)) else batch.get("compostKg")
    return compost_kg is not None and int(compost_kg) == expected_compost_kg


def main():
    parser = argparse.ArgumentParser(
        description="Verificar batch de residuos en GaiaChain (Decreto 123/2023)"
    )
    parser.add_argument("token_id", type=int, help="ID del token CircularEconomyToken")
    parser.add_argument(
        "expected_compost_kg",
        type=int,
        help="Kg de compost esperados (ej: 1000)",
    )
    args = parser.parse_args()

    if not CIRCULAR_ECONOMY_TOKEN_ADDRESS:
        print("Configurar CIRCULAR_ECONOMY_TOKEN_ADDRESS", file=sys.stderr)
        return 1
    try:
        valid = verify_residue_batch(args.token_id, args.expected_compost_kg)
        print("Batch de residuos válido: ✅ Sí" if valid else "Batch de residuos válido: ❌ No")
        return 0 if valid else 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
