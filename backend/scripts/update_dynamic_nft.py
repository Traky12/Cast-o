#!/usr/bin/env python3
"""
Actualiza growth stage y metadatos IPFS de un DynamicCropNFT en GaiaChain.
Uso: python3 scripts/update_dynamic_nft.py <token_id> <growth_stage> [image_path]
Ejemplo: python3 scripts/update_dynamic_nft.py 1 50 images/lettuce_50percent.jpg
Variables: GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS, PRIVATE_KEY, IPFS_GATEWAY (opcional)
"""
import json
import os
import sys
from datetime import datetime

DYNAMIC_NFT_ABI = [
    {
        "inputs": [
            {"name": "tokenId", "type": "uint256"},
            {"name": "newGrowthStage", "type": "uint256"},
            {"name": "newIpfsHash", "type": "string"},
        ],
        "name": "updateGrowthStage",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def connect_ipfs():
    try:
        import ipfshttpclient
    except ImportError:
        return None
    api = os.getenv("IPFS_GATEWAY", "/dns/ipfs.infura.io/tcp/5001/https")
    try:
        return ipfshttpclient.connect(api)
    except Exception:
        return None


def upload_to_ipfs_str(client, data: str) -> str:
    if client is None:
        return "QmPlaceholderNoIPFS"
    return client.add_str(data)


def upload_file_to_ipfs(client, path: str) -> str:
    if client is None or not os.path.isfile(path):
        return "QmPlaceholderImage"
    with open(path, "rb") as f:
        data = f.read()
    result = client.add_bytes(data)
    if isinstance(result, list) and result:
        return result[0].get("Hash", result[0]) if isinstance(result[0], dict) else str(result[0])
    return str(result)


def update_growth_stage(token_id: int, growth_stage: int, image_path: str | None) -> str:
    client = connect_ipfs()
    image_hash = upload_file_to_ipfs(client, image_path) if image_path else "QmPlaceholderImage"
    image_uri = f"ipfs://{image_hash}"

    metadata = {
        "name": f"Growing Lettuce (Stage {growth_stage}%)",
        "description": f"A lettuce at {growth_stage}% growth stage.",
        "image": image_uri,
        "attributes": [
            {"trait_type": "Growth Stage", "value": growth_stage},
            {"trait_type": "Last Update", "value": datetime.utcnow().isoformat() + "Z"},
        ],
    }
    new_ipfs_hash = upload_to_ipfs_str(client, json.dumps(metadata, ensure_ascii=False))

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        return ""

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("DYNAMIC_NFT_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")
    if not contract_address or not private_key:
        print("Definir GAIA_CHAIN_RPC, DYNAMIC_NFT_ADDRESS y PRIVATE_KEY", file=sys.stderr)
        return ""

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    contract_address = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=contract_address, abi=DYNAMIC_NFT_ABI)

    tx = contract.functions.updateGrowthStage(
        token_id, growth_stage, new_ipfs_hash
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 300000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()


def main():
    if len(sys.argv) < 3:
        print(
            "Uso: update_dynamic_nft.py <token_id> <growth_stage> [image_path]",
            file=sys.stderr,
        )
        sys.exit(1)
    token_id = int(sys.argv[1])
    growth_stage = int(sys.argv[2])
    image_path = sys.argv[3] if len(sys.argv) > 3 else None
    if growth_stage < 0 or growth_stage > 100:
        print("growth_stage debe estar entre 0 y 100", file=sys.stderr)
        sys.exit(1)

    tx_hex = update_growth_stage(token_id, growth_stage, image_path)
    if tx_hex:
        print(tx_hex)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
