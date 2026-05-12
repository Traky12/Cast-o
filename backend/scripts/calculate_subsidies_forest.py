#!/usr/bin/env python3
"""
Calcula subvenciones elegibles para un ForestOwnershipToken (PAC 2040, Decreto 45/2020, Red Natura 2000).
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
FOREST_OWNERSHIP_TOKEN_ADDRESS = os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS", "")

ABI = [
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "calculateSubsidies", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getEligibleSubsidies", "outputs": [{"name": "", "type": "string[]"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getCertifications", "outputs": [{"name": "", "type": "string[]"}], "stateMutability": "view", "type": "function"},
]


def main():
    parser = argparse.ArgumentParser(description="Calcular subvenciones para ForestOwnershipToken")
    parser.add_argument("token_id", type=int, help="ID del token de propiedad")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar códigos elegibles y certificaciones")
    args = parser.parse_args()

    if not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        print("Configurar FOREST_OWNERSHIP_TOKEN_ADDRESS", file=sys.stderr)
        return 1
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI,
    )
    try:
        total = contract.functions.calculateSubsidies(args.token_id).call()
        print(f"Subvenciones totales para token {args.token_id}: €{total}/año")
        if args.verbose:
            codes = contract.functions.getEligibleSubsidies(args.token_id).call()
            certs = contract.functions.getCertifications(args.token_id).call()
            print("Códigos:", ", ".join(codes))
            print("Certificaciones:", ", ".join(certs))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
