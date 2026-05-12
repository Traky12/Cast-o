#!/usr/bin/env python3
"""
Registra batches de compost en GaiaChain (contrato CompostToken).
Uso: python3 scripts/register_compost.py <kg> <temperature> <humidity> <ph> <batch_id>
Ejemplo: python3 scripts/register_compost.py 100 60 50 70 extremadura-farm-batch-1
Variables: GAIA_CHAIN_RPC, COMPOST_TOKEN_ADDRESS, PRIVATE_KEY
"""
import os
import sys


COMPOST_ABI = [
    {
        "inputs": [
            {"name": "kg", "type": "uint256"},
            {"name": "temperature", "type": "uint256"},
            {"name": "humidity", "type": "uint256"},
            {"name": "ph", "type": "uint256"},
            {"name": "batchId", "type": "string"},
        ],
        "name": "registerCompostQuality",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def main():
    if len(sys.argv) != 6:
        print(
            "Uso: register_compost.py <kg> <temperature> <humidity> <ph> <batch_id>",
            file=sys.stderr,
        )
        sys.exit(1)
    kg = int(sys.argv[1])
    temperature = int(sys.argv[2])
    humidity = int(sys.argv[3])
    ph = int(sys.argv[4])
    batch_id = sys.argv[5]

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("COMPOST_TOKEN_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")

    if not contract_address or not private_key:
        print(
            "Definir GAIA_CHAIN_RPC, COMPOST_TOKEN_ADDRESS y PRIVATE_KEY",
            file=sys.stderr,
        )
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    contract_address = Web3.to_checksum_address(contract_address)
    contract = w3.eth.contract(address=contract_address, abi=COMPOST_ABI)

    tx = contract.functions.registerCompostQuality(
        kg, temperature, humidity, ph, batch_id
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
