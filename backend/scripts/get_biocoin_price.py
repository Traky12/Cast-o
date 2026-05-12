#!/usr/bin/env python3
"""
Obtener el precio de BioCoin/USD desde el contrato BioCoinPriceConsumer (Chainlink).
Uso: python3 scripts/get_biocoin_price.py
Env: GAIA_CHAIN_RPC, BIOCOIN_PRICE_CONSUMER_ADDRESS
"""
import os
import sys

def main():
    try:
        from web3 import Web3
    except ImportError:
        print("Instalar web3: pip install web3", file=sys.stderr)
        sys.exit(1)

    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    consumer_address = os.getenv("BIOCOIN_PRICE_CONSUMER_ADDRESS", "")
    if not consumer_address:
        print("Definir BIOCOIN_PRICE_CONSUMER_ADDRESS", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    consumer_address = Web3.to_checksum_address(consumer_address)
    abi = [
        {"inputs": [], "name": "getBioCoinPriceUSD", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
        {"inputs": [], "name": "getLatestPrice", "outputs": [{"name": "", "type": "int256"}], "stateMutability": "nonpayable", "type": "function"},
    ]
    contract = w3.eth.contract(address=consumer_address, abi=abi)
    price = contract.functions.getBioCoinPriceUSD().call()
    print(f"Precio actual de BioCoin: ${price} USD")
    return price


if __name__ == "__main__":
    main()
