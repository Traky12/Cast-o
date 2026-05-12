#!/usr/bin/env python3
"""
Despliega CASTUO_NFT en testnet. Requiere TESTNET_RPC_URL y TESTNET_PRIVATE_KEY en .env.
No usar claves de mainnet. Guarda contract_address en contract_address.txt.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_env() -> tuple[str, str]:
    rpc = os.environ.get("TESTNET_RPC_URL", "").strip()
    key = os.environ.get("TESTNET_PRIVATE_KEY", "").strip()
    if not rpc or not key:
        print("Configura TESTNET_RPC_URL y TESTNET_PRIVATE_KEY (ej. en .env)", file=sys.stderr)
        sys.exit(2)
    return rpc, key


def main() -> None:
    try:
        from web3 import Web3
    except ImportError:
        print("Instala web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc, private_key = load_env()
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        print("No conectado a testnet", file=sys.stderr)
        sys.exit(3)

    abi_path = ROOT / "contracts" / "nft" / "CASTUO_NFT_ABI.json"
    bin_path = ROOT / "contracts" / "nft" / "CASTUO_NFT_BIN.json"
    if not abi_path.is_file() or not bin_path.is_file():
        print("Faltan ABI/BIN. Ejecuta scripts/nft/compile_castuo_nft.py o genera con solc.", file=sys.stderr)
        sys.exit(4)

    with open(abi_path, encoding="utf-8") as f:
        abi = json.load(f)
    with open(bin_path, encoding="utf-8") as f:
        data = json.load(f)
    bytecode = data.get("bytecode") or (data.get("data") or {}).get("bytecode")
    if isinstance(bytecode, dict):
        bytecode = bytecode.get("object", "")
    if not bytecode:
        print("CASTUO_NFT_BIN.json debe contener 'bytecode' (string hex)", file=sys.stderr)
        sys.exit(4)

    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = contract.constructor().build_transaction({
        "from": account.address,
        "gas": 2_000_000,
        "gasPrice": w3.to_wei(10, "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Desplegando... TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = receipt.get("contractAddress")
    if not address:
        print("Fallo en deployment", file=sys.stderr)
        sys.exit(5)
    out = ROOT / "contract_address.txt"
    out.write_text(address, encoding="utf-8")
    print(f"Contrato desplegado: {address}")


if __name__ == "__main__":
    main()
