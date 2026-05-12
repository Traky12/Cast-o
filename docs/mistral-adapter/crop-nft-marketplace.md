# CropNFT: NFTs de cultivos + Marketplace

NFTs únicos por cultivo (lechuga, cannabis, tomate) con metadatos inmutables en GaiaChain 2.0 y marketplace para compra/venta.

---

## Paso 1: Contrato CropNFT.sol (ERC-721)

**Ubicación:** `blockchain/contracts/CropNFT.sol`

- **OpenZeppelin:** ERC721, Counters, Strings.
- **CropMetadata:** cropType, farmId, harvestDate, location, co2Saved, ipfsHash.
- **mintNFT(to, cropType, farmId, location, co2Saved, ipfsHash):** mintea un NFT y guarda metadatos on-chain.
- **getMetadata(tokenId), tokenURI(tokenId):** lectura de metadatos y URI (IPFS).

### Desplegar

```bash
cd blockchain
npm install
npx hardhat compile
npx hardhat run scripts/deploy-crop-nft.js --network gaiachain
export CROP_NFT_ADDRESS="0x..."
```

---

## Paso 2: Metadatos en IPFS

**Script:** `backend/scripts/generate_crop_metadata.py`

Genera JSON ERC-721 (name, description, image, attributes) y lo sube a IPFS. Opcional: subir imagen de cultivo.

```bash
# Con IPFS (ipfshttpclient) e Infura/IPFS local
pip install ipfshttpclient
export IPFS_GATEWAY="/dns/ipfs.infura.io/tcp/5001/https"
python3 scripts/generate_crop_metadata.py lettuce extremadura-farm-001 "39.4769°N, 6.3706°W" 12 images/lettuce.jpg
# Salida: hash IPFS (ej. QmXoypiz...)
```

Sin IPFS devuelve un hash placeholder; en producción configurar nodo IPFS o Infura.

---

## Paso 3: Minting desde el backend

**Script:** `backend/scripts/mint_crop_nft.py`

```bash
export GAIA_CHAIN_RPC="https://gaiachain.castuo-system.com"
export CROP_NFT_ADDRESS="0x..."
export PRIVATE_KEY="..."
python3 scripts/mint_crop_nft.py 0xAgricultor lettuce extremadura-farm-001 "39.4769°N, 6.3706°W" 12 QmXoypiz...
```

**Consultar propietario:** `backend/scripts/get_nft_owner.py`

```bash
python3 scripts/get_nft_owner.py 1
```

---

## Paso 4: Marketplace CropNFTMarketplace.sol

**Ubicación:** `blockchain/contracts/CropNFTMarketplace.sol`

- **createListing(tokenId, price):** el vendedor debe haber aprobado este contrato en CropNFT (`approve(marketplace, tokenId)` o `setApprovalForAll(marketplace, true)`).
- **buyListing(listingId):** pago en ETH (msg.value); el contrato transfiere el NFT del vendedor al comprador y reparte el pago (2,5% fee al owner).
- **getListing, getAllListings:** listado de ofertas.

### Desplegar marketplace

```bash
export CROP_NFT_ADDRESS="0x..."
npx hardhat run scripts/deploy-crop-nft-marketplace.js --network gaiachain
export CROP_NFT_MARKETPLACE_ADDRESS="0x..."
```

### Frontend React

**Ubicación:** `frontend/crop-nft-marketplace/`

- Conectar MetaMask, listar listings, crear listing (tokenId + precio en ETH), comprar.
- Variables de build: `REACT_APP_CROP_NFT_ADDRESS`, `REACT_APP_CROP_NFT_MARKETPLACE_ADDRESS`.

```bash
cd frontend/crop-nft-marketplace
REACT_APP_CROP_NFT_ADDRESS=0x... REACT_APP_CROP_NFT_MARKETPLACE_ADDRESS=0x... npm run build
```

### Docker y Kubernetes

- **Dockerfile:** multi-stage (Node build → nginx).
- **Kubernetes:** `kubernetes/marketplace/crop-nft-marketplace.yaml` (Deployment 2 réplicas + Service LoadBalancer).

Para ArgoCD: crear app apuntando al manifest o al directorio que incluya este recurso y opcionalmente sincronizar en el workflow global:

```yaml
# Opcional en .github/workflows/argocd-sync-global.yml
- name: Sync CropNFT Marketplace (opcional)
  run: argocd app sync crop-nft-marketplace || true
```

---

## Paso 5: Validación

1. **Mintar NFT:** generar metadatos con `generate_crop_metadata.py`, luego `mint_crop_nft.py`.
2. **Listar:** en el frontend (o llamando a `createListing`), aprobar el marketplace en CropNFT y crear listing (tokenId, precio ETH).
3. **Comprar:** desde otra wallet, `buyListing(listingId)` con `value = price`.
4. **Verificar:** `get_nft_owner.py <tokenId>` y explorador GaiaChain.

```bash
echo "🎉 NFTs DE CULTIVOS ACTIVADOS: 1 NFT = 1 LECHUGA CULTIVADA + TRAZABILIDAD BLOCKCHAIN + MERCADO SECUNDARIO! 🌱"
```

---

[Runbook](runbook-despliegue-global.md) · [NFTs dinámicos + OpenSea](dynamic-nft-opensea.md) · [BioCoin + AirCarbon](biocoin-aircarbon.md) · [Chainlink + Marketplace](chainlink-marketplace.md)
