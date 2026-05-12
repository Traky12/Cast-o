#!/usr/bin/env python3
"""
Mint DynamicCropNFT por cooperativa (3 coops: lechuga, vid, tomate).
Uso: python3 scripts/mint_dynamic_nft.py --coop 1 [--cultivo lechuga]
     python3 scripts/mint_dynamic_nft.py --coop 2 --cultivo vid
Variables: GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS, PRIVATE_KEY
"""
from __future__ import annotations

import argparse
import os
import sys

COOP_CULTIVO = {1: "lechuga", 2: "vid", 3: "tomate"}

DYNAMIC_NFT_MINT_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "cropType", "type": "string"},
            {"name": "farmId", "type": "string"},
            {"name": "initialIpfsHash", "type": "string"},
            {"name": "strain", "type": "string"},
            {"name": "thcCbdRatio", "type": "uint256"},
            {"name": "brixLevel", "type": "uint256"},
        ],
        "name": "mintNFT",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coop", type=int, choices=[1, 2, 3], required=True, help="Cooperativa 1, 2 o 3")
    parser.add_argument("--cultivo", type=str, default=None, help="Cultivo (default: lechuga/vid/tomate por coop)")
    args = parser.parse_args()
    cultivo = (args.cultivo or COOP_CULTIVO.get(args.coop, "lechuga")).lower()
    farm_id = f"coop{args.coop}"
    ipfs_hash = os.getenv("MINT_IPFS_PLACEHOLDER", "QmPlaceholderDynamicNFT")

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("DYNAMIC_NFT_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")
    if not contract_address or not private_key:
        print("Definir GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS y PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    to_address = account.address
    contract_address = Web3.to_checksum_address(contract_address)
    to_address = Web3.to_checksum_address(to_address)
    contract = w3.eth.contract(address=contract_address, abi=DYNAMIC_NFT_MINT_ABI)

    tx = contract.functions.mintNFT(
        to_address,
        cultivo,
        farm_id,
        ipfs_hash,
        "",
        0,
        0,
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 500000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())


if __name__ == "__main__":
    main()
