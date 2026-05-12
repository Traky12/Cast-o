#!/usr/bin/env python3
"""
Verificación de permisos de tala en GaiaChain (Orden 15/03/2021 — Gestión de Montes Públicos).
Permite a agentes forestales validar autorizaciones (PublicForestToken / GreenLicenseToken).
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    from web3 import Web3
except ImportError:
    print("Instalar: pip install web3", file=sys.stderr)
    sys.exit(1)

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
DOCUMENT_TOKEN_ADDRESS = os.getenv("DOCUMENT_TOKEN_ADDRESS", "")
FOREST_PERMIT_TOKEN_ADDRESS = os.getenv("FOREST_PERMIT_TOKEN_ADDRESS", DOCUMENT_TOKEN_ADDRESS)

# GreenLicenseToken / documento genérico: getDocumentMetadata(tokenId)
ABI_METADATA = [
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


def verify_forest_permit(token_id: int) -> dict | None:
    """Obtiene metadatos del permiso forestal por token_id. None si no existe."""
    addr = FOREST_PERMIT_TOKEN_ADDRESS or DOCUMENT_TOKEN_ADDRESS
    if not addr:
        raise ValueError("FOREST_PERMIT_TOKEN_ADDRESS o DOCUMENT_TOKEN_ADDRESS es obligatorio")
    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(addr),
        abi=ABI_METADATA,
    )
    try:
        meta = contract.functions.getDocumentMetadata(token_id).call()
    except Exception:
        return None
    doc_hash, doc_type, ipfs_hash, timestamp, responsible = meta
    return {
        "documentHash": doc_hash,
        "documentType": doc_type,
        "ipfsHash": ipfs_hash,
        "timestamp": int(timestamp),
        "responsible": responsible,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verificar permiso forestal en GaiaChain (Orden 15/03/2021)"
    )
    parser.add_argument("token_id", type=int, help="ID del token de permiso de tala")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostrar metadatos")
    args = parser.parse_args()

    if not FOREST_PERMIT_TOKEN_ADDRESS and not DOCUMENT_TOKEN_ADDRESS:
        print("Configurar FOREST_PERMIT_TOKEN_ADDRESS o DOCUMENT_TOKEN_ADDRESS", file=sys.stderr)
        return 1
    try:
        data = verify_forest_permit(args.token_id)
        if data is None:
            print("Permiso forestal: ❌ No encontrado o token inválido")
            return 2
        print("Permiso forestal: ✅ Válido")
        if args.verbose:
            print("  Tipo:", data["documentType"])
            print("  Responsable:", data["responsible"])
            print("  Timestamp:", data["timestamp"])
            if data["ipfsHash"]:
                print("  IPFS:", data["ipfsHash"])
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
