# CASTUO_NFT — Certificación CASTUO_GOLD_V1

Contrato ERC-721 mínimo (sin OpenZeppelin) para NFT de integridad del bundle GOLD.

- **Testnet-first:** desplegar y mintar en testnet; ver [docs/NFT-TESTNET-STRATEGY-CASTUO-GOLD-V1.md](../../docs/NFT-TESTNET-STRATEGY-CASTUO-GOLD-V1.md).
- **ABI:** incluido en `CASTUO_NFT_ABI.json`. **BIN:** generar con `python scripts/nft/compile_castuo_nft.py` (requiere `solc` en PATH) o manualmente: `solc --abi --bin -o contracts/nft/ CASTUO_NFT.sol` y volcar el `.bin` en `CASTUO_NFT_BIN.json` como `{"bytecode": "0x..."}`.
- **Scripts:** [scripts/nft/](../../scripts/nft/) — `compile_castuo_nft.py`, `deploy_castuo_nft_testnet.py`, `mint_castuo_nft_testnet.py`, `recover_from_nft.py`, `create_test_bundle.py`.
