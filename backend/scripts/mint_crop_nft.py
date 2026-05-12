#!/usr/bin/env python3
"""
Mintea un CropNFT en GaiaChain (metadatos en IPFS).
Uso: python3 scripts/mint_crop_nft.py <to_address> <crop_type> <farm_id> <location> <co2_saved> <ipfs_hash>
Ejemplo: python3 scripts/mint_crop_nft.py 0xAgricultor lettuce extremadura-farm-001 "39.4769°N, 6.3706°W" 12 QmXoypiz...
Variables: GAIA_CHAIN_RPC, CROP_NFT_ADDRESS, PRIVATE_KEY
"""
import os
import sys

CROP_NFT_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "cropType", "type": "string"},
            {"name": "farmId", "type": "string"},
            {"name": "location", "type": "string"},
            {"name": "co2Saved", "type": "uint256"},
            {"name": "ipfsHash", "type": "string"},
        ],
        "name": "mintNFT",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def main():
    if len(sys.argv) != 7:
        print(
            "Uso: mint_crop_nft.py <to_address> <crop_type> <farm_id> <location> <co2_saved> <ipfs_hash>",
            file=sys.stderr,
        )
        sys.exit(1)
    to_address = sys.argv[1]
    crop_type = sys.argv[2]
    farm_id = sys.argv[3]
    location = sys.argv[4]
    co2_saved = int(sys.argv[5])
    ipfs_hash = sys.argv[6]

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("CROP_NFT_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")

    if not contract_address or not private_key:
        print(
            "Definir GAIA_CHAIN_RPC, CROP_NFT_ADDRESS y PRIVATE_KEY",
            file=sys.stderr,
        )
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    contract_address = Web3.to_checksum_address(contract_address)
    to_address = Web3.to_checksum_address(to_address)
    contract = w3.eth.contract(address=contract_address, abi=CROP_NFT_ABI)

    tx = contract.functions.mintNFT(
        to_address, crop_type, farm_id, location, co2_saved, ipfs_hash
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 500000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx_hex = tx_hash.hex()
    print(tx_hex)
    explorer = os.getenv("GAIA_EXPLORER_URL", "https://explorer.gaiachain.castuo-system.com")
    print(f"NFT minteado: {explorer}/tx/{tx_hex}")
    return tx_hex


if __name__ == "__main__":
    main()
