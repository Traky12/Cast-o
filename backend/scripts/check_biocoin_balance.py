#!/usr/bin/env python3
"""
Consultar saldo de BioCoin de una dirección en GaiaChain.
Uso: python3 scripts/check_biocoin_balance.py <address_0x>
"""
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Uso: check_biocoin_balance.py <address_0x>", file=sys.stderr)
        sys.exit(1)
    address = sys.argv[1]

    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    bio_coin_address = os.getenv("BIOCOIN_ADDRESS", "")
    if not bio_coin_address:
        print("Definir BIOCOIN_ADDRESS", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    address = Web3.to_checksum_address(address)
    bio_coin_address = Web3.to_checksum_address(bio_coin_address)

    abi = [{"inputs":[{"name":"account","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
    contract = w3.eth.contract(address=bio_coin_address, abi=abi)
    balance = contract.functions.balanceOf(address).call()
    decimals = 18
    if hasattr(contract.functions, "decimals"):
        try:
            decimals = contract.functions.decimals().call()
        except Exception:
            pass
    balance_human = balance / (10 ** decimals)
    print(f"Saldo BioCoin ({address}): {balance_human}")
    return balance_human


if __name__ == "__main__":
    main()
