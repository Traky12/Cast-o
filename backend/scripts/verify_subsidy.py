#!/usr/bin/env python3
"""
Verificación de subvenciones en GaiaChain (Decreto 45/2020 — Junta de Extremadura).
Comprueba que un token de subvención corresponde al beneficiario y al importe esperado.
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
SUBSIDY_TOKEN_ADDRESS = os.getenv("SUBSIDY_TOKEN_ADDRESS", "")

# ABI mínimo: getSubsidy(tokenId) -> (beneficiary, amount, ...)
SUBSIDY_ABI = [
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "getSubsidy",
        "outputs": [
            {"name": "beneficiary", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


def verify_subsidy(token_id: int, beneficiary_address: str, expected_amount: int) -> bool:
    if not SUBSIDY_TOKEN_ADDRESS:
        raise ValueError("SUBSIDY_TOKEN_ADDRESS es obligatorio")
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(SUBSIDY_TOKEN_ADDRESS),
        abi=SUBSIDY_ABI,
    )
    result = contract.functions.getSubsidy(token_id).call()
    beneficiary = result[0] if isinstance(result, (list, tuple)) else result.get("beneficiary")
    amount = result[1] if isinstance(result, (list, tuple)) else result.get("amount")
    return (
        beneficiary and str(beneficiary).lower() == beneficiary_address.lower()
        and amount is not None
        and int(amount) == expected_amount
    )


def main():
    parser = argparse.ArgumentParser(description="Verificar subvención en GaiaChain (Decreto 45/2020)")
    parser.add_argument("token_id", type=int, help="ID del token de subvención")
    parser.add_argument("beneficiary", help="Dirección del beneficiario (0x...)")
    parser.add_argument("amount", type=int, help="Importe esperado en euros (ej: 5000)")
    args = parser.parse_args()

    if not SUBSIDY_TOKEN_ADDRESS:
        print("Configurar SUBSIDY_TOKEN_ADDRESS", file=sys.stderr)
        return 1
    try:
        valid = verify_subsidy(args.token_id, args.beneficiary, args.amount)
        print("Subvención válida: ✅ Sí" if valid else "Subvención válida: ❌ No")
        return 0 if valid else 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
