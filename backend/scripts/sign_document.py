#!/usr/bin/env python3
"""
Firma de documentos en GaiaChain: hash SHA-512 + mint de token (GreenLicenseToken).
Uso: JUNTA_PRIVATE_KEY y DOCUMENT_TOKEN_ADDRESS (GreenLicenseToken).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

try:
    from web3 import Web3
except ImportError:
    print("Instalar: pip install web3", file=sys.stderr)
    sys.exit(1)

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
PRIVATE_KEY = os.getenv("JUNTA_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
DOCUMENT_TOKEN_ADDRESS = os.getenv("DOCUMENT_TOKEN_ADDRESS", "")

GREEN_LICENSE_ABI = [
    {
        "inputs": [
            {"name": "documentHash", "type": "string"},
            {"name": "documentType", "type": "string"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "responsible", "type": "string"},
        ],
        "name": "mintDocument",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "getDocumentMetadata",
        "outputs": [
            {"name": "documentHash", "type": "string"},
            {"name": "documentType", "type": "string"},
            {"name": "ipfsHash", "type": "string"},
            {"name": "timestamp", "type": "uint256"},
            {"name": "responsible", "type": "string"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


def sha512_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha512(f.read()).hexdigest()


def sign_document(
    document_hash: str,
    document_type: str,
    metadata_ipfs_hash: str,
    responsible: str = "Junta de Extremadura",
) -> str:
    if not PRIVATE_KEY or not DOCUMENT_TOKEN_ADDRESS:
        raise ValueError("JUNTA_PRIVATE_KEY y DOCUMENT_TOKEN_ADDRESS son obligatorios")

    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    account = w3.eth.account.from_key(PRIVATE_KEY.replace("0x", "").strip())
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(DOCUMENT_TOKEN_ADDRESS),
        abi=GREEN_LICENSE_ABI,
    )
    tx = contract.functions.mintDocument(
        document_hash,
        document_type,
        metadata_ipfs_hash,
        responsible,
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 500000,
            "gasPrice": w3.to_wei("50", "gwei"),
        }
    )
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash_bytes.hex()


def main():
    parser = argparse.ArgumentParser(description="Firmar documento en GaiaChain (GreenLicenseToken)")
    parser.add_argument("document_hash", help="SHA-512 del documento (hex) o ruta al archivo para calcularlo")
    parser.add_argument("document_type", help="Ej: licencia_ambiental, parte_incendio, tala")
    parser.add_argument("metadata_ipfs_hash", help="Hash IPFS de metadatos JSON")
    parser.add_argument("--responsible", default="Junta de Extremadura", help="Responsable del documento")
    parser.add_argument("--from-file", action="store_true", help="document_hash es ruta de archivo; calcular SHA-512")
    args = parser.parse_args()

    doc_hash = sha512_file(args.document_hash) if args.from_file else args.document_hash

    try:
        tx_hash = sign_document(
            doc_hash,
            args.document_type,
            args.metadata_ipfs_hash,
            args.responsible,
        )
        print(tx_hash)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
