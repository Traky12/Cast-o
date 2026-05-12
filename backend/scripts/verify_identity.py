#!/usr/bin/env python3
"""
Validación de identidad para ejercicio del derecho al olvido (GDPR Art. 17).
Comprueba que la dirección proporcionada es propietaria del token en GaiaChain.
En producción: integrar con API Junta para DNI y envío OTP.
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
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "ownerOf", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
]


def verify_owner(token_id: int, requester_address: str) -> bool:
    """Comprueba que requester_address es el propietario del token en GaiaChain."""
    if not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        return False
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI,
    )
    owner = contract.functions.ownerOf(token_id).call()
    return owner and str(owner).lower() == requester_address.strip().lower()


def main():
    parser = argparse.ArgumentParser(description="Verificar que una dirección es propietaria del token")
    parser.add_argument("token_id", type=int, help="ForestOwnershipToken ID")
    parser.add_argument("address", help="Dirección del solicitante (0x...)")
    args = parser.parse_args()

    if not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        print("Configurar FOREST_OWNERSHIP_TOKEN_ADDRESS", file=sys.stderr)
        return 1
    ok = verify_owner(args.token_id, args.address)
    print("Propietario verificado: Sí" if ok else "Propietario verificado: No")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
