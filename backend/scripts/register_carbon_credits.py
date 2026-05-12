#!/usr/bin/env python3
"""
Registra créditos de CO₂ ahorrados en GaiaChain 2.0 (contrato CarbonCredit).
Uso: python3 scripts/register_carbon_credits.py <farm_address_0x> <kg_co2>
Ejemplo: python3 scripts/register_carbon_credits.py 0x1234567890abcdef... 12
"""
import os
import sys

def main():
    if len(sys.argv) != 3:
        print("Uso: register_carbon_credits.py <farm_address> <kg_co2>", file=sys.stderr)
        sys.exit(1)
    farm_id = sys.argv[1]
    kg_co2 = int(sys.argv[2])

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    contract_address = os.getenv("CARBON_CREDIT_CONTRACT_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")

    if not contract_address or not private_key:
        print("Definir GAIA_CHAIN_RPC, CARBON_CREDIT_CONTRACT_ADDRESS y PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    contract_address = Web3.to_checksum_address(contract_address)
    farm_address = Web3.to_checksum_address(farm_id)

    abi = [{"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"issueCredits","outputs":[],"stateMutability":"nonpayable","type":"function"}]
    contract = w3.eth.contract(address=contract_address, abi=abi)
    amount_credits = kg_co2 * 1000

    tx = contract.functions.issueCredits(farm_address, amount_credits).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    return tx_hash.hex()

if __name__ == "__main__":
    main()
