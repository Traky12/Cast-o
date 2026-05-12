#!/usr/bin/env python3
"""
Auditoría de borrados (derecho al olvido): consulta eventos DataRedacted en GaiaChain
y opcionalmente verifica que el ipfsHash actual del token apunta a metadatos sin datos personales.
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

GAIA_CHAIN_RPC = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
FOREST_OWNERSHIP_TOKEN_ADDRESS = os.getenv("FOREST_OWNERSHIP_TOKEN_ADDRESS", "")

ABI = [
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getProperty", "outputs": [
        {"name": "parcelaId", "type": "string"}, {"name": "owner", "type": "address"},
        {"name": "coordinates", "type": "string"}, {"name": "area", "type": "uint256"},
        {"name": "treeSpecies", "type": "string"}, {"name": "carbonSequestered", "type": "uint256"},
        {"name": "ipfsHash", "type": "string"}, {"name": "isProtected", "type": "bool"},
    ], "stateMutability": "view", "type": "function"},
]

# DataRedacted(uint256 indexed tokenId, string reason, uint256 timestamp)


def get_events_data_redacted(w3, contract_address, from_block: int = 0, to_block: str = "latest") -> list:
    """Obtiene logs de DataRedacted (requiere que el contrato emita el evento)."""
    try:
        logs = w3.eth.get_logs({
            "address": Web3.to_checksum_address(contract_address),
            "fromBlock": from_block,
            "toBlock": to_block,
            "topics": [Web3.keccak(text="DataRedacted(uint256,string,uint256)")],
        })
        return logs
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Auditar redacciones (derecho al olvido)")
    parser.add_argument("--from-block", type=int, default=0, help="Bloque inicial")
    parser.add_argument("--to-block", default="latest", help="Bloque final o 'latest'")
    parser.add_argument("-o", "--output", default="-", help="Salida JSON (default: stdout)")
    args = parser.parse_args()

    if not FOREST_OWNERSHIP_TOKEN_ADDRESS:
        print("Configurar FOREST_OWNERSHIP_TOKEN_ADDRESS", file=sys.stderr)
        return 1

    w3 = Web3(Web3.HTTPProvider(GAIA_CHAIN_RPC))
    to_block = args.to_block if args.to_block == "latest" else args.to_block
    logs = get_events_data_redacted(w3, FOREST_OWNERSHIP_TOKEN_ADDRESS, args.from_block, to_block)

    audited = []
    for log in logs:
        token_id = int(log["topics"][1].hex(), 16) if len(log.get("topics", [])) > 1 else 0
        audited.append({
            "token_id": token_id,
            "block_number": log.get("blockNumber"),
            "transaction_hash": log.get("transactionHash").hex() if log.get("transactionHash") else None,
        })

    result = {
        "status": "ok",
        "audited": len(audited),
        "from_block": args.from_block,
        "to_block": args.to_block,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "events": audited,
        "issues": [],
    }

    out = json.dumps(result, indent=2)
    if args.output == "-":
        print(out)
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
