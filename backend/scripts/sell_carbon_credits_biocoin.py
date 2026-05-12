#!/usr/bin/env python3
"""
Comprar créditos de carbono con BioCoin (GaiaChain 2.0 - BioCoinCarbonMarket).
Uso: python3 scripts/sell_carbon_credits_biocoin.py <kg_co2>
Env: GAIA_CHAIN_RPC, BIOCOIN_CARBON_MARKET_ADDRESS, BIOCOIN_ADDRESS, PRIVATE_KEY (comprador).
"""
import os
import sys

def _w3_and_account(private_key: str):
    from web3 import Web3
    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    return w3, account


def approve_biocoin_spending(w3, bio_coin_contract, owner_account, spender: str, amount: int) -> str:
    abi_erc20 = [{"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]
    token = w3.eth.contract(address=spender, abi=abi_erc20) if bio_coin_contract.address != spender else bio_coin_contract
    tx = token.functions.approve(spender, amount).build_transaction({
        "from": owner_account.address,
        "nonce": w3.eth.get_transaction_count(owner_account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed = owner_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()


def buy_carbon_credits(kg_co2: int) -> str:
    from web3 import Web3
    rpc = os.getenv("GAIA_CHAIN_RPC", "https://gaiachain.castuo-system.com")
    market_address = os.getenv("BIOCOIN_CARBON_MARKET_ADDRESS", "")
    bio_coin_address = os.getenv("BIOCOIN_ADDRESS", "")
    private_key = os.getenv("PRIVATE_KEY", "")

    if not market_address or not private_key or not bio_coin_address:
        print("Definir GAIA_CHAIN_RPC, BIOCOIN_CARBON_MARKET_ADDRESS, BIOCOIN_ADDRESS, PRIVATE_KEY", file=sys.stderr)
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(rpc))
    account = w3.eth.account.from_key(private_key)
    market_address = Web3.to_checksum_address(market_address)
    bio_coin_address = Web3.to_checksum_address(bio_coin_address)

    abi_market = [
        {"inputs":[],"name":"pricePerKgCO2","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
        {"inputs":[{"name":"kgCO2","type":"uint256"}],"name":"buyCarbonCredits","outputs":[],"stateMutability":"nonpayable","type":"function"},
    ]
    market = w3.eth.contract(address=market_address, abi=abi_market)
    price = market.functions.pricePerKgCO2().call()
    total_biocoin = kg_co2 * price

    abi_erc20 = [{"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]
    bio_coin = w3.eth.contract(address=bio_coin_address, abi=abi_erc20)
    tx_approve = bio_coin.functions.approve(market_address, total_biocoin).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed_a = account.sign_transaction(tx_approve)
    w3.eth.send_raw_transaction(signed_a.rawTransaction)

    tx_buy = market.functions.buyCarbonCredits(kg_co2).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 300000,
        "gasPrice": w3.to_wei("50", "gwei"),
    })
    signed_b = account.sign_transaction(tx_buy)
    tx_hash = w3.eth.send_raw_transaction(signed_b.rawTransaction)
    print(tx_hash.hex())
    return tx_hash.hex()


def main():
    if len(sys.argv) < 2:
        print("Uso: sell_carbon_credits_biocoin.py <kg_co2>", file=sys.stderr)
        sys.exit(1)
    kg_co2 = int(sys.argv[1])
    buyer_address = os.getenv("PRIVATE_KEY")
    if not buyer_address:
        print("Definir PRIVATE_KEY (cuenta compradora)", file=sys.stderr)
        sys.exit(1)
    buy_carbon_credits(kg_co2)


if __name__ == "__main__":
    main()
