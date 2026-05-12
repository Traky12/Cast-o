#!/usr/bin/env python3
"""
Mint de tokens de propiedad forestal en GaiaChain (ForestOwnershipToken).
Ley 3/2023 de Montes, Decreto 45/2020, Orden 15/03/2021 — Junta de Extremadura.
"""
from __future__ import annotations

import argparse
import json
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

ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "parcelaId", "type": "string"},
            {"name": "coordinates", "type": "string"},
            {"name": "area", "type": "uint256"},
            {"name": "treeSpecies", "type": "string"},
            {"name": "carbonSequestered", "type": "uint256"},
            {"name": "isProtected", "type": "bool"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "certifications", "type": "string[]"},
        ],
        "name": "mintProperty",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def mint_forest_property(
    to_address: str,
    parcela_id: str,
    coordinates: str,
    area_m2: int,
    tree_species: str,
    carbon_sequestered: int,
    is_protected: bool,
    ipfs_hash: str,
    certifications: list[str] | None = None,
) -> str:
    if not PRIVATE_KEY or not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        raise ValueError("FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY son obligatorios")
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    account = w3.eth.account.from_key(PRIVATE_KEY.replace("0x", "").strip())
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI,
    )
    certs = certifications if certifications is not None else []
    tx = contract.functions.mintProperty(
        Web3.to_checksum_address(to_address),
        parcela_id,
        coordinates,
        area_m2,
        tree_species,
        carbon_sequestered,
        is_protected,
        ipfs_hash,
        certs,
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 600000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash_bytes.hex()


def main():
    parser = argparse.ArgumentParser(description="Mint de propiedad forestal (ForestOwnershipToken)")
    parser.add_argument("to_address", help="Dirección del propietario (0x...)")
    parser.add_argument("parcela_id", help="ID catastral (ej: XT-12345-001)")
    parser.add_argument("coordinates", help="Coordenadas GPS (ej: 39.4769°N, 6.3706°W)")
    parser.add_argument("area_m2", type=int, help="Área en m² (ej: 10000)")
    parser.add_argument("tree_species", help="Especies separadas por coma (ej: Quercus ilex,Pinus pinea)")
    parser.add_argument("carbon_sequestered", type=int, help="kg CO₂ secuestrados/año (ej: 5000)")
    parser.add_argument(
        "is_protected",
        nargs="?",
        default="false",
        help="¿Área protegida? (true/false/1/0)",
    )
    parser.add_argument("ipfs_hash", help="Hash IPFS de metadatos")
    parser.add_argument(
        "--certifications",
        "-c",
        nargs="*",
        default=[],
        help="Certificaciones (ej: PEFC FSC 'Red Natura 2000')",
    )
    args = parser.parse_args()

    is_protected = str(args.is_protected).lower() in ("1", "true", "yes")
    try:
        tx_hash = mint_forest_property(
            args.to_address,
            args.parcela_id,
            args.coordinates,
            args.area_m2,
            args.tree_species,
            args.carbon_sequestered,
            is_protected,
            args.ipfs_hash,
            args.certifications,
        )
        print(tx_hash)
        print(f"Explorer: https://explorer.gaiachain.castuo-system.com/tx/{tx_hash}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
