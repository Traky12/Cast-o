"""
Ejemplo PLANTILLA: mint NFT en cadena compatible EVM/Web3.
NO ejecutar con claves reales en repo. Sustituir RPC, contrato, IPFS tras despliegue GaiaChain/red propia.
"""
# from web3 import Web3
# import hashlib, json, os
#
# def main():
#     w3 = Web3(Web3.HTTPProvider(os.environ["CASTUO_RPC_URL"]))
#     assert w3.is_connected()
#     zip_path = "CASTUO_GOLD_V1.zip"
#     zip_hash = hashlib.sha256(open(zip_path, "rb").read()).hexdigest()
#     # metadata en IPFS; mint ERC-721 con tokenURI ipfs://...
#     ...
# if __name__ == "__main__":
#     main()
raise SystemExit(
    "Plantilla: copiar a entorno seguro, completar RPC/contrato/IPFS y descomentar. "
    "Nunca commitear private_key."
)
