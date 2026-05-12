#!/usr/bin/env python3
"""
Aprueba un DynamicCropNFT (o ERC721) para el marketplace de OpenSea.
Tras la aprobación, listar manualmente en https://opensea.io/assets/<contract>/<token_id>
Uso: python3 scripts/list_on_opensea.py <token_id>
Variables: POLYGON_RPC o ETHEREUM_RPC, DYNAMIC_NFT_ADDRESS, PRIVATE_KEY, OPENSEA_PROXY (opcional)
"""
import os
import sys

# OpenSea Wyvern Proxy (Ethereum mainnet). Polygon: usar OPENSEA_PROXY si es distinta.
OPENSEA_WYVERN_ETH = "0x7be8076f4ea4a4ad08075c2508e481d6c946d12b"

ERC721_APPROVE_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def main():
    if len(sys.argv) < 2:
        print("Uso: list_on_opensea.py <token_id>", file=sys.stderr)
        sys.exit(1)
    token_id = int(sys.argv[1])

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("POLYGON_RPC") or os.getenv("ETHEREUM_RPC") or os.getenv("GAIA_CHAIN_RPC", "https://polygon-rpc.com")
    contract_address = os.getenv("DYNAMIC_NFT_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")
    opensea_proxy = os.getenv("OPENSEA_PROXY", OPENSEA_WYVERN_ETH)

    if not contract_address or not private_key:
        print("Definir DYNAMIC_NFT_ADDRESS y PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    contract_address = Web3.to_checksum_address(contract_address)
    opensea_proxy = Web3.to_checksum_address(opensea_proxy)
    nft = w3.eth.contract(address=contract_address, abi=ERC721_APPROVE_ABI)

    tx = nft.functions.approve(opensea_proxy, token_id).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 100000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    tx_hex = tx_hash.hex()
    print(tx_hex)
    base = "https://opensea.io/assets"
    if "polygon" in rpc.lower():
        base = "https://opensea.io/assets/matic"
    print(f"NFT {token_id} aprobado para OpenSea. Listar en: {base}/{contract_address}/{token_id}")
    return tx_hex


if __name__ == "__main__":
    main()
