#!/usr/bin/env python3
"""
Devuelve el propietario de un CropNFT por tokenId.
Uso: python3 scripts/get_nft_owner.py <token_id>
Variables: GAIA_CHAIN_RPC, CROP_NFT_ADDRESS
"""
import os
import sys

ERC721_OWNER_ABI = [
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    }
]


def main():
    if len(sys.argv) != 2:
        print("Uso: get_nft_owner.py <token_id>", file=sys.stderr)
        sys.exit(1)
    token_id = int(sys.argv[1])

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("CROP_NFT_ADDRESS", "")
    if not contract_address:
        print("Definir GAIA_CHAIN_RPC y CROP_NFT_ADDRESS", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    contract_address = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=contract_address, abi=ERC721_OWNER_ABI)
    owner = contract.functions.ownerOf(token_id).call()
    print(owner)
    return owner


if __name__ == "__main__":
    main()
