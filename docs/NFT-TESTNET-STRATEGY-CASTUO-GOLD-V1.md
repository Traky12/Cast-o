# Estrategia Testnet-first para NFT CASTUO_GOLD_V1

*Como probar el aceite en un vaso antes de embotellarlo para vender.*

---

## 1. Testnet vs Mainnet

| Criterio | Testnet (GaiaChain) | Mainnet (GaiaChain) |
|----------|---------------------|----------------------|
| **Coste** | Gas sin valor real | Gas real (GAIA) |
| **Riesgo** | Cero para producción | Error = nuevo deployment |
| **Cumplimiento** | Pruebas internas | Válido para AEMPS/inversores |
| **Velocidad** | ~5 s bloque (referencial) | ~15 s |
| **Flexibilidad** | Borrar/rehacer NFT | Inmutable |
| **Visibilidad** | testnet.gaiachain.eu | explorer.gaiachain.eu |
| **Analogía** | Probar aceite en vaso antes de embotellar | Embotellar y etiquetar para mercado |

**Recomendación:** Empezar siempre en **testnet** (seguridad, ahorro, iteración, validar flujo antes de mainnet).

---

## 2. Plan de acción (testnet)

1. **Entorno:** RPC testnet, wallet nueva solo testnet, faucet GAIA.
2. **Desplegar contrato:** `scripts/nft/deploy_castuo_nft_testnet.py` (usa `TESTNET_RPC_URL`, `TESTNET_PRIVATE_KEY` en `.env`).
3. **Mintar NFT:** `scripts/nft/mint_castuo_nft_testnet.py` (ZIP de prueba, metadatos en IPFS).
4. **Verificar:** Explorador testnet + comprobar `tokenURI` y `getComplianceData`.
5. **Recuperación:** `scripts/nft/recover_from_nft.py` — validar hash ZIP vs metadatos.
6. **Iterar** hasta que todo funcione; luego **mainnet** con datos reales.

---

## 3. Cuándo pasar a mainnet

- [ ] NFT en testnet mintado sin errores.
- [ ] Recuperación al 100 %.
- [ ] Metadatos alineados con normativa (GDPR, eIDAS2, etc.).
- [ ] Copias de seguridad del ZIP, log y certificado.

*Primero siembras en el bancal pequeño; cuando está fuerte, trasplantas al campo grande.*

---

## 4. Estructura de scripts y contrato

| Elemento | Ubicación |
|----------|-----------|
| Contrato NFT (ERC-721 + cumplimiento) | `contracts/nft/CASTUO_NFT.sol` |
| ABI (incluido) / BIN (generar) | `contracts/nft/CASTUO_NFT_ABI.json`, `CASTUO_NFT_BIN.json` — generar BIN con `scripts/nft/compile_castuo_nft.py` (requiere solc en PATH) |
| Despliegue testnet | `scripts/nft/deploy_castuo_nft_testnet.py` |
| Mint testnet | `scripts/nft/mint_castuo_nft_testnet.py` |
| Recuperación desde NFT | `scripts/nft/recover_from_nft.py` |
| ZIP de prueba | `scripts/nft/create_test_bundle.py` → `CASTUO_GOLD_V1_TEST.zip` |
| Metadatos ejemplo | `scripts/nft/nft_metadata_test.example.json` |
| Dashboard Grafana / Prometheus | `scripts/nft/castuo_nft_dashboard.example.json`, `scripts/nft/prometheus_gaiachain_example.yml` |
| Variables de entorno | `scripts/nft/.env.example` (copiar a `.env`; no commitear claves) |

---

## 5. Errores frecuentes y soluciones

| Error | Causa | Solución |
|-------|--------|----------|
| Transaction ran out of gas | Gas insuficiente | Subir `gas` en la TX |
| Contract deployment failed | Bytecode/ABI | Recompilar con solc y revisar JSON |
| IPFS hash not found | CID inexistente | Subir metadatos a Pinata/Infura |
| Invalid private key | Formato/clave | Verificar `TESTNET_PRIVATE_KEY` en hex |
| Nonce too low/high | Desincronizado | Usar `get_transaction_count` actual |

---

## 6. Checklist post-mint (testnet)

| Item | Verificado | Notas |
|------|------------|--------|
| NFT mintado en testnet | ☐ | TX: _____ |
| Metadatos accesibles en IPFS | ☐ | URI: ipfs://_____ |
| Hash del ZIP coincide | ☐ | SHA-256 |
| Cumplimiento registrado | ☐ | TX registerCompliance |
| Recuperación exitosa | ☐ | `recover_from_nft.py` |

---

*Documento vivo. RPC y URLs de GaiaChain son referenciales hasta tener red desplegada.*
