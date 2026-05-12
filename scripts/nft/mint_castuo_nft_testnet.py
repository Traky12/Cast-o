#!/usr/bin/env python3
"""
Minta NFT CASTUO_GOLD_V1 en testnet. Requiere contract_address.txt, TESTNET_RPC_URL, TESTNET_PRIVATE_KEY.
Opcional: ZIP_PATH (ZIP de prueba), IPFS_CID (metadatos en IPFS).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    try:
        from web3 import Web3
    except ImportError:
        print("pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.environ.get("TESTNET_RPC_URL", "").strip()
    key = os.environ.get("TESTNET_PRIVATE_KEY", "").strip()
    if not rpc or not key:
        print("TESTNET_RPC_URL y TESTNET_PRIVATE_KEY requeridos", file=sys.stderr)
        sys.exit(2)

    addr_file = ROOT / "contract_address.txt"
    if not addr_file.is_file():
        print("Ejecuta antes deploy_castuo_nft_testnet.py", file=sys.stderr)
        sys.exit(3)

    contract_address = addr_file.read_text(encoding="utf-8").strip()
    zip_path = Path(os.environ.get("ZIP_PATH", str(ROOT / "CASTUO_GOLD_V1_TEST.zip")))
    ipfs_cid = os.environ.get("IPFS_CID", "QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco")

    if zip_path.is_file():
        zip_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    else:
        zip_hash = "0" * 64

    abi_path = ROOT / "contracts" / "nft" / "CASTUO_NFT_ABI.json"
    if not abi_path.is_file():
        print("Genera CASTUO_NFT_ABI.json con solc", file=sys.stderr)
        sys.exit(4)
    with open(abi_path, encoding="utf-8") as f:
        abi = json.load(f)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(key)
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=abi)
    token_uri = f"ipfs://{ipfs_cid}"

    tx = contract.functions.mint(account.address, token_uri).build_transaction({
        "from": account.address,
        "gas": 500_000,
        "gasPrice": w3.to_wei(10, "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"NFT mintado en testnet. TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    token_id = 1
    try:
        contract.functions.registerCompliance(
            token_id,
            "EU_AI_ACT_2024",
            "0x" + zip_hash[:62],
        ).build_transaction({
            "from": account.address,
            "gas": 300_000,
            "gasPrice": w3.to_wei(10, "gwei"),
            "nonce": w3.eth.get_transaction_count(account.address),
        })
        # opcional: enviar registerCompliance
    except Exception as e:
        print("registerCompliance (opcional):", e)


if __name__ == "__main__":
    main()
