#!/usr/bin/env python3
"""
Recuperación desde NFT: lee tokenURI (IPFS), valida hash ZIP y muestra compliance.
Uso: TESTNET_RPC_URL, contract_address.txt, token_id=1. Opcional: ZIP local para comparar hash.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fetch_ipfs(cid: str) -> dict:
    try:
        import requests
        r = requests.get(f"https://ipfs.io/ipfs/{cid}", timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"IPFS fetch error: {e}", file=sys.stderr)
        return {}


def main() -> None:
    try:
        from web3 import Web3
    except ImportError:
        print("pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.environ.get("TESTNET_RPC_URL", "").strip()
    if not rpc:
        print("TESTNET_RPC_URL requerido", file=sys.stderr)
        sys.exit(2)

    addr_file = ROOT / "contract_address.txt"
    if not addr_file.is_file():
        print("Falta contract_address.txt (ejecuta deploy antes)", file=sys.stderr)
        sys.exit(3)

    contract_address = addr_file.read_text(encoding="utf-8").strip()
    token_id = int(os.environ.get("TOKEN_ID", "1"))
    zip_path = os.environ.get("ZIP_PATH", str(ROOT / "CASTUO_GOLD_V1_TEST.zip"))

    abi_path = ROOT / "contracts" / "nft" / "CASTUO_NFT_ABI.json"
    if not abi_path.is_file():
        print("Genera CASTUO_NFT_ABI.json", file=sys.stderr)
        sys.exit(4)
    with open(abi_path, encoding="utf-8") as f:
        abi = json.load(f)

    w3 = Web3(Web3.HTTPProvider(rpc))
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=abi)
    uri = contract.functions.tokenURI(token_id).call()
    if not uri or not uri.startswith("ipfs://"):
        print("tokenURI no disponible o no IPFS", file=sys.stderr)
        sys.exit(5)
    cid = uri.replace("ipfs://", "").strip()
    metadata = fetch_ipfs(cid)
    if not metadata:
        sys.exit(6)

    expected_hash = None
    for att in metadata.get("attributes", []):
        if att.get("trait_type") == "Zip Hash":
            expected_hash = att.get("value")
            break
    if expected_hash and Path(zip_path).is_file():
        actual = hashlib.sha256(Path(zip_path).read_bytes()).hexdigest()
        if actual == expected_hash:
            print("Recuperación exitosa: el hash del ZIP coincide.")
        else:
            print("Error: hashes no coinciden (posible corrupción).", file=sys.stderr)
    else:
        print("ZIP Hash en metadatos:", expected_hash or "(no encontrado)")

    try:
        standards, hashes_arr, timestamps = contract.functions.getComplianceData(token_id).call()
        print("Datos de cumplimiento:")
        for i, (s, h, t) in enumerate(zip(standards, hashes_arr, timestamps)):
            print(f"  - {s}: {h[:20]}... (ts: {t})")
    except Exception as e:
        print("getComplianceData:", e)


if __name__ == "__main__":
    main()
