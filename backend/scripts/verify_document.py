#!/usr/bin/env python3
"""
Verificación de documentos: compara SHA-512 local con el hash registrado en GaiaChain (GreenLicenseToken).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

try:
    from web3 import Web3
except ImportError:
    print("Instalar: pip install web3", file=sys.stderr)
    sys.exit(1)

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
DOCUMENT_TOKEN_ADDRESS = os.getenv("DOCUMENT_TOKEN_ADDRESS", "")

ABI_GET_METADATA = [
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
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}, {"name": "documentHash", "type": "string"}],
        "name": "verifyDocument",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


def sha512_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha512(f.read()).hexdigest()


def verify_document(token_id: int, document_path: str) -> bool:
    if not DOCUMENT_TOKEN_ADDRESS:
        raise ValueError("DOCUMENT_TOKEN_ADDRESS es obligatorio")

    local_hash = sha512_file(document_path)
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(DOCUMENT_TOKEN_ADDRESS),
        abi=ABI_GET_METADATA,
    )
    return contract.functions.verifyDocument(token_id, local_hash).call()


def get_metadata(token_id: int) -> tuple:
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(DOCUMENT_TOKEN_ADDRESS),
        abi=ABI_GET_METADATA,
    )
    return contract.functions.getDocumentMetadata(token_id).call()


def main():
    parser = argparse.ArgumentParser(description="Verificar documento contra GaiaChain")
    parser.add_argument("token_id", type=int, help="ID del token (GreenLicenseToken)")
    parser.add_argument("document_path", help="Ruta al documento local (PDF/JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Mostrar metadatos")
    args = parser.parse_args()

    if not os.path.isfile(args.document_path):
        print(f"Archivo no encontrado: {args.document_path}", file=sys.stderr)
        return 1
    if not DOCUMENT_TOKEN_ADDRESS:
        print("Configurar DOCUMENT_TOKEN_ADDRESS", file=sys.stderr)
        return 1

    try:
        valid = verify_document(args.token_id, args.document_path)
        if args.verbose and valid:
            meta = get_metadata(args.token_id)
            print("documentHash:", meta[0][:32] + "...")
            print("documentType:", meta[1])
            print("ipfsHash:", meta[2])
            print("timestamp:", meta[3])
            print("responsible:", meta[4])
        print("Documento válido: ✅ Sí" if valid else "Documento válido: ❌ No")
        return 0 if valid else 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
