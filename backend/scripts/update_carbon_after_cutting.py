#!/usr/bin/env python3
"""
Actualiza el CO₂ secuestrado de un ForestOwnershipToken tras una tala legal.
Opcional: emisión de CarbonCredit por madera vendida (lógica externa).
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
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("JUNTA_PRIVATE_KEY")

ABI_GET = [
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "getProperty",
        "outputs": [
            {"name": "parcelaId", "type": "string"},
            {"name": "owner", "type": "address"},
            {"name": "coordinates", "type": "string"},
            {"name": "area", "type": "uint256"},
            {"name": "treeSpecies", "type": "string"},
            {"name": "carbonSequestered", "type": "uint256"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "isProtected", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]
ABI_UPDATE = [
    {
        "inputs": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "newCarbonValue", "type": "uint256"},
        ],
        "name": "updateCarbonSequestered",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def update_carbon_after_cutting(property_token_id: int, volume_m3: int) -> str:
    """
    Reduce el CO₂ secuestrado tras una tala (ej: 1 m³ madera ≈ 1000 kg CO₂).
    Solo el propietario del token puede llamar.
    """
    if not PRIVATE_KEY or not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        raise ValueError("FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY son obligatorios")
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    account = w3.eth.account.from_key(PRIVATE_KEY.replace("0x", "").strip())
    contract_get = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI_GET,
    )
    contract_update = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI_UPDATE,
    )
    prop = contract_get.functions.getProperty(property_token_id).call()
    current_carbon = int(prop[5])
    carbon_reduction_kg = volume_m3 * 1000
    new_carbon = current_carbon - carbon_reduction_kg
    if new_carbon < 0:
        new_carbon = 0
    tx = contract_update.functions.updateCarbonSequestered(
        property_token_id,
        new_carbon,
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash_bytes.hex()


def main():
    parser = argparse.ArgumentParser(
        description="Actualizar CO₂ secuestrado tras tala (ForestOwnershipToken)"
    )
    parser.add_argument("property_token_id", type=int, help="ID del token de propiedad")
    parser.add_argument("volume_m3", type=int, help="Volumen talado en m³ (reducción: volume_m3 * 1000 kg CO₂)")
    args = parser.parse_args()

    try:
        tx_hash = update_carbon_after_cutting(args.property_token_id, args.volume_m3)
        print(tx_hash)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
