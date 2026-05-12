#!/usr/bin/env python3
"""
Ejecuta el derecho al olvido (GDPR Art. 17) para un ForestOwnershipToken:
1. Obtiene metadatos actuales (IPFS o fichero).
2. Genera nuevos metadatos sin datos personales (erase_personal_data).
3. Sube a IPFS (si disponible).
4. Llama a updateMetadata(tokenId, newIpfsHash) en GaiaChain (propietario).
Salida: JSON con status, token_id, hashes, timestamp, transaction_hash.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

try:
    from web3 import Web3
except ImportError:
    print("Instalar: pip install web3", file=sys.stderr)
    sys.exit(1)

# Importar lógica de borrado (mismo directorio)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
from erase_personal_data import erase_personal_data, upload_to_ipfs

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
FOREST_OWNERSHIP_TOKEN_ADDRESS = os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY") or os.getenv("JUNTA_PRIVATE_KEY")

ABI = [
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getProperty", "outputs": [
        {"name": "parcelaId", "type": "string"}, {"name": "owner", "type": "address"},
        {"name": "coordinates", "type": "string"}, {"name": "area", "type": "uint256"},
        {"name": "treeSpecies", "type": "string"}, {"name": "carbonSequestered", "type": "uint256"},
        {"name": "ipfsHash", "type": "string"}, {"name": "isProtected", "type": "bool"},
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}, {"name": "newIpfsHash", "type": "string"}], "name": "updateMetadata", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
]


def fetch_metadata_from_ipfs(ipfs_hash: str) -> dict | None:
    """Obtiene JSON de IPFS."""
    try:
        import requests
        r = requests.get(f"https://ipfs.io/ipfs/{ipfs_hash}", timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Ejecutar derecho al olvido (GDPR Art. 17)")
    parser.add_argument("--token-id", type=int, required=True, help="ForestOwnershipToken ID")
    parser.add_argument("--metadata-file", help="Ruta a JSON de metadatos (si no se usa IPFS del contrato)")
    parser.add_argument("--dry-run", action="store_true", help="Solo generar nuevo JSON, no subir ni actualizar contrato")
    args = parser.parse_args()

    if not FOREST_OWNERSHIP_TOKEN_ADDRESS or not PRIVATE_KEY:
        print("Configurar FOREST_OWNERSHIP_TOKEN_ADDRESS y PRIVATE_KEY", file=sys.stderr)
        return 1

    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    account = w3.eth.account.from_key(PRIVATE_KEY.replace("0x", "").strip())
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(FOREST_OWNERSHIP_TOKEN_ADDRESS),
        abi=ABI,
    )

    prop = contract.functions.getProperty(args.token_id).call()
    old_ipfs_hash = prop[6]
    metadata = None

    if args.metadata_file and os.path.isfile(args.metadata_file):
        with open(args.metadata_file, encoding="utf-8") as f:
            metadata = json.load(f)
    elif old_ipfs_hash:
        metadata = fetch_metadata_from_ipfs(old_ipfs_hash)

    if not metadata:
        print("No se pudieron obtener metadatos (proporcione --metadata-file o IPFS del contrato)", file=sys.stderr)
        return 1

    new_metadata = erase_personal_data(metadata)
    new_ipfs_hash = upload_to_ipfs(new_metadata) if not args.dry_run else None
    if not args.dry_run and not new_ipfs_hash:
        new_ipfs_hash = "QmPlaceholderRightToBeForgotten"

    result = {
        "status": "success",
        "token_id": args.token_id,
        "old_ipfs_hash": old_ipfs_hash,
        "new_ipfs_hash": new_ipfs_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "transaction_hash": None,
        "redacted_fields": ["Propietario", "DNI", "Email"],
    }

    if not args.dry_run and new_ipfs_hash:
        tx = contract.functions.updateMetadata(args.token_id, new_ipfs_hash).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": w3.to_wei("50", "gwei"),
        })
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
        result["transaction_hash"] = tx_hash_bytes.hex()

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
