# Chainlink (precio BioCoin) + Marketplace de carbono

Precio de BioCoin en tiempo real vía Chainlink y marketplace descentralizado para vender créditos de carbono en BioCoin.

---

## Paso 1: Chainlink para precio BioCoin/USD

**Objetivo:** Obtener el precio de BioCoin/USD en tiempo real con Chainlink Data Feeds.

### 1.1 Contrato BioCoinPriceConsumer.sol

Ubicación: `blockchain/contracts/BioCoinPriceConsumer.sol`

- **AggregatorV3Interface:** interfaz mínima para `latestRoundData()` (roundId, answer, startedAt, updatedAt, answeredInRound).
- **getLatestPrice():** actualiza `bioCoinPriceUSD` desde el feed y emite `PriceUpdated`.
- **getBioCoinPriceUSD():** devuelve el último precio en USD.

Si en GaiaChain no existe un feed Chainlink para BioCoin/USD, se puede usar un oracle local (Chainlink Node) o un feed de prueba (ej. ETH/USD) y ajustar decimales.

### 1.2 Desplegar

```bash
cd blockchain
npm install @chainlink/contracts   # Opcional: el contrato usa interfaz mínima local
export BIOCOIN_ADDRESS=0x...
export CHAINLINK_PRICE_FEED_ADDRESS=0x...   # Dirección del price feed en GaiaChain
npx hardhat compile
npx hardhat run scripts/deploy-biocoin-price-consumer.js --network gaiachain
```

### 1.3 Script para obtener el precio

```bash
export BIOCOIN_PRICE_CONSUMER_ADDRESS=0x...
python3 scripts/get_biocoin_price.py
```

Salida: `Precio actual de BioCoin: $X USD`.

### 1.4 Integración opcional con BioCoinCarbonMarket

Se puede extender `BioCoinCarbonMarket` para que use `BioCoinPriceConsumer.getBioCoinPriceUSD()` y calcule el total en BioCoin de forma dinámica (precio por kg CO₂ en USD → equivalente en BioCoin).

---

## Paso 2: Marketplace propio de créditos de carbono

**Objetivo:** Marketplace descentralizado donde los agricultores venden créditos en BioCoin (comisión de plataforma 5%).

### 2.1 Contrato CarbonMarketplace.sol

Ubicación: `blockchain/contracts/CarbonMarketplace.sol`

- **createListing(kgCO2, pricePerKgBioCoin):** el vendedor crea un listing.
- **buyListing(listingId):** el comprador paga en BioCoin al vendedor (total) y a la plataforma (fee 5%). Debe aprobar antes `total + fee`.
- **getListing(listingId):** devuelve seller, kgCO2, pricePerKgBioCoin, sold.

### 2.2 Desplegar

```bash
export BIOCOIN_ADDRESS=0x...
npx hardhat run scripts/deploy-carbon-marketplace.js --network gaiachain
```

### 2.3 Frontend (React + Web3)

Ubicación: `frontend/marketplace/`

- **src/App.js:** conexión MetaMask, lista de listings, crear listing y comprar.
- **CarbonMarketplaceABI.json:** ABI mínimo del contrato.
- Variable de entorno en build: `REACT_APP_MARKETPLACE_ADDRESS`.

Build y ejecución local:

```bash
cd frontend/marketplace
npm install
REACT_APP_MARKETPLACE_ADDRESS=0x... npm run build
```

### 2.4 Docker y Kubernetes

- **Dockerfile:** multi-stage (Node build → nginx serve).
- **kubernetes/marketplace/deployment.yaml:** Deployment (2 réplicas) y Service LoadBalancer para el frontend.

Para desplegar con ArgoCD: crear una aplicación que apunte al path `kubernetes/marketplace` y opcionalmente añadir en el workflow global:

```yaml
- name: Deploy Marketplace
  run: |
    argocd app sync carbon-marketplace
    argocd app wait --health carbon-marketplace
```

(Solo si la app `carbon-marketplace` está creada en ArgoCD.)

---

[BioCoin + AirCarbon](biocoin-aircarbon.md) · [Runbook](runbook-despliegue-global.md)
