#!/usr/bin/env python3
"""
Mintea un DynamicCropNFT para fresas en GaiaChain.
Uso: python3 scripts/mint_strawberry_nft.py <to_address> <farm_id> <brix_level> <ipfs_hash>
Ejemplo: python3 scripts/mint_strawberry_nft.py 0xAgricultor extremadura-farm-001 12 QmXoypiz...
  (brix 10-15 para fresas dulces)
Variables: GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS, PRIVATE_KEY
"""
import os
import sys

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
    if len(sys.argv) != 5:
        print(
            "Uso: mint_strawberry_nft.py <to_address> <farm_id> <brix_level> <ipfs_hash>",
            file=sys.stderr,
        )
        sys.exit(1)
    to_address = sys.argv[1]
    farm_id = sys.argv[2]
    brix_level = int(sys.argv[3])
    ipfs_hash = sys.argv[4]

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
    contract_address = Web3.to_checksum_address(contract_address)
    to_address = Web3.to_checksum_address(to_address)
    contract = w3.eth.contract(address=contract_address, abi=DYNAMIC_NFT_MINT_ABI)

    tx = contract.functions.mintNFT(
        to_address,
        "strawberry",
        farm_id,
        ipfs_hash,
        "",   # strain no aplica
        0,    # thcCbdRatio no aplica
        brix_level,
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
    return tx_hex


if __name__ == "__main__":
    main()
