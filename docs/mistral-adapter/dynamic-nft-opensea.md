# NFTs dinámicos + OpenSea + Cannabis y fresas

NFTs que reflejan el crecimiento en tiempo real (growthStage 0-100), integración con OpenSea y tokenización de cannabis medicinal y fresas.

**Release:** [v1.7.0 — Estado y flujo producción](release-v1.7.0.md)

---

## Paso 1: DynamicCropNFT (crecimiento en tiempo real)

### 1.1 Contrato DynamicCropNFT.sol

**Ubicación:** `blockchain/contracts/DynamicCropNFT.sol`

- **ERC721** con metadatos actualizables.
- **CropMetadata:** cropType, farmId, plantDate, lastUpdate, ipfsHash, growthStage (0-100), strain, thcCbdRatio, brixLevel.
- **mintNFT(to, cropType, farmId, initialIpfsHash, strain, thcCbdRatio, brixLevel):** mintea con growthStage 0. Para lechuga usar strain="" y thcCbdRatio=0, brixLevel=0. Script de ayuda: `mint_dynamic_lettuce_nft.py <to> <farm_id> <ipfs_hash>`.
- **updateGrowthStage(tokenId, newGrowthStage, newIpfsHash):** actualiza etapa de crecimiento y hash IPFS (cualquiera puede llamar; en producción restringir al backend/finca).

### 1.2 Desplegar

```bash
cd blockchain
npx hardhat compile
npx hardhat run scripts/deploy-dynamic-nft.js --network gaiachain
export DYNAMIC_NFT_ADDRESS="0x..."
```

### 1.3 Actualizar growth stage (script)

**Script:** `backend/scripts/update_dynamic_nft.py`

Genera metadatos (nombre, imagen, atributos Growth Stage / Last Update), los sube a IPFS y llama a `updateGrowthStage` en GaiaChain.

```bash
export GAIA_CHAIN_RPC="https://gaiachain.castuo-system.com"
export DYNAMIC_NFT_ADDRESS="0x..."
export PRIVATE_KEY="..."
python3 scripts/update_dynamic_nft.py 1 50 images/lettuce_50percent.jpg
```

Variables opcionales: `IPFS_GATEWAY`.

### 1.4 Monitor IoT (automatización)

**Script:** `backend/scripts/iot_growth_monitor.py`

Simula etapas de crecimiento y llama a `update_dynamic_nft.py` en cada paso. En producción sustituir por datos reales de sensores (pH, EC, cámara).

```bash
# 10 pasos de 10%, cada 86400 s (1 día). Desde repo root: backend/scripts/iot_growth_monitor.py
python3 scripts/iot_growth_monitor.py 1 86400 10
```

---

## Paso 2: Integración con OpenSea

### 2.1 Requisitos del contrato

- **ERC721** (DynamicCropNFT ya lo cumple).
- **tokenURI** apuntando a metadatos en IPFS.
- Metadatos compatibles: name, description, image, attributes (trait_type, value).

Ejemplo de metadatos compatibles con OpenSea:

```json
{
  "name": "Lettuce #1 (Growth Stage: 50%)",
  "description": "A hydroponic lettuce cultivated with zero waste in Extremadura, Spain. CO₂ saved: 12kg.",
  "image": "ipfs://QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco/lettuce_50percent.jpg",
  "attributes": [
    {"trait_type": "Crop Type", "value": "Lettuce"},
    {"trait_type": "Farm ID", "value": "extremadura-farm-001"},
    {"trait_type": "Growth Stage", "value": "50%"},
    {"trait_type": "CO₂ Saved", "value": "12kg"},
    {"trait_type": "Harvest Date", "value": "2026-03-20"}
  ]
}
```

### 2.2 Desplegar en Polygon (para OpenSea)

```bash
export POLYGON_RPC="https://polygon-rpc.com"
export PRIVATE_KEY="..."
npx hardhat run scripts/deploy-dynamic-nft.js --network polygon
export DYNAMIC_NFT_ADDRESS="0x..."
```

### 2.3 Verificar y listar en OpenSea

1. Ir a [OpenSea](https://opensea.io) (o Testnets para pruebas).
2. **Create** → **My Collections** → **Add a contract**. Pegar la dirección del contrato.
3. Para listar un NFT en venta: seleccionar el NFT → **Sell** → precio y duración.

### 2.4 Aprobar NFT para OpenSea (script)

**Script:** `backend/scripts/list_on_opensea.py`

Aprueba el proxy de OpenSea (Wyvern) para un tokenId. Después se puede listar manualmente en la web.

```bash
export POLYGON_RPC="https://polygon-rpc.com"
export DYNAMIC_NFT_ADDRESS="0x..."
export PRIVATE_KEY="..."
python3 scripts/list_on_opensea.py 1
# Listar en: https://opensea.io/assets/matic/<DYNAMIC_NFT_ADDRESS>/1
```

Variable opcional: `OPENSEA_PROXY` (por defecto Wyvern Ethereum).

---

## Paso 3: Cannabis medicinal y fresas

### 3.1 Contrato

El mismo **DynamicCropNFT.sol** incluye en el struct:

- **strain:** variedad (ej. "Amnesia Haze").
- **thcCbdRatio:** ej. 2000 = 20,00% THC (centésimas).
- **brixLevel:** nivel de azúcar para fresas (10-15 típico).

### 3.2 Mint cannabis

**Script:** `backend/scripts/mint_cannabis_nft.py`

```bash
python3 scripts/mint_cannabis_nft.py 0xAgricultor extremadura-farm-001 "Amnesia Haze" 2000 QmXoypiz...
# 2000 = 20.00% THC
```

### 3.3 Metadatos ejemplo cannabis

**Ubicación:** `metadata/cannabis_amnesia_haze.json`

Incluye name, description, image (IPFS), attributes (Crop Type, Strain, THC, CBD, CO₂ Saved, Farm ID, Growth Stage). Subir el JSON a IPFS y usar el hash en `mint_cannabis_nft.py`.

### 3.4 Mint fresas

**Script:** `backend/scripts/mint_strawberry_nft.py`

```bash
python3 scripts/mint_strawberry_nft.py 0xAgricultor extremadura-farm-001 12 QmXoypiz...
# 12 = nivel Brix (dulzor)
```

---

[CropNFT Marketplace](crop-nft-marketplace.md) · [Runbook](runbook-despliegue-global.md)
