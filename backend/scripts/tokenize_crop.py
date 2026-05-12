#!/usr/bin/env python3
"""
Tokeniza cultivos (lechugas, cannabis, tomates, etc.) en GaiaChain 2.0 (CropToken).
Uso: python3 scripts/tokenize_crop.py <farm_id> <crop_type> <quantity> <co2_saved_kg> [verra_project_id]
Crop types: lettuce=0, cannabis=1, tomato=2, strawberry=3
Ejemplo: python3 scripts/tokenize_crop.py farm-eu-001 lettuce 288 12 VCS-1234
"""
import os
import sys

CROP_TYPE_MAP = {"lettuce": 0, "cannabis": 1, "tomato": 2, "strawberry": 3}


def main():
    if len(sys.argv) < 5:
        print(
            "Uso: tokenize_crop.py <farm_id> <crop_type> <quantity> <co2_saved_kg> [verra_project_id]",
            file=sys.stderr,
        )
        sys.exit(1)
    farm_id = sys.argv[1]
    crop_type_name = sys.argv[2].lower()
    quantity = int(sys.argv[3])
    co2_saved = int(sys.argv[4])
    verra_project_id = sys.argv[5] if len(sys.argv) > 5 else ""

    if crop_type_name not in CROP_TYPE_MAP:
        print("crop_type debe ser: lettuce, cannabis, tomato, strawberry", file=sys.stderr)
        sys.exit(1)
    crop_type = CROP_TYPE_MAP[crop_type_name]

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("CROP_TOKEN_CONTRACT_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")

    if not contract_address or not private_key:
        print("Definir GAIA_CHAIN_RPC, CROP_TOKEN_CONTRACT_ADDRESS y PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    contract_address = Web3.to_checksum_address(contract_address)

    abi = [
        {
            "inputs": [
                {"name": "farmId", "type": "string"},
                {"name": "cropType", "type": "uint8"},
                {"name": "quantity", "type": "uint256"},
                {"name": "co2Saved", "type": "uint256"},
                {"name": "verraProjectId", "type": "string"},
            ],
            "name": "tokenizeCrop",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]
    contract = w3.eth.contract(address=contract_address, abi=abi)

    tx = contract.functions.tokenizeCrop(
        farm_id, crop_type, quantity, co2_saved, verra_project_id
    ).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 300000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    return tx_hash.hex()


if __name__ == "__main__":
    main()
